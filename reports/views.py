# reports/views.py
import os
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from weasyprint import HTML
from .models import ComplianceReport
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from users.models import FirmProfile
from scanner.models import ScanResult
from core.mixins import FirmRequiredMixin
import io
import hashlib
from django.utils.timezone import now
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.files.base import ContentFile
from .models import ComplianceReport, ReportVerification
from scanner.models import ScanResult 
from checklists.models import ChecklistResponse



class ReportListView(FirmRequiredMixin, ListView):
    model = ComplianceReport
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 12

    def get_queryset(self):
        # request.user.firm is guaranteed to exist by the Mixin
        return ComplianceReport.objects.filter(scan__firm=self.request.user.firm).order_by('-generated_at')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if any scan exists
        context['has_scans'] = self.get_queryset().exists()
        return context


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = ComplianceReport
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'

    def dispatch(self, request, *args, **kwargs):
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)
    
    
    def get_queryset(self):
        return ComplianceReport.objects.filter(scan__firm=self.request.user.firmprofile)


class ReportDownloadView(LoginRequiredMixin, View):
    
    def dispatch(self, request, *args, **kwargs):
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)
    
    
    def get(self, request, pk):
        report = get_object_or_404(ComplianceReport, pk=pk, scan__firm=request.user.firmprofile)
        if not report.pdf_file or not os.path.exists(report.pdf_file.path):
            raise Http404("PDF not generated yet.")
        return FileResponse(
            open(report.pdf_file.path, 'rb'),
            as_attachment=True,
            filename=f"ComplyNet_Report_{report.scan.domain}_{report.pk}.pdf"
        )



'''
class ReportPreviewView(LoginRequiredMixin, View):
    
    
    def dispatch(self, request, *args, **kwargs):
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)
    
    
    def get(self, request, pk):
        report = get_object_or_404(ComplianceReport, pk=pk, scan__firm=request.user.firmprofile)
        if not report.pdf_file or not os.path.exists(report.pdf_file.path):
            report.generate_pdf(request)  # Pass request for base_url
        return FileResponse(
            open(report.pdf_file.path, 'rb'),
            content_type='application/pdf'
        )
        
    def generate_pdf(self, report):
        html_string = render(request, 'reports/pdf_template.html', {
            'report': report,
            'scan': report.scan,
            'firm': report.scan.firm,
            'generated_at': timezone.now(),
        }).content.decode('utf-8')

        pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(
            stylesheets=[os.path.join('static', 'css', 'pdf-styles.css')]
        )

        # Save to model
        from django.core.files.base import ContentFile
        pdf_file = ContentFile(pdf)
        report.pdf_file.save(f"report_{report.pk}.pdf", pdf_file, save=True)
        
'''

class ReportPreviewView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        report = get_object_or_404(ComplianceReport, pk=pk, scan__firm=request.user.firmprofile)
        if not report.pdf_file or not os.path.exists(report.pdf_file.path):
            # Generate PDF on-the-fly with all computed fields
            report.generate_pdf(request)  # request needed for base_url in template

        return FileResponse(
            open(report.pdf_file.path, 'rb'),
            content_type='application/pdf'
        )





def verify_report(request):
    """
    Verify a report using its report_id.
    Works with GET (query param) or POST (form submission).
    """
    report_id = request.GET.get("report_id") or request.POST.get("report_id", "").strip()
    context = {"searched": False}

    if report_id:
        context["searched"] = True
        try:
            report = ReportVerification.objects.select_related('scan').get(report_id=report_id)
            context["valid"] = True
            context["report"] = report
        except ReportVerification.DoesNotExist:
            context["valid"] = False

    return render(request, "reports/verify_report.html", context)
    
    
    
    
##########################################
# FOR COMPLIANCE REPORTS
########################################




def generate_professional_audit_report(request, scan_id):
    # 1. Fetch Data
    scan = get_object_or_404(ScanResult, scan_id=scan_id, firm=request.user.firm)
    
    # 2. Calculate Weighted Compliance Score
    # Assuming ChecklistResponse relates to ChecklistTemplate and ScanResult
    responses = ChecklistResponse.objects.filter(scan=scan).select_related('template')
    
    total_weight = 0
    earned_weight = 0
    for res in responses:
        weight = res.template.weight
        total_weight += weight
        if res.status == 'COMPLIANT':
            earned_weight += weight
        elif res.status == 'PARTIAL':
            earned_weight += (weight * 0.5)

    compliance_score = (earned_weight / total_weight * 100) if total_weight > 0 else 0
    
    # 3. Determine Grade based on Score
    if compliance_score >= 90: grade = 'A'
    elif compliance_score >= 80: grade = 'B'
    elif compliance_score >= 70: grade = 'C'
    elif compliance_score >= 60: grade = 'D'
    else: grade = 'F'

    # 4. Prepare Context
    current_host = request.get_host()
    context = {
        'scan': scan,
        'responses': responses,
        'compliance_score': compliance_score,
        'grade': grade,
        'generated_at': now(),
        'host': current_host,
        'report_id': f"CR-{scan.scan_id}-{now().strftime('%y%m%d')}",
    }

    # 5. Render HTML to String
    html_string = render_to_string('reports/audit_report_v2.html', context)
    
    # 6. Generate PDF with Integrity Hash
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf_bytes = html.write_pdf()
    
    # Cryptographic Hash for Verification (SHA-256)
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # 7. Save and Record for Verification Portal
    report, _ = ComplianceReport.objects.update_or_create(
        scan=scan,
        defaults={'pdf_file': ContentFile(pdf_bytes, name=f"Audit_{scan.scan_id}.pdf")}
    )
    
    ReportVerification.objects.update_or_create(
        report_id=scan.scan_id,
        defaults={
            'pdf_sha256': pdf_hash,
            'verification_token': hashlib.md5(f"{scan.scan_id}{settings.SECRET_KEY}".encode()).hexdigest()
        }
    )

    # 8. Return PDF Response
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Audit_Report_{scan.domain}.pdf"'
    return response


#########################################
## COMPLIANCE SECTION
#######################################




def generate_compliance_audit_pdf(request, pk):
    """
    Generates an International Standard (ISO/NIST style) Audit Report.
    Includes both Technical Scan Findings + Manual Checklist Controls.
    """
    report = get_object_or_404(ComplianceReport, pk=pk)
    scan = report.scan
    
    # 1. Fetch Technical Findings (from your existing model logic)
    tech_findings = report.map_gdpr_articles()
    
    # 2. Fetch Manual Checklist Responses (SOC2, HIPAA, etc.)
    responses = report.checklist_responses.all().select_related('template')
    
    # 3. Calculate Weighted Score (International Standard Calculation)
    total_possible_weight = 0
    earned_weight = 0
    
    for r in responses:
        weight = r.template.weight
        total_possible_weight += weight
        if r.status == 'COMPLIANT':
            earned_weight += weight
        elif r.status == 'PARTIAL':
            earned_weight += (weight * 0.5)

    compliance_index = (earned_weight / total_possible_weight * 100) if total_possible_weight > 0 else 0
    
    # 4. Generate Cryptographic Hash for Verification
    # We hash the combination of the scan ID and the result to ensure it's untamperable
    integrity_string = f"{scan.scan_id}-{compliance_index}-{report.generated_at}"
    digital_signature = hashlib.sha256(integrity_string.encode()).hexdigest()

    # 5. Prepare Context for "State of the Art" Template
    context = {
        'report': report,
        'scan': scan,
        'tech_findings': tech_findings,
        'responses': responses,
        'compliance_index': compliance_index,
        'legal_exposure': report.calculate_legal_exposure(tech_findings),
        'signature': digital_signature,
        'host': request.get_host(),
    }

    # Render to HTML then PDF (using your existing WeasyPrint setup)
    html_string = render_to_string('reports/international_audit_pdf.html', context)
    pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    
    # Save verification record for the QR code
    ReportVerification.objects.update_or_create(
        report_id=scan.scan_id[:16],
        defaults={
            'domain': scan.domain,
            'scan': scan,
            'pdf_sha256': digital_signature,
            'generated_at': report.generated_at
        }
    )

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Audit_Report_{scan.domain}.pdf"'
    return response