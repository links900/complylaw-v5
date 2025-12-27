# checklists/signals.py
from django.db.models.signals import post_save, pre_save # <--- Add pre_save here
from django.dispatch import receiver
from .models import ChecklistSubmission, ChecklistResponse # <--- Add ChecklistResponse here
from users.models import FirmProfile

# Use the @ decorator syntax to ensure it registers correctly
@receiver(pre_save, sender=ChecklistResponse)
def log_audit_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_val = ChecklistResponse.objects.get(pk=instance.pk).status
            if old_val != instance.status:
                # Assuming submission has a field or property to get the user
                user = getattr(instance.submission, 'completed_by', 'System')
                print(f"AUDIT LOG: Control {instance.template.code} changed from {old_val} to {instance.status} by {user}")
        except ChecklistResponse.DoesNotExist:
            pass




@receiver(post_save, sender=FirmProfile)
def create_starter_audit(sender, instance, created, **kwargs):
    if created:
        # Use the specific standard selected in the wizard
        selected_std = instance.active_standard or "SOC2" # Fallback if empty
        
        ChecklistSubmission.objects.create(
            firm=instance,
            standard=selected_std,
            is_locked=False,
            # Ensure scan=None is allowed in your ChecklistSubmission model null=True
            scan=None 
        )