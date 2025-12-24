# billing/views.py
import stripe
import logging
import secrets
import string
from django.urls import reverse
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import transaction

from allauth.account.models import EmailAddress

# Setup
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)
User = get_user_model()

# ------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------
def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(chars) for _ in range(length))

def send_welcome_email(email, password):
    """SaaS Grade: Sends HTML credentials email."""
    subject = f"Welcome to {settings.SITE_NAME} - Account Ready"
    context = {
        'email': email,
        'password': password,
        'login_url': f"https://{settings.SITE_DOMAIN}/accounts/login/",
        'site_name': settings.SITE_NAME
    }
    
    html_content = render_to_string('emails/welcome.html', context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject, 
        text_content, 
        settings.DEFAULT_FROM_EMAIL, 
        [email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()

# ------------------------------------------------------------------
# Pages (Pricing & Success)
# ------------------------------------------------------------------
def pricing(request):
    return render(request, "billing/pricing.html")

def success(request):
    session_id = request.GET.get('session_id')
    customer_email = None
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            customer_email = session.customer_details.email
        except Exception as e:
            logger.error(f"Error retrieving session: {e}")
            
    return render(request, "billing/success.html", {"customer_email": customer_email})

# ------------------------------------------------------------------
# Billing Dashboard
# ------------------------------------------------------------------
@login_required
def billing_dashboard(request):
    user = request.user
    subscription_data = None
    
    if user.stripe_customer_id:
        try:
            customer = stripe.Customer.retrieve(
                user.stripe_customer_id, 
                expand=['subscriptions']
            )
            if customer.subscriptions.data:
                sub = customer.subscriptions.data[0]
                plan_name = "Professional" if sub.plan.id == settings.STRIPE_PRICE_PRO else "Basic"
                subscription_data = {
                    "status": sub.status,
                    "plan_name": plan_name,
                    "amount": f"${sub.plan.amount / 100:.2f}",
                    "current_period_end": sub.current_period_end * 1000,
                    "cancel_at_period_end": sub.cancel_at_period_end,
                }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Error: {e}")

    return render(request, "billing/dashboard.html", {"subscription": subscription_data})

# ------------------------------------------------------------------
# Stripe Actions
# ------------------------------------------------------------------
def create_checkout(request):
    if request.method != "POST":
        return redirect("billing:pricing")

    email = request.user.email if request.user.is_authenticated else request.POST.get("email")
    plan = request.POST.get("plan", "pro")

    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)

    price_id = settings.STRIPE_PRICE_PRO if plan == "pro" else settings.STRIPE_PRICE_BASIC
    DOMAIN = settings.SITE_DOMAIN
    # Logic to handle protocol based on your settings
    protocol = "https" if not ("localhost" in DOMAIN or "127.0.0.1" in DOMAIN) else "http"

    try:
        checkout_params = {
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": "subscription",
            "success_url": f"{protocol}://{DOMAIN}/billing/success/?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{protocol}://{DOMAIN}/billing/pricing/",
        }

        if request.user.is_authenticated and request.user.stripe_customer_id:
            checkout_params["customer"] = request.user.stripe_customer_id
        else:
            checkout_params["customer_email"] = email

        session = stripe.checkout.Session.create(**checkout_params)
        return redirect(session.url, code=303)
    except Exception as e:
        logger.exception("Checkout creation failed")
        return HttpResponse("Payment server error", status=500)

@login_required
def create_portal_session(request):
    if not request.user.stripe_customer_id:
        return redirect("billing:pricing")

    # Dynamically build the return URL based on your URL names
    # This will resolve to "/billing/" based on your current URLconf
    relative_return_url = reverse("billing:dashboard")
    
    DOMAIN = settings.SITE_DOMAIN
    protocol = "https" if not ("localhost" in DOMAIN or "127.0.0.1" in DOMAIN) else "http"
    
    # Construct the full absolute URL
    return_url = f"{protocol}://{DOMAIN}{relative_return_url}"
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=request.user.stripe_customer_id,
            return_url=return_url,
        )
        return redirect(session.url, code=303)
    except Exception as e:
        logger.error(f"Portal Error: {e}")
        # Using name-based redirect here too for safety
        return redirect("billing:dashboard")
# ------------------------------------------------------------------
# Webhooks
# ------------------------------------------------------------------
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        handle_checkout_success(event["data"]["object"])
    elif event["type"] in ["customer.subscription.deleted", "customer.subscription.updated"]:
        handle_subscription_change(event["data"]["object"])

    return HttpResponse(status=200)

def handle_checkout_success(session):
    email = session.get("customer_details", {}).get("email") or session.get("customer_email")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    user = User.objects.filter(email=email).first()

    if not user:
        with transaction.atomic():
            password = generate_random_password()
            user = User.objects.create_user(
                username=email.split("@")[0] + "_" + secrets.token_hex(3),
                email=email,
                password=password
            )
            user.stripe_customer_id = customer_id
            user.stripe_subscription_id = subscription_id
            user.save()
            
            EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
            transaction.on_commit(lambda: send_welcome_email(email, password))
    else:
        user.stripe_customer_id = customer_id
        user.stripe_subscription_id = subscription_id
        user.save()

def handle_subscription_change(subscription):
    user = User.objects.filter(stripe_customer_id=subscription.customer).first()
    if user:
        if subscription.status in ['canceled', 'unpaid']:
            user.stripe_subscription_id = None
        else:
            user.stripe_subscription_id = subscription.id
        user.save()
        
        
@login_required
def billing_dashboard(request):
    """SaaS Standard: Fetch live subscription status from Stripe."""
    user = request.user
    subscription_data = None
    
    if user.stripe_customer_id:
        try:
            # Expand subscriptions so we get the full object
            customer = stripe.Customer.retrieve(
                user.stripe_customer_id, 
                expand=['subscriptions']
            )
            
            if customer.subscriptions.data:
                # Get the first active subscription
                sub = customer.subscriptions.data[0]
                
                # Logic to determine plan name
                plan_id = getattr(sub.plan, 'id', None)
                plan_name = "Professional" if plan_id == settings.STRIPE_PRICE_PRO else "Basic"
                
                # SAFER ACCESS: Use getattr or .get() to avoid AttributeError
                # Stripe timestamps are in seconds, JS/Django templates often prefer milliseconds
                period_end = getattr(sub, 'current_period_end', None)
                cancel_at_end = getattr(sub, 'cancel_at_period_end', False)
                
                subscription_data = {
                    "status": sub.status,
                    "plan_name": plan_name,
                    "amount": f"${sub.plan.amount / 100:.2f}",
                    "current_period_end": period_end * 1000 if period_end else None,
                    "cancel_at_period_end": cancel_at_end,
                }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Error: {e}")
        except Exception as e:
            logger.error(f"General Billing Error: {e}")

    return render(request, "billing/dashboard.html", {"subscription": subscription_data})