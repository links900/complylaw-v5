from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Main Pricing Page
    path('pricing/', views.pricing, name='pricing'),
    
    # Stripe Checkout Redirect
    path('create-checkout/', views.create_checkout, name='create_checkout'),
    
    # Success Page (Redirected from Stripe)
    path('success/', views.success, name='success'),
    
    # Logged-in Billing Dashboard
    path('', views.billing_dashboard, name='dashboard'),
    
    # Stripe Customer Portal (Self-Service)
    path('create-portal/', views.create_portal_session, name='create_portal'),
    
    # Webhook Endpoint (Must be excluded from CSRF in views)
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]