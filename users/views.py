# users/views.py
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
from django.db import transaction

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
        firm = self.get_object() 
        context['firm'] = firm
        
        '''
        # Logic to find available seed commands for standards
        commands_path = os.path.join(settings.BASE_DIR, 'checklists', 'management', 'commands')
        standards = []
        if os.path.exists(commands_path):
            for filename in os.listdir(commands_path):
                if filename.startswith("seed_") and filename.endswith(".py"):
                    standards.append(filename.replace("seed_", "").replace(".py", "").upper())
        
        context['available_standards'] = sorted(list(set(standards))) if standards else ['GDPR']
        '''
              
        
        # 1. Get the QuerySet from the model method
        # This calls the method we added to FirmProfile that checks Tiers + Manual Additions
        available_db_standards = firm.get_available_standards()
        
        
        # 2. Convert to a list of UPPERCASE strings
        # We use .name because available_db_standards is a list of RegulatoryStandard objects
        standards_list = [s.name.upper() for s in available_db_standards]
        
        # 3. Sort and pass to context
        context['available_standards'] = sorted(list(set(standards_list)))
        
       
        
        # 3. Sort and pass to context
        final_standards = sorted(list(set(standards_list)))
        
        # DEBUG: Uncomment the line below to see if data is hitting the view
        # print(f"DEBUG: Standards for {firm.firm_name} (Tier: {firm.subscription_tier}): {final_standards}")
        #if not context['available_standards']:
        #    context['available_standards'] = [] # Default is null as requested

        context['available_standards'] = final_standards
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
        try:
            with transaction.atomic():
                # 1. Fetch the existing instance FIRST
                firm, created = FirmProfile.objects.get_or_create(user=self.request.user)
                
                # 2. Re-initialize the form with the instance so Django knows it's an UPDATE
                # and preserves fields like 'created_at'
                form.instance = firm 
                
                # 3. Now save the form to the existing instance
                updated_firm = form.save(commit=False)
                updated_firm.user = self.request.user
                
                # 4. Set your defaults
                updated_firm.scan_mode = 'simple'
                updated_firm.is_active = True
                updated_firm.subscription_tier = getattr(self.request.user, 'subscription_tier', 'trial')
                
                # Ensure we don't accidentally nullify the created_at if it's already there
                if not updated_firm.created_at and not created:
                    # Optional: refresh from db if you want to be extra safe
                    firm.refresh_from_db()
                    updated_firm.created_at = firm.created_at

                # 5. Handle Framework Logic
                updated_firm.active_standard = form.cleaned_data.get('active_standard')
                
                # 6. Final Save
                updated_firm.save()
                
                # 7. Link User
                if self.request.user.firm != updated_firm:
                    self.request.user.firm = updated_firm
                    self.request.user.save()
                
                if hasattr(updated_firm, 'sync_compliance_checklist'):
                    updated_firm.sync_compliance_checklist()
                    
                messages.success(self.request, f"Welcome to {updated_firm.firm_name}!")
                return HttpResponseRedirect(self.get_success_url())

        except Exception as e:
            form.add_error(None, f"Database Error: {str(e)}")
            return self.form_invalid(form)    
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import TierStandard, RegulatoryStandard
        
        # 1. Get tier from User (default to 'trial' if not set)
        # Note: Ensure your UserAccount model has a subscription_tier field
        user_tier = getattr(self.request.user, 'subscription_tier', 'trial')
        
        # 2. Get Standards mapped to this Tier
        tier_defaults = TierStandard.objects.filter(tier=user_tier).first()
        
        # 3. Get the queryset (Tier Defaults + any global ones if needed)
        if tier_defaults:
            standards = tier_defaults.standards.all()
        else:
            standards = RegulatoryStandard.objects.all()

        context['available_standards'] = standards
        context['user_tier'] = user_tier
        context['is_wizard'] = True
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