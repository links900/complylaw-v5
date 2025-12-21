from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds SOC 2 Trust Services Criteria'

    def handle(self, *args, **kwargs):
        data = [
            {
                "standard": "SOC2",
                "code": "CC1.1",
                "reference_article": "Common Criteria 1.1",
                "title": "Integrity and Ethical Values",
                "description": "The organization demonstrates a commitment to integrity and ethical values.",
                "risk_impact": "MEDIUM",
                "weight": 1.0,
                "requires_evidence": True,
                "how_to_check": "Review the signed Code of Conduct and whistleblower policy. Verify employees acknowledge these during onboarding.",
                "recommendations": "Implement an automated HR onboarding workflow that requires a digital signature on the Code of Ethics."
            },
            {
                "standard": "SOC2",
                "code": "CC6.1",
                "reference_article": "Common Criteria 6.1",
                "title": "Logical Access Security",
                "description": "The CO restricts logical access to confidential information assets.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Inspect IAM (Identity Access Management) settings. Check for MFA on all production environments and administrative accounts.",
                "recommendations": "Enable SSO (Single Sign-On) and enforce a 'No MFA, No Access' policy for all cloud resources."
            },
            {
                "standard": "SOC2",
                "code": "CC7.1",
                "reference_article": "Common Criteria 7.1",
                "title": "System Operations & Monitoring",
                "description": "The CO evaluates and mitigates security risks associated with system changes and operations.",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Check the Change Management log. Ensure every production change has a corresponding ticket and peer review/approval.",
                "recommendations": "Integrate Jira or ServiceNow with GitHub/GitLab to prevent code merges without approved change tickets."
            }
        ]
        for item in data:
            ChecklistTemplate.objects.update_or_create(standard="SOC2", code=item['code'], defaults=item)
        self.stdout.write(self.style.SUCCESS('SOC2 seeded.'))