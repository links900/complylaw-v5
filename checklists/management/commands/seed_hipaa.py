# checklists/management/commands/seed_hipaa.py
from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds HIPAA Security & Privacy Rules'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "HIPAA",
                "code": "164.308(a)(1)",
                "reference_article": "Security Management Process",
                "title": "Risk Analysis",
                "description": "Conduct an accurate and thorough assessment of potential risks to the confidentiality, integrity, and availability of ePHI.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Request the most recent Enterprise Risk Assessment. Verify it specifically addresses ePHI storage and transmission points.",
                "recommendations": "Perform a HIPAA-specific risk assessment annually or whenever significant changes are made to the infrastructure."
            },
            {
                "standard": "HIPAA",
                "code": "164.312(a)(2)(iv)",
                "reference_article": "Technical Safeguards",
                "title": "Encryption and Decryption",
                "description": "Implement a mechanism to encrypt and decrypt electronic protected health information.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Inspect database configurations (AWS RDS, Azure SQL) and S3 buckets for 'Encryption at Rest'. Test TLS versions for data in transit.",
                "recommendations": "Enforce AES-256 encryption at rest and TLS 1.3 for all endpoints handling patient data."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="HIPAA", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('HIPAA seeded.'))