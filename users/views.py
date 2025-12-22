import json
import os
import logging
import secrets
import string
from django.views.generic import TemplateView, UpdateView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from allauth.account.views import SignupView
from .models import FirmProfile, UserAccount
from .forms import FirmSettingsForm, FirmProfileForm
from django.utils import timezone as django_timezone

# Set up logger
logger = logging.getLogger(__name__)
User = get_user_model()


# -----------------------------
# PROFILE VIEWS
# -----------------------------
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firm'] = getattr(self.request.user, 'firmprofile', None)
        return context

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserAccount
    fields = ['first_name', 'last_name']
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')
    def get_object(self): return self.request.user
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
        return getattr(self.request.user, 'firmprofile', None)

    def form_valid(self, form):
        # Identify which button was clicked via section_name
        section = self.request.POST.get('section_name', 'Settings')
        
        # Save the instance (UpdateView logic)
        self.object = form.save()
        
        # Specific logic for Compliance section
        if section == "Compliance Settings" and hasattr(self.object, 'sync_compliance_checklist'):
            self.object.sync_compliance_checklist()
            
        messages.success(self.request, f"Success: {section} has been updated.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        section = self.request.POST.get('section_name', 'Section')
        logger.error(f"Form Invalid for {section}: {form.errors}")
        messages.error(self.request, f"Error: Could not save {section}. Please check the fields.")
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if not hasattr(request.user, 'firmprofile'):
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firm'] = self.get_object() 
        
        # Logic to find available seed commands for standards
        commands_path = os.path.join(settings.BASE_DIR, 'checklists', 'management', 'commands')
        standards = []
        if os.path.exists(commands_path):
            for filename in os.listdir(commands_path):
                if filename.startswith("seed_") and filename.endswith(".py"):
                    standards.append(filename.replace("seed_", "").replace(".py", "").upper())
        
        context['available_standards'] = sorted(list(set(standards))) if standards else ['GDPR']
        return context


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
    form_class = FirmProfileForm
    template_name = 'users/firm_wizard.html'
    success_url = reverse_lazy('dashboard:home')
    
    def form_valid(self, form):
        firm = form.save(commit=False)
        firm.user = self.request.user
        firm.scan_mode = 'simple'
        firm.active_standard = 'GDPR'
        firm.is_active = True
        firm.save()
        
        # Link the user to the new firm
        self.request.user.firm_id = firm.id
        self.request.user.save()
        
        messages.success(self.request, f"Welcome to {firm.firm_name}!")
        return super().form_valid(form)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_wizard'], context['firm'] = True, None
        return context

    def get(self, request, *args, **kwargs):
        if hasattr(request.user, 'firmprofile') and request.user.firmprofile:
            return redirect('dashboard:home')
        return super().get(request, *args, **kwargs)


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, 'firmprofile') or request.user.firmprofile is None:
            return redirect('users:firm_wizard')
        return redirect('dashboard:home')


class ClearFirmLogoView(LoginRequiredMixin, View):
    def post(self, request):
        profile = getattr(request.user, 'firmprofile', None)
        if profile and profile.logo:
            profile.logo.delete(save=False)
            profile.logo = None
            profile.save()
        
        # Returns HTMX snippet to update the preview area
        return HttpResponse('''
            <div id="empty-preview" class="w-full h-48 bg-slate-50 rounded-xl border-2 border-dashed border-slate-300 flex flex-col items-center justify-center text-slate-400">
                <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                <span class="text-xs font-bold uppercase tracking-widest">No Logo</span>
            </div>
        ''')


class CustomSignupView(SignupView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Check your email for an activation link.")
        return response


class EmailConfirmationSentView(TemplateView):
    template_name = "account/email_confirmation_sent.html"


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