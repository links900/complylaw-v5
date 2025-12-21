# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField
from django.core.serializers.json import DjangoJSONEncoder
import json
from auditlog.registry import auditlog
from django.conf import settings
from django.core.validators import RegexValidator

class FirmProfile(models.Model):
    SUBSCRIPTION_CHOICES = [
        ('trial', 'Trial'),
        ('basic', 'Basic'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    firm_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    domain = models.CharField(max_length=255, unique=True)
    phone = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        validators=[RegexValidator(r'^\+?\d{7,15}$', 'Enter a valid phone number.')],
        help_text="e.g +18881234567"
    )
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    address = EncryptedTextField(blank=True)
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='firmprofile'
    )
    
    SCAN_MODE_CHOICES = [
        ('simple', 'Simple'),
        ('detailed', 'Detailed'),
    ]
    scan_mode = models.CharField(
        max_length=10, 
        choices=SCAN_MODE_CHOICES, 
        default='simple'
    )
    active_standard = models.CharField(
        max_length=100, 
        default='GDPR'  # Default as requested
    )
    
    # New Localization & Status
    timezone = models.CharField(max_length=100, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    date_format = models.CharField(max_length=20, default='%d/%m/%Y')
    is_active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    _preferences = EncryptedTextField(blank=True, default='{}')
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, default='trial')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Stores selected frameworks like ['iso27001', 'gdpr']
    selected_frameworks = models.JSONField(default=list, blank=True) # Stores ['iso27001', 'gdpr']
    audit_rigor = models.CharField(
        max_length=20, 
        choices=[('simple', 'Simple'), ('detailed', 'Detailed')],
        default='simple'
    )
    
    retention_days = models.IntegerField(default=365, help_text="Number of days to keep audit logs")
    data_region = models.CharField(max_length=10, default='us')
    
   
    def __str__(self):
        return self.firm_name

    def get_preferences(self):
        return json.loads(self._preferences) if self._preferences else {}
    def set_preferences(self, value):
        self._preferences = json.dumps(value, cls=DjangoJSONEncoder)
    preferences = property(get_preferences, set_preferences)
    
    def sync_compliance_checklist(self):
        """
        Dynamically calls the seed command based on the active_standard.
        e.g., if active_standard is 'GDPR', it calls 'seed_gdpr'
        """
        command_name = f"seed_{self.active_standard.lower()}"
        try:
            # We pass the firm ID so the seed script knows which firm to populate
            call_command(command_name, firm_id=self.id)
            return True
        except Exception as e:
            print(f"Error seeding {command_name}: {e}")
            return False

class UserAccount(AbstractUser):
    ROLE_CHOICES = [('owner', 'Owner'), ('viewer', 'Viewer')]
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    firm = models.ForeignKey(FirmProfile, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='viewer')
    mfa_secret = EncryptedCharField(max_length=255, null=True, blank=True)
    last_scan_at = models.DateTimeField(null=True, blank=True)

auditlog.register(FirmProfile)
auditlog.register(UserAccount)

