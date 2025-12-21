from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds NIST 800-53 Rev 5 Core Controls'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "NIST800-53",
                "code": "AU-2",
                "reference_article": "Audit and Accountability",
                "title": "Event Logging",
                "description": "The organization determines that the information system is capable of logging specific security events.",
                "risk_impact": "MEDIUM",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Examine system logs to ensure they capture: User ID, Type of event, Date/Time, Success/Failure, and Identity of affected data.",
                "recommendations": "Configure a centralized logging server (SIEM) with alerts for unauthorized configuration changes."
            },
            {
                "standard": "NIST800-53",
                "code": "IA-2",
                "reference_article": "Identification and Authentication",
                "title": "Multi-Factor Authentication",
                "description": "The information system implements multi-factor authentication for network access to privileged accounts.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Attempt to log into a management console (AWS, Azure, etc.) without an MFA token. Verify that access is denied.",
                "recommendations": "Standardize on FIDO2 or hardware-based MFA (like YubiKeys) for all administrative personnel."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="NIST800-53", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('NIST 800-53 seeded.'))