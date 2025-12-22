# checklists/management/commands/seed_cmmc.py
from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds CMMC Level 2 Practices'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "CMMC",
                "code": "AC.L2-3.1.1",
                "reference_article": "Access Control",
                "title": "Limit Authorized User Access",
                "description": "Limit information system access to authorized users, processes acting on behalf of authorized users, or devices.",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Review the Access Control List (ACL). Verify that CUI (Controlled Unclassified Information) is stored in a segregated environment.",
                "recommendations": "Implement a 'Zero Trust' architecture and use security groups to restrict access to CUI based strictly on job role."
            },
            {
                "standard": "CMMC",
                "code": "SC.L2-3.13.11",
                "reference_article": "System & Comm Protection",
                "title": "FIPS-Validated Cryptography",
                "description": "Use FIPS-validated cryptography when used to protect the confidentiality of CUI.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Check system properties to ensure FIPS mode is enabled. Verify that VPNs and encryption tools use FIPS 140-2/3 validated modules.",
                "recommendations": "Only purchase hardware and software that is explicitly listed on the NIST Cryptographic Module Validation Program (CMVP) list."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="CMMC", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('CMMC seeded.'))