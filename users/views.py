# users/views.py — SAFE & FINAL

from django.views.generic import TemplateView, UpdateView, CreateView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from allauth.account.views import SignupView
from .models import FirmProfile, UserAccount
from .forms import FirmSettingsForm, FirmProfileForm # <--- Updated Imports
import json
import os
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone as django_timezone

import secrets
import string
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# -----------------------------
# PROFILE VIEWS
# -----------------------------
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firm'] = getattr(self.request.user, 'firm', None)
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserAccount
    fields = ['first_name', 'last_name']
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        return self.request.user
        
    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)


# -----------------------------
# FIRM VIEWS
# -----------------------------
class FirmSettingsView(LoginRequiredMixin, UpdateView):
    model = FirmProfile
    form_class = FirmSettingsForm
    template_name = 'users/firm_settings.html'
    success_url = reverse_lazy('users:firm_settings')
    
    
    def get_object(self):
        # Access the profile linked to the user
        try:
            return self.request.user.firmprofile
        except (UserAccount.firmprofile.RelatedObjectDoesNotExist, AttributeError):
            return None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if not hasattr(request.user, 'firmprofile'):
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Get base context (this includes the 'form' and 'object')
        context = super().get_context_data(**kwargs)
        
        # Explicitly set 'firm' for the template
        context['firm'] = self.get_object() 

        # --- DYNAMIC FILE PARSING ---
        # Path: project_root/checklists/management/commands/
        commands_path = os.path.join(settings.BASE_DIR, 'checklists', 'management', 'commands')
        
        standards = []
        if os.path.exists(commands_path):
            for filename in os.listdir(commands_path):
                # Filter for your seed files
                if filename.startswith("seed_") and filename.endswith(".py"):
                    # Transform 'seed_gdpr.py' -> 'GDPR'
                    display_name = filename.replace("seed_", "").replace(".py", "").upper()
                    standards.append(display_name)
        
        # Fallback to GDPR if no files are found
        if not standards:
            standards = ['GDPR']
            
        context['available_standards'] = sorted(list(set(standards)))
        return context

    def form_valid(self, form):
        messages.success(self.request, "Settings updated successfully.")
        response = super().form_valid(form)
        
        # Trigger the checklist sync for the new active standard
        self.object.sync_compliance_checklist()
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

class ArchiveFirmView(LoginRequiredMixin, View):
    def post(self, request):
        profile = getattr(request.user, 'firmprofile', None)
        if profile:
            profile.is_active = False
            profile.archived_at = django_timezone.now()
            profile.save()
            messages.error(request, "Organization has been archived.")
        return redirect('users:profile')
        
        
class FirmSetupWizardView(LoginRequiredMixin, CreateView):
    model = FirmProfile
    form_class = FirmProfileForm # Uses the alias from forms.py
    template_name = 'users/firm_wizard.html'
    success_url = reverse_lazy('dashboard:home')

    def form_valid(self, form):
        firm = form.save(commit=False)
        firm.user = self.request.user
        
        # Inject defaults for the required fields that aren't in the wizard UI
        firm.scan_mode = 'simple'
        firm.active_standard = 'GDPR'
        firm.is_active = True
        
        firm.save()
        
        # Link the user to the firm correctly
        self.request.user.firm_id = firm.id
        self.request.user.save()

        messages.success(self.request, f"Welcome to {firm.firm_name}!")
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        # Prevent users who already have a firm from re-running the wizard
        if hasattr(request.user, 'firmprofile') and request.user.firmprofile:
            return redirect('dashboard:home')
        messages.get_messages(request).used = True  
        return super().get(request, *args, **kwargs)

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_wizard'] = True
        # This is the "Magic Line": It tells the template 'firm' is None
        # so it stops trying to look for user.firmprofile
        context['firm'] = None 
        return context


# -----------------------------
# DASHBOARD REDIRECT
# -----------------------------
class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, 'firmprofile') or request.user.firmprofile is None:
            return redirect('users:firm_wizard')
        return redirect('dashboard:home')


# -----------------------------
# SIGNUP VIEWS
# -----------------------------
class SignupWizardView(FormView):
    template_name = 'users/signup.html'
    success_url = reverse_lazy('dashboard:home')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return redirect('account_signup')


class CustomSignupView(SignupView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Check your inbox! We sent a confirmation link to your email. Click it to activate your account."
        )
        return render(self.request, "account/signup.html", self.get_context_data(form=form))


class EmailConfirmationSentView(TemplateView):
    template_name = "account/email_confirmation_sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.session.get("account_verified_email", "your inbox")
        return context


# -----------------------------
# ADMIN HELPER (DEBUG ONLY)
# -----------------------------
def create_admin_user(request):
    if not settings.DEBUG:
        return HttpResponse("Not allowed.", status=403)

    User = get_user_model()
    username = "admin"
    email = "complylaw@alhambra-solutions.com"
    password = "1234abcd@dmin"

    if User.objects.filter(username=username).exists():
        return HttpResponse("Admin user already exists.")

    User.objects.create_superuser(username=username, email=email, password=password)
    return HttpResponse(f"Superuser '{username}' created successfully!")


# -----------------------------
# FIRM LOGO CLEAR
# -----------------------------
class ClearFirmLogoView(LoginRequiredMixin, View):
    def post(self, request):
        profile = getattr(request.user, 'firmprofile', None)
        if profile and profile.logo:
            profile.logo.delete(save=False)
            profile.logo = None
            profile.save()
            messages.success(request, "Firm logo removed successfully.")
        return HttpResponse("""
            <div class="p-5 bg-gray-50 rounded-xl border border-gray-200 text-center text-gray-500 text-sm">
                No logo uploaded
            </div>
        """)
