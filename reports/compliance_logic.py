# reports/compliance_logic.py

def run_auto_audit(compliance_report):
    """
    Automated cross-referencing: Maps technical findings to GRC controls.
    """
    responses = compliance_report.checklist_responses.all()
    scan = compliance_report.scan
    
    # Extract technical data (adjust keys based on your ScanResult structure)
    raw_data = getattr(scan, 'raw_data', {})
    grade = getattr(scan, 'grade', 'F')
    risk_score = getattr(scan, 'risk_score', 100)

    # 1. SSL/TLS CONTROL MAPPING
    ssl_valid = raw_data.get('ssl_valid', False)
    if ssl_valid:
        responses.filter(template__code__icontains="SSL").update(
            status='COMPLIANT', 
            auditor_comment="[AUTO-AUDIT] Technical scan confirmed a valid SSL/TLS configuration."
        )

    # 2. ENCRYPTION & SECURE HEADERS (GDPR Art. 32 / ISO A.12.6.1)
    if grade in ['A+', 'A', 'B']:
        responses.filter(template__title__icontains="Encryption").update(
            status='COMPLIANT',
            auditor_comment=f"[AUTO-AUDIT] High security grade ({grade}) validates technical encryption controls."
        )

    # 3. IDENTIFYING NON-COMPLIANCE
    if risk_score > 70:
        responses.filter(template__title__icontains="Vulnerability").update(
            status='NON_COMPLIANT',
            auditor_comment="[AUTO-AUDIT] Critical vulnerabilities detected in technical scan."
        )

    return True