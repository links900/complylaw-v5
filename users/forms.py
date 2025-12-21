# users/forms.py
import re
import pytz
from django import forms
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
            'firm_name', 'email', 'domain', 'phone', 'address', 
            'logo', 'subscription_tier', 'timezone', 'currency', 'date_format'
        ]

    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            # High-contrast international grade styling
            # Border is slate-300 (visible), background is slate-50 (subtle grey)
            standard_css = (
                "w-full rounded-lg border-slate-300 bg-slate-50/50 text-slate-900 text-sm py-2.5 "
                "placeholder:text-slate-400 "
                "focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 focus:bg-white "
                "transition-all duration-200 shadow-sm"
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
                
                # Special handling for disabled fields (like subscription)
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