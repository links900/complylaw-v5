from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds TPRM (Third-Party Risk Management) Framework'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "TPRM",
                "code": "TPRM-01",
                "reference_article": "Vendor Onboarding",
                "title": "Vendor Security Assessment",
                "description": "All vendors must undergo a security assessment prior to contract signing.",
                "risk_impact": "MEDIUM",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Review the files for the 3 most recently onboarded vendors. Ensure a completed SIG (Standardized Information Gathering) questionnaire or SOC 2 report is on file.",
                "recommendations": "Automate the assessment process using a vendor risk platform like Whistic or OneTrust."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="TPRM", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('TPRM seeded.'))