import io
import json
import uuid
from django.views.generic import ListView, View
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from django.db import transaction
from scanner.models import ScanResult  
from reports.models import ComplianceReport
from .models import ChecklistSubmission, ChecklistResponse, EvidenceFile, ChecklistTemplate
from users.models import FirmProfile
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


# --- 1. CORE WIZARD VIEWS ---

class ChecklistWizardView(ListView):
    """
    Main interface for performing the manual review.
    Uses 'scan_id' (string) to manage the audit workflow.
    """
    template_name = 'checklists/wizard.html'
    context_object_name = 'responses'

    def dispatch(self, request, *args, **kwargs):
        scan_id_str = self.kwargs.get('scan_id')
        submission = ChecklistSubmission.objects.filter(scan__scan_id=scan_id_str).first()
        
        # If audit is already locked, prevent editing and send to report
        if submission and submission.is_locked:
            messages.info(request, "This audit is locked and can no longer be edited.")
            return redirect('checklists:compliance_report', scan_id=scan_id_str)
            
        return super().dispatch(request, *args, **kwargs)

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scan_id_str = self.kwargs.get('scan_id')
        submission = ChecklistSubmission.objects.filter(scan__scan_id=scan_id_str).first()
        
        # Add submission to context
        context['submission'] = submission
        
        if submission:
            # Get the counts needed by progress_bar.html
            responses = submission.responses.all()
            total = responses.count()
            completed = responses.exclude(status='pending').count()
            
            context['total_count'] = total
            context['completed_count'] = completed
            context['completion_percentage'] = int((completed / total) * 100) if total > 0 else 0
            
        return context
        
    
    def get_queryset(self):
        scan_id_str = self.kwargs.get('scan_id')
        scan_obj = get_object_or_404(ScanResult, scan_id=scan_id_str)
        submission = ChecklistSubmission.objects.filter(scan=scan_obj).first()

        # 1. Create submission if it doesn't exist
        if not submission:
            with transaction.atomic():
                submission = ChecklistSubmission.objects.create(
                    scan=scan_obj,
                    firm=self.request.user.firm
                )
                
                report, _ = ComplianceReport.objects.get_or_create(scan=scan_obj)
                templates = ChecklistTemplate.objects.filter(active=True)
                
                responses = [
                    ChecklistResponse(
                        submission=submission,
                        template=t,
                        report=report,
                        status='pending'
                    ) for t in templates
                ]
                ChecklistResponse.objects.bulk_create(responses)

        # 2. Find the most recent previous LOCKED submission for HINT logic
        previous_submission = ChecklistSubmission.objects.filter(
            firm=self.request.user.firm,
            is_locked=True
        ).exclude(id=submission.id).order_by('-created_at').first()

        prev_answers = {}
        if previous_submission:
            prev_answers = {
                resp.template_id: resp.status 
                for resp in previous_submission.responses.all()
            }

        # 3. Get the current responses and inject hints dynamically
        qs = submission.responses.select_related('template')\
                                   .prefetch_related('evidence_files')\
                                   .order_by('template__code')
        
        for r in qs:
            r.hint_status = prev_answers.get(r.template_id)

        return qs


class UpdateResponseView(View):
    """
    HTMX-driven view to update individual checklist answers.
    """
    def post(self, request, response_id):
        resp = get_object_or_404(ChecklistResponse, id=response_id)
        
        if resp.submission.is_locked:
            return HttpResponseForbidden("Cannot update a locked audit.")

        # Update fields if present in POST data
        if 'status' in request.POST:
            resp.status = request.POST.get('status')
        if 'comment' in request.POST:
            resp.comment = request.POST.get('comment')
        resp.save()
        
        submission = resp.submission
        total = submission.responses.count()
        completed = submission.responses.exclude(status='pending').count()
        
        # Prepare HTMX Response
        django_response = render(request, 'checklists/partials/status_buttons.html', {'resp': resp})
        
        triggers = {
            "responseUpdated": True, 
            "refreshScore": True     
        }
        
        # Signal the UI if the entire audit is ready for completion
        if total > 0 and completed == total:
            triggers["auditComplete"] = True  
            
        django_response["HX-Trigger"] = json.dumps(triggers)
        return django_response 


# --- 2. REPORTING & DASHBOARD VIEWS ---

def compliance_report(request, scan_id):
    """ 
    The 'Gap Analysis' view. Shows compliance scores and risks.
    """
    scan = get_object_or_404(ScanResult, scan_id=scan_id)
    
    submission, _ = ChecklistSubmission.objects.get_or_create(
        scan=scan,
        defaults={'firm': scan.firm}
    )

    responses = submission.responses.select_related('template', 'submission__firm').all().order_by('-template__risk_impact')

    risk_config = [
        {
            'level': 'HIGH', 
            'color': 'rose', 
            'icon': '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>'
        },
        {
            'level': 'MEDIUM', 
            'color': 'amber', 
            'icon': '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'
        },
        {
            'level': 'LOW', 
            'color': 'emerald', 
            'icon': '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'
        },
    ]

    context = {
        'submission': submission,
        'overall_score': submission.calculate_compliance_score() or 0,
        'risk_stats': submission.get_risk_breakdown(),
        'responses': responses,
        'risk_config': risk_config, 
    }
    return render(request, 'checklists/compliance_dashboard.html', context)


def complete_audit(request, submission_id):
    """
    Locks the submission so no further changes can be made.
    """
    submission = get_object_or_404(ChecklistSubmission, id=submission_id, firm=request.user.firm)
    
    if request.method == "POST":
        submission.is_locked = True
        submission.save()
        messages.success(request, "Audit finalized and locked successfully.")
        return redirect('checklists:compliance_report', scan_id=submission.scan.scan_id)
    
    return redirect('checklists:wizard', scan_id=submission.scan.scan_id)


# --- 3. UTILITY & AJAX VIEWS ---

def get_progress(request, submission_id):
    """ Returns a partial HTML for the progress bar. """
    submission = get_object_or_404(ChecklistSubmission.objects.select_related('scan'), id=submission_id)
    responses = submission.responses.all()
    total = responses.count()
    completed = responses.exclude(status='pending').count()
    
    return render(request, 'checklists/partials/progress_bar.html', {
        'submission': submission,
        'completion_percentage': int((completed / total) * 100) if total > 0 else 0,
        'completed_count': completed,
        'total_count': total,
    })


class EvidenceUploadView(View):
    """ Handles file uploads for compliance evidence. """
    def post(self, request, response_id):
        response = get_object_or_404(ChecklistResponse, id=response_id)
        if response.submission.is_locked: 
            return HttpResponseForbidden("Audit is locked.")

        files = request.FILES.getlist('evidence')
        for f in files:
            EvidenceFile.objects.create(
                response=response, 
                file=f, 
                filename=f.name, 
                uploaded_by=request.user
            )
        return render(request, 'checklists/partials/evidence_list.html', {'response': response})


def delete_submission(request, submission_id):
    """ Archival view for deleting audit records. """
    if request.method == 'POST':
        submission = get_object_or_404(
            ChecklistSubmission, 
            id=submission_id, 
            firm=request.user.firm
        )
        submission.delete()
        messages.success(request, "Audit record successfully archived.")
    return redirect('checklists:submission_list')


def generate_checklist_pdf(request, pk):
    submission = get_object_or_404(ChecklistSubmission, id=pk, firm=request.user.firm)
    responses = submission.responses.all().select_related('template')
    scan = submission.scan 
    
    raw_data = scan.raw_data or {}
    tech_findings = raw_data.get('findings', [])

    context = {
        'submission': submission,
        'responses': responses,
        'scan': scan,
        'firm': request.user.firm,
        'tech_findings': tech_findings, 
        'compliance_index': submission.calculate_compliance_score(),
        'generated_at': timezone.now(),
        'signature': uuid.uuid4().hex[:16].upper(),
        'host': request.get_host(),
    }

    html_string = render_to_string('checklists/pdf_report_template.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf_buffer = io.BytesIO()
    html.write_pdf(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"Compliance_Report_{submission.scan.scan_id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def submission_list(request):
    """ Overview of all audits within the firm. """
    submissions = ChecklistSubmission.objects.filter(
        firm=request.user.firm
    ).select_related('scan').order_by('-created_at')
    
    return render(request, 'checklists/submission_list.html', {'submissions': submissions})


def get_roadmap(request, scan_id):
    submission = get_object_or_404(
        ChecklistSubmission.objects.select_related('scan'), 
        scan__scan_id=scan_id, 
        firm=request.user.firm
    )
    
    all_responses = submission.responses.select_related('template')
    total_count = all_responses.count()
    completed_count = all_responses.exclude(status='pending').count()
    completion_percentage = int((completed_count / total_count) * 100) if total_count > 0 else 0
    
    roadmap_responses = all_responses.exclude(status='yes').prefetch_related('evidence_files').order_by('template__code')

    context = {
        'submission': submission,
        'responses': roadmap_responses,
        'overall_score': submission.calculate_compliance_score(),
        'last_scan': submission.scan,
        'completion_percentage': completion_percentage,
        'total_count': total_count,
        'completed_count': completed_count,
    }
    return render(request, 'checklists/risk_roadmap.html', context)


def delete_evidence(request, evidence_id):
    evidence = get_object_or_404(EvidenceFile, id=evidence_id)
    
    if evidence.response.submission.is_locked:
        return HttpResponseForbidden("Cannot delete evidence from a locked audit.")
    
    if evidence.response.submission.firm != request.user.firm:
        return HttpResponseForbidden("Unauthorized.")

    evidence.delete()
    return HttpResponse("")
    
########   
# CHECKLIST TOP simple and detailed checklist settings
################# 
@login_required
@require_POST
def update_scan_mode(request):
    mode = request.POST.get('scan_mode')
    if mode in ['simple', 'detailed'] and hasattr(request.user, 'firmprofile'):
        profile = request.user.firmprofile
        profile.scan_mode = mode
        profile.save()
        
        # We return a 204 No Content because the UI updates via Alpine.js 
        # or we can return a trigger to refresh the checklist items
        response = HttpResponse(status=204)
        response["HX-Refresh"] = "true"  # Force refresh to show/hide detailed fields
        return response
    return HttpResponse(status=400)