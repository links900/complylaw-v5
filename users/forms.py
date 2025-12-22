import re
import pytz
import os
import logging
from django import forms
from django.conf import settings
from .models import FirmProfile

logger = logging.getLogger(__name__)

class BaseFirmForm(forms.ModelForm):
    """ The Core logic shared by both Wizard and Settings """
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
            'address', 'logo', 'subscription_tier','retention_days'
        ]
        
        widgets = {
            'retention_days': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        standard_css = "w-full bg-slate-50 border border-slate-300 rounded-xl py-3 px-4 text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium shadow-sm"
        file_css = "block w-full text-sm text-slate-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': file_css if name == 'logo' else standard_css})
            if name == 'subscription_tier':
                field.disabled = True

        # If this is a POST/submitting data, make missing fields optional
        if self.data:
            for name, field in self.fields.items():
                if name not in self.data and name not in self.files:
                    field.required = False

    def clean_domain(self):
        domain = self.cleaned_data.get('domain')
        if 'domain' not in self.data:
            return self.instance.domain
        domain = domain.strip().lower()
        domain = re.sub(r'^https?://', '', domain.rstrip('/')).replace('www.', '')
        if FirmProfile.objects.filter(domain=domain).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Domain already registered.")
        return domain

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if 'email' not in self.data:
            return self.instance.email
        if FirmProfile.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email already in use.")
        return email

    def save(self, commit=True):
        """ CRITICAL: Only update fields that were actually submitted in the POST request """
        instance = super().save(commit=False)
        if self.data:
            # Get the list of fields actually sent in the request
            submitted_fields = [f for f in self.fields if f in self.data or f in self.files]
            # Only update those specific fields on the instance
            for field in submitted_fields:
                if hasattr(instance, field):
                    setattr(instance, field, self.cleaned_data.get(field))
        
        if commit:
            instance.save()
        return instance

class FirmProfileForm(BaseFirmForm):
    class Meta(BaseFirmForm.Meta):
        fields = [f for f in BaseFirmForm.Meta.fields if f != 'subscription_tier']

class FirmSettingsForm(BaseFirmForm):
    class Meta(BaseFirmForm.Meta):
        fields = BaseFirmForm.Meta.fields + ['scan_mode', 'active_standard', 'audit_rigor']