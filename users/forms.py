# users/forms.py
import re
import pytz
import os
from django import forms
from django.conf import settings
from .models import FirmProfile

class FirmSettingsForm(forms.ModelForm):
    # Standard International Choices
    CURRENCY_CHOICES = [('USD', 'USD ($)'), ('EUR', 'EUR (€)'), ('GBP', 'GBP (£)'), ('INR', 'INR (₹)')]
    DATE_FORMAT_CHOICES = [('%m/%d/%Y', 'MM/DD/YYYY'), ('%d/%m/%Y', 'DD/MM/YYYY'), ('%Y-%m-%d', 'YYYY-MM-DD')]
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]

    timezone = forms.ChoiceField(choices=TIMEZONE_CHOICES, initial='UTC')
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, initial='USD')
    date_format = forms.ChoiceField(choices=DATE_FORMAT_CHOICES, initial='%d/%m/%Y')

    class Meta:
        model = FirmProfile
        fields = [
            'firm_name', 'email', 'phone', 'domain', 
            'timezone', 'currency', 'date_format', 
            'address', 'logo', 'subscription_tier'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. DYNAMICALLY LOAD STANDARDS FROM FILESYSTEM
        commands_path = os.path.join(settings.BASE_DIR, 'checklists', 'management', 'commands')
        dynamic_choices = []
        
        if os.path.exists(commands_path):
            for filename in os.listdir(commands_path):
                if filename.startswith("seed_") and filename.endswith(".py"):
                    # Transform 'seed_gdpr.py' -> 'GDPR'
                    val = filename.replace("seed_", "").replace(".py", "").upper()
                    dynamic_choices.append((val, val))
        
        # Fallback to GDPR if no files found
        if not dynamic_choices:
            dynamic_choices = [('GDPR', 'GDPR')]
            
        # Update the choices for the active_standard field to allow validation
        if 'active_standard' in self.fields:
            self.fields['active_standard'].choices = sorted(dynamic_choices)

        # 2. APPLY STYLING
        # High-contrast international grade styling
        standard_css = (
            "w-full bg-slate-50 border border-slate-300 rounded-xl py-3 px-4 "
            "text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 "
            "transition-all placeholder:text-slate-400 font-medium shadow-sm"
        )
                    
        file_css = (
            "block w-full text-sm text-slate-500 "
            "file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 "
            "file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 "
            "hover:file:bg-indigo-100 transition-all"
        )

        for name, field in self.fields.items():
            # Apply the appropriate CSS based on field type
            if name == 'logo':
                field.widget.attrs.update({'class': file_css})
            else:
                field.widget.attrs.update({'class': standard_css})
            
            # Special handling for disabled fields
            if name == 'subscription_tier':
                field.disabled = True
                field.widget.attrs.update({
                    'class': standard_css + " bg-slate-100 cursor-not-allowed border-slate-200 text-slate-500"
                })
                    
    def clean_domain(self):
        domain = self.cleaned_data.get('domain', '').strip().lower()
        domain = re.sub(r'^https?://', '', domain.rstrip('/')).replace('www.', '')
        if FirmProfile.objects.filter(domain=domain).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Domain already registered.")
        return domain

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if FirmProfile.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email already in use.")
        return email

# Set the alias so the Wizard view doesn't break
FirmProfileForm = FirmSettingsForm