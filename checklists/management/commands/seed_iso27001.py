# checklists/management/commands/seed_iso27001.py
from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, RiskImpact

class Command(BaseCommand):
    help = 'Seeds the database with ISO 27001:2013 Annex A Checklist Templates'

    def handle(self, *args, **kwargs):
        seed_iso_checklist = [
            {
                "standard": "ISO27001",
                "code": "ISO-A.5.1.1",
                "reference_article": "Control A.5.1.1",
                "title": "Policies for Information Security",
                "description": "A set of policies for information security must be defined, approved by management, and communicated to employees.",
                "risk_impact": "MEDIUM",
                "weight": 1.0,
                "requires_evidence": True,
                "how_to_check": "Request the Information Security Policy (ISP). Check for a formal approval signature (CEO/CTO) and a version history date within the last 12 months.",
                "recommendations": "If no policy exists, use a template aligned with ISO 27001 requirements. Ensure it is hosted on a central intranet where all employees can access it."
            },
            {
                "standard": "ISO27001",
                "code": "ISO-A.8.1.1",
                "reference_article": "Control A.8.1.1",
                "title": "Inventory of Assets",
                "description": "Information, other assets associated with information and information processing facilities must be identified and an inventory maintained.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Review the Asset Register. Verify it includes Hardware, Software, and Information assets. Cross-check 5 random laptops against the list for accuracy.",
                "recommendations": "Implement an automated IT Asset Management (ITAM) tool to track hardware and software licenses in real-time."
            },
            {
                "standard": "ISO27001",
                "code": "ISO-A.9.2.1",
                "reference_article": "Control A.9.2.1",
                "title": "User Registration and De-registration",
                "description": "A formal user registration and de-registration process must be implemented to enable assignment of access rights.",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": True,
                "how_to_check": "Compare the list of current employees against active users in Active Directory/SaaS tools. Check for accounts belonging to former employees.",
                "recommendations": "Link the HR system to the IT identity provider (e.g., Okta, Azure AD) to automate account suspension upon employee termination."
            },
            {
                "standard": "ISO27001",
                "code": "ISO-A.10.1.1",
                "reference_article": "Control A.10.1.1",
                "title": "Policy on the use of Cryptographic Controls",
                "description": "A policy on the use of cryptographic controls for protection of information must be developed and implemented.",
                "risk_impact": "HIGH",
                "weight": 1.5,
                "requires_evidence": False,
                "how_to_check": "Verify that sensitive data (at rest and in transit) is encrypted. Check for the use of modern protocols (e.g., TLS 1.2+ and AES-256).",
                "recommendations": "Enforce Full Disk Encryption (FDE) via MDM (Mobile Device Management) for all company laptops and mobile devices."
            },
            {
                "standard": "ISO27001",
                "code": "ISO-A.11.1.1",
                "reference_article": "Control A.11.1.1",
                "title": "Physical Security Perimeter",
                "description": "Security perimeters must be defined and used to protect areas that contain either sensitive or critical information.",
                "risk_impact": "MEDIUM",
                "weight": 1.0,
                "requires_evidence": True,
                "how_to_check": "Verify physical access controls (badge readers, locks, cameras). Inspect server rooms or sensitive areas for unauthorized access points.",
                "recommendations": "Install a visitor logbook and ensure all guests are escorted by a staff member at all times while in secure areas."
            },
            {
                "standard": "ISO27001",
                "code": "ISO-A.12.4.1",
                "reference_article": "Control A.12.4.1",
                "title": "Event Logging",
                "description": "Event logs recording user activities, exceptions, faults and information security events must be produced, kept and regularly reviewed.",
                "risk_impact": "MEDIUM",
                "weight": 1.2,
                "requires_evidence": True,
                "how_to_check": "Examine the SIEM (Security Information and Event Management) dashboard or log storage. Confirm logs are retained for at least 90 days.",
                "recommendations": "Centralize logs from all critical systems into a single searchable platform. Set up automated alerts for failed login attempts."
            },
            {
                "standard": "ISO27001",
                "code": "ISO-A.12.6.1",
                "reference_article": "Control A.12.6.1",
                "title": "Management of Technical Vulnerabilities",
                "description": "Information about technical vulnerabilities of information systems being used must be obtained and appropriate measures taken.",
                "risk_impact": "HIGH",
                "weight": 2.0,
                "requires_evidence": True,
                "how_to_check": "Review the most recent Vulnerability Scan or Penetration Test report. Verify that 'Critical' and 'High' issues have been remediated.",
                "recommendations": "Schedule monthly automated vulnerability scans. Establish a patching SLA: 48 hours for Critical and 30 days for Medium vulnerabilities."
            },
            {
                "standard": "ISO27001",
                "code": "ISO-A.15.1.1",
                "reference_article": "Control A.15.1.1",
                "title": "Information Security Policy for Supplier Relationships",
                "description": "Information security requirements for mitigating the risks associated with supplier access to assets must be agreed with the supplier.",
                "risk_impact": "MEDIUM",
                "weight": 1.0,
                "requires_evidence": True,
                "how_to_check": "Review vendor contracts. Ensure they include 'Right to Audit' clauses and security requirements (e.g., SOC2 or ISO 27001 certification).",
                "recommendations": "Create a Third-Party Risk Management (TPRM) questionnaire that all new vendors must complete before onboarding."
            },
            {
                "standard": "ISO27001",
                "code": "ISO-A.16.1.1",
                "reference_article": "Control A.16.1.1",
                "title": "Responsibilities and Procedures for Incidents",
                "description": "Management responsibilities and procedures must be established to ensure a quick, effective and orderly response to security incidents.",
                "risk_impact": "HIGH",
                "weight": 1.8,
                "requires_evidence": True,
                "how_to_check": "Request the Incident Response Plan (IRP). Check for a defined 'Incident Response Team' with contact details and escalation paths.",
                "recommendations": "Maintain a 'War Room' protocol and conduct biannual tabletop exercises to ensure the team knows their roles during a live attack."
            }
        ]

        for item in seed_iso_checklist:
            ChecklistTemplate.objects.update_or_create(
                standard="ISO27001",
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

        self.stdout.write(self.style.SUCCESS('Successfully seeded ISO 27001 checklist'))