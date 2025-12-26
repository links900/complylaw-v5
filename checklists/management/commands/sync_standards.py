# checklists/management/commands/sync_standards.py
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import RegulatoryStandard

class Command(BaseCommand):
    help = "Syncs RegulatoryStandard database table with seed_*.py files"

    def handle(self, *args, **options):
        commands_path = os.path.join(settings.BASE_DIR, 'checklists', 'management', 'commands')
        
        if not os.path.exists(commands_path):
            self.stdout.write(self.style.ERROR("Commands path not found."))
            return

        found_standards = []
        for filename in os.listdir(commands_path):
            if filename.startswith("seed_") and filename.endswith(".py"):
                standard_name = filename.replace("seed_", "").replace(".py", "").upper()
                found_standards.append(standard_name)

        for name in found_standards:
            obj, created = RegulatoryStandard.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added new standard: {name}"))

        # Optional: Remove standards from DB that no longer have a seed file
        RegulatoryStandard.objects.exclude(name__in=found_standards).delete()