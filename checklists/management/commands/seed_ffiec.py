# checklists/management/commands/seed_ffiec.py
from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds FFIEC Cybersecurity Assessment Tool (CAT)'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "FFIEC",
                "code": "D1.R1",
                "reference_article": "Domain 1: Cyber Risk Management",
                "title": "Board Oversight",
                "description": "The board of directors oversees the development and implementation of the cybersecurity program.",
                "risk_impact": "MEDIUM",
                "weight": 1.0,
                "requires_evidence": True,
                "how_to_check": "Review Board Meeting minutes from the last 4 quarters. Look for specific line items discussing cybersecurity metrics and risks.",
                "recommendations": "Establish a dedicated Board Risk Committee that receives monthly reports on the organization's cyber-risk posture."
            },
            {
                "standard": "FFIEC",
                "code": "D3.R10",
                "reference_article": "Domain 3: Cybersecurity Controls",
                "title": "Network Perimeter Defense",
                "description": "Firewalls and other perimeter defenses are configured to block unauthorized traffic.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Examine firewall rule sets. Look for 'Any-Any' rules or overly permissive configurations. Verify an annual firewall rule audit occurred.",
                "recommendations": "Implement a 'Deny by Default' rule at the perimeter and only allow specifically authorized protocols and IP addresses."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="FFIEC", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('FFIEC seeded.'))