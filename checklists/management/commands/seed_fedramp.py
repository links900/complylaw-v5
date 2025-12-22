# checklists/management/commands/seed_fedramp.py
from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds FedRAMP (Moderate Impact) Controls'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "FedRAMP",
                "code": "AC-2(1)",
                "reference_article": "Account Management",
                "title": "Automated System Account Management",
                "description": "The organization employs automated mechanisms to support the management of information system accounts.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Verify that account creation, modification, and disabling are handled via an automated system (e.g., Active Directory, Okta) rather than manual requests.",
                "recommendations": "Integrate your HR system (e.g., Workday) with your Identity Provider to trigger automated provisioning/deprovisioning flows."
            },
            {
                "standard": "FedRAMP",
                "code": "CP-9",
                "reference_article": "Contingency Planning",
                "title": "Information System Backup",
                "description": "Conduct incremental and full backups of user-level and system-level information.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Inspect backup logs for the last 30 days. Verify that backups are stored in a geographically separate location (different cloud region).",
                "recommendations": "Implement 'Immutable Backups' to prevent ransomware from encrypting your recovery data."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="FedRAMP", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('FedRAMP seeded.'))