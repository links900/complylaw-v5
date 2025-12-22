# checklists/management/commands/seed_nist_csf.py
from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds NIST Cybersecurity Framework (CSF)'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "NIST-CSF",
                "code": "ID.AM-1",
                "reference_article": "Identify: Asset Management",
                "title": "Physical Devices Inventory",
                "description": "Physical devices and systems within the organization are inventoried.",
                "risk_impact": "MEDIUM",
                "weight": 1.2,
                "requires_evidence": True,
                "how_to_check": "Review the hardware asset list. Check if it includes serial numbers, owners, and locations.",
                "recommendations": "Use an MDM (Mobile Device Management) solution like Jamf or Intune to maintain an automated, real-time inventory."
            },
            {
                "standard": "NIST-CSF",
                "code": "PR.AT-1",
                "reference_article": "Protect: Awareness & Training",
                "title": "Security Awareness Training",
                "description": "All users are informed and trained on information security risks.",
                "risk_impact": "LOW",
                "weight": 0.8,
                "requires_evidence": True,
                "how_to_check": "Check completion records for security awareness training. Verify that 100% of active employees completed it in the last year.",
                "recommendations": "Use a platform like KnowBe4 to automate training and run monthly simulated phishing campaigns."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="NIST-CSF", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('NIST CSF seeded.'))