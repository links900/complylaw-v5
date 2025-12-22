# checklists/management/commands/seed_pci_dss.py
from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds PCI DSS Core Controls'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "PCI-DSS",
                "code": "REQ-3",
                "reference_article": "Requirement 3",
                "title": "Protect Stored Account Data",
                "description": "Protect stored account data with effective encryption and hashing.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Search databases for unmasked Primary Account Numbers (PAN). Verify that the first 6 and last 4 digits only are visible.",
                "recommendations": "Implement tokenization so that raw credit card numbers are never stored in your local environment."
            },
            {
                "standard": "PCI-DSS",
                "code": "REQ-11",
                "reference_article": "Requirement 11",
                "title": "Regular Security Testing",
                "description": "Test security of systems and networks regularly (ASV Scans).",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Verify Quarterly ASV (Approved Scanning Vendor) reports. Ensure no 'High' vulnerabilities remain unaddressed.",
                "recommendations": "Automate internal scans weekly and ensure the official ASV scan is scheduled at least 30 days before the quarterly deadline."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="PCI-DSS", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('PCI DSS seeded.'))