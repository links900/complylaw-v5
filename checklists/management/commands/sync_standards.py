import os
from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import RegulatoryStandard

class Command(BaseCommand):
    help = "Syncs RegulatoryStandard database table with seed_*.py files and adds metadata"

    def handle(self, *args, **options):
        # Professional SaaS Metadata for the standards
        metadata = {
            "SOC2": {"tag": "Trust", "desc": "Security, availability, and processing integrity of cloud data."},
            "HIPAA": {"tag": "Health", "desc": "Protection of sensitive patient health information (PHI)."},
            "TPRM": {"tag": "Vendor", "desc": "Third-Party Risk Management and supply chain security."},
            "CMMC": {"tag": "Defense", "desc": "Cybersecurity standards for the defense industrial base."},
            "GRC": {"tag": "Governance", "desc": "Integrated strategy for governance, risk, and compliance."},
            "ISO27001": {"tag": "Global", "desc": "International standard for Information Security Management Systems."},
            "PCIDSS": {"tag": "Finance", "desc": "Security standards for handling major credit card data."},
            "GDPR": {"tag": "Privacy", "desc": "EU data protection and privacy requirements for citizens."},
            "CCPA": {"tag": "Privacy", "desc": "California Consumer Privacy Act compliance requirements."},
            "ISO27701": {"tag": "Privacy", "desc": "Privacy information management extension to ISO 27001."},
            "MICROSOFT SSPA": {"tag": "Vendor", "desc": "Microsoft Supplier Security and Privacy Assurance."},
            "NISTCSF": {"tag": "Federal", "desc": "Voluntary framework to manage and reduce cybersecurity risk."},
            "NIST800171": {"tag": "Defense", "desc": "Protecting Controlled Unclassified Information in non-federal systems."},
            "NIST80053": {"tag": "Federal", "desc": "Security and privacy controls for federal information systems."},
            "FFIEC": {"tag": "Finance", "desc": "Cybersecurity standards for financial institutions and banks."},
            "FEDRAMP": {"tag": "Federal", "desc": "Security assessment and authorization for cloud services."},
        }

        commands_path = os.path.join(settings.BASE_DIR, 'checklists', 'management', 'commands')
        
        if not os.path.exists(commands_path):
            self.stdout.write(self.style.ERROR(f"Commands path not found at: {commands_path}"))
            return

        found_standards = []
        for filename in os.listdir(commands_path):
            if filename.startswith("seed_") and filename.endswith(".py"):
                # Normalize name to match dictionary keys (e.g., seed_iso27001.py -> ISO27001)
                raw_name = filename.replace("seed_", "").replace(".py", "").upper().replace("_", "").replace("-", "")
                found_standards.append(raw_name)

                # Get metadata or use defaults
                data = metadata.get(raw_name, {"tag": "Compliance", "desc": "Standard regulatory compliance framework."})

                obj, created = RegulatoryStandard.objects.update_or_create(
                    name=raw_name,
                    defaults={
                        'one_liner': data['desc'],
                        'scope_tag': data['tag']
                    }
                )

                status = "Added" if created else "Updated"
                self.stdout.write(self.style.SUCCESS(f"{status} standard: {raw_name}"))

        # Optional: Remove standards from DB that no longer have a seed file
        # Standard names in DB are upper case without symbols based on logic above
        RegulatoryStandard.objects.exclude(name__in=found_standards).delete()
        self.stdout.write(self.style.SUCCESS("Sync complete."))