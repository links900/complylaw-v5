# checklists/management/commands/seed_ccpa.py
from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds CCPA/CPRA Compliance'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "CCPA",
                "code": "CCPA-01",
                "reference_article": "1798.120",
                "title": "Right to Opt-Out of Sale/Sharing",
                "description": "Consumers must have the right to opt-out of the sale or sharing of their personal information.",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Check the website footer for a 'Do Not Sell or Share My Personal Information' link. Test the link to ensure it functions.",
                "recommendations": "Use a Consent Management Platform (CMP) that automatically broadcasts the GPC (Global Privacy Control) signal to third-party trackers."
            },
            {
                "standard": "CCPA",
                "code": "CCPA-02",
                "reference_article": "1798.130",
                "title": "Notice at Collection",
                "description": "Inform consumers at or before the point of collection about the categories of personal information to be collected.",
                "risk_impact": "MEDIUM",
                "weight": 1.0,
                "requires_evidence": False,
                "how_to_check": "Review all web forms. Ensure a link to the privacy policy or a specific 'Notice at Collection' is visible before the user submits data.",
                "recommendations": "Update web form templates to include a checkbox or text block disclosing data usage categories."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="CCPA", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('CCPA seeded.'))