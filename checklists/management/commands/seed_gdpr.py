# checklists/management/commands/seed_gdpr.py
# checklists/management/commands/seed_compliance.py


from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds the database with GDPR Checklist Templates including audit steps and recommendations'

    def handle(self, *args, **kwargs):
        seed_gdpr_checklist = [
            {
                "standard": "GDPR",
                "code": "GDPR-01",
                "reference_article": "Article 30",
                "title": "Record of Processing Activities (ROPA)",
                "description": "The organization must maintain a central registry of all personal data processing activities.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Request the ROPA document. Verify it includes: purpose of processing, categories of data subjects, categories of personal data, recipients, and retention periods.",
                "recommendations": "Use a centralized template for all departments. Conduct annual interviews with department heads to ensure the registry is up to date."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-02",
                "reference_article": "Articles 12, 13, 14",
                "title": "Privacy Notice & Transparency",
                "description": "Privacy notices must be concise, transparent, and easily accessible.",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Review the public-facing privacy policy on the website and internal employee notices. Check for clear language and inclusion of data subject rights.",
                "recommendations": "Ensure the notice is accessible at the point of data collection (e.g., web forms). Use a 'layered' notice approach for better readability."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-03",
                "reference_article": "Article 6",
                "title": "Lawfulness of Processing",
                "description": "A valid legal basis must be identified for every processing activity.",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": False,
                "how_to_check": "Cross-reference the ROPA against Article 6 legal bases. Ensure 'Legitimate Interest' use is backed by an assessment (LIA).",
                "recommendations": "Document a 'Legitimate Interest Assessment' for any processing not covered by consent, contract, or legal obligation."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-04",
                "reference_article": "Article 32",
                "title": "Security of Processing (TOMs)",
                "description": "Implementation of Technical and Organizational Measures (TOMs).",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Audit technical controls: check for disk encryption, SSL/TLS certificates, 2FA implementation, and evidence of recent penetration testing.",
                "recommendations": "Adopt an industry standard like ISO 27001 or NIST. Automate security patching and implement 'Least Privilege' access controls."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-05",
                "reference_article": "Article 35",
                "title": "Data Protection Impact Assessment (DPIA)",
                "description": "Process for conducting assessments for high-risk processing operations.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Review the DPIA policy. Look for completed DPIA reports for recent high-risk projects (e.g., AI implementation, large-scale monitoring).",
                "recommendations": "Integrate a 'DPIA Trigger' questionnaire into the initial phase of the Project Management Office (PMO) or software development lifecycle."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-06",
                "reference_article": "Articles 15-22",
                "title": "Data Subject Rights Procedure",
                "description": "Workflows to handle requests (DSAR, erasure, etc.) within 30 days.",
                "risk_impact": "MEDIUM",
                "weight": 1.0,
                "requires_evidence": True,
                "how_to_check": "Inspect the DSAR log. Verify that requests were acknowledged and fulfilled within the statutory 30-day window.",
                "recommendations": "Create standardized response templates for different request types. Train customer support teams on how to identify a verbal DSAR."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-07",
                "reference_article": "Articles 33 & 34",
                "title": "Data Breach Notification Protocol",
                "description": "Procedure to report breaches to the Authority within 72 hours.",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Examine the Incident Response Plan and the Data Breach Log. Check if past incidents were evaluated for notification requirements.",
                "recommendations": "Conduct 'Tabletop Exercises' annually to simulate a data breach and test the effectiveness of the 72-hour reporting timeline."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-08",
                "reference_article": "Article 28",
                "title": "Processor & Third-Party Contracts",
                "description": "Presence of Data Processing Agreements (DPAs) with all vendors.",
                "risk_impact": "MEDIUM",
                "weight": 1.2,
                "requires_evidence": True,
                "how_to_check": "Sample 10% of vendor contracts. Verify they include mandatory clauses (audit rights, breach notification, sub-processor rules).",
                "recommendations": "Maintain a master list of processors. Use a standardized DPA addendum for all new vendor onboardings."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-09",
                "reference_article": "Article 37",
                "title": "DPO Appointment & Governance",
                "description": "Designation of a DPO or documentation explaining why one isn't required.",
                "risk_impact": "LOW",
                "weight": 0.8,
                "requires_evidence": False,
                "how_to_check": "Verify the appointment letter of the DPO. If no DPO is appointed, check for a formal memo justifying this decision.",
                "recommendations": "Ensure the DPO has a direct reporting line to the board and is involved in all issues relating to the protection of personal data."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-10",
                "reference_article": "Articles 44-49",
                "title": "International Data Transfers",
                "description": "Ensuring protection for data transferred outside the EEA/UK.",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Identify all vendors outside the EEA. Check for 'Standard Contractual Clauses' (SCCs) and 'Transfer Impact Assessments' (TIAs).",
                "recommendations": "Migrate data to EEA-based servers where possible. For US transfers, verify if the vendor is certified under the Data Privacy Framework."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-11",
                "reference_article": "Article 5(1)(e)",
                "title": "Data Retention & Disposal Policy",
                "description": "Policy defining how long data is kept and how it is deleted.",
                "risk_impact": "MEDIUM",
                "weight": 1.0,
                "requires_evidence": True,
                "how_to_check": "Review the Data Retention Schedule. Verify that a sample of data older than the retention period has been deleted or anonymized.",
                "recommendations": "Implement automated deletion scripts in databases. For physical records, ensure a certificate of destruction is obtained from shredding vendors."
            },
            {
                "standard": "GDPR",
                "code": "GDPR-12",
                "reference_article": "Article 25",
                "title": "Privacy by Design & Default",
                "description": "Integrating data protection into system development.",
                "risk_impact": "MEDIUM",
                "weight": 1.0,
                "requires_evidence": False,
                "how_to_check": "Review product design documents or sprint planning notes for privacy requirements (e.g., data minimization by default).",
                "recommendations": "Include privacy reviews in the 'Definition of Done' for development teams. Ensure default settings are always the most privacy-restrictive."
            }
        ]

        for item in seed_gdpr_checklist:
            obj, created = ChecklistTemplate.objects.update_or_create(
                standard="GDPR",
                code=item['code'],
                defaults={
                    "reference_article": item['reference_article'],
                    "title": item['title'],
                    "description": item['description'],
                    "risk_impact": item['risk_impact'],
                    "weight": item['weight'],
                    "requires_evidence": item['requires_evidence'],
                    "how_to_check": item['how_to_check'],
                    "recommendations": item['recommendations'],
                    "active": True
                }
            )
            status = "Created" if created else "Updated"
            self.stdout.write(f"{status}: {item['code']}")

        self.stdout.write(self.style.SUCCESS('Successfully seeded GDPR checklist'))
        