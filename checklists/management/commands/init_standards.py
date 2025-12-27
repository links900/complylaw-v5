# checklists/management/commands/init_standards.py
from django.core.management.base import BaseCommand
from users.models import RegulatoryStandard, TierStandard, SUBSCRIPTION_CHOICES

class Command(BaseCommand):
    help = 'Seeds all subscription tiers with default regulatory standards'

    def handle(self, *args, **options):
        # 1. Define the list of global standards
        names = [
            'GDPR', 'HIPAA', 'SOC2', 'PCI_DSS', 'ISO27001', 
            'CCPA', 'NIST_CSF', 'CMMC', 'FEDRAMP'
        ]
        
        # 2. Bulk create standards (objects)
        standard_objs = []
        for name in names:
            standard, created = RegulatoryStandard.objects.get_or_create(name=name)
            standard_objs.append(standard)
            if created:
                self.stdout.write(f"Created standard: {name}")

        # 3. Assign standards to ALL tiers defined in SUBSCRIPTION_CHOICES
        # This covers ('trial', 'basic', 'pro', 'enterprise')
        for tier_slug, tier_name in SUBSCRIPTION_CHOICES:
            tier_obj, created = TierStandard.objects.get_or_create(tier=tier_slug)
            
            # Use .set() to sync the many-to-many relationship
            tier_obj.standards.set(standard_objs)
            
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status} Tier: {tier_name} ({tier_slug})"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded all tiers with standards!'))