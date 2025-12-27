# users/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from django.contrib.sites.models import Site

@receiver(post_migrate)
def update_site(sender, **kwargs):
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={
            "domain": settings.SITE_DOMAIN,
            "name": settings.SITE_NAME,
        },
    )


@receiver(post_save, sender=UserAccount)
def create_user_firm_profile(sender, instance, created, **kwargs):
    if created:
        # Create a blank profile for the new user
        FirmProfile.objects.create(
            user=instance, 
            firm_name=f"{instance.username}'s Firm", # Default name
            email=instance.email
        )