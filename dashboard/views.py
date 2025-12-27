# dashboard/views.py

from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.db.models import Count

# Models from other apps
from scanner.models import ScanResult
from checklists.models import ChecklistSubmission

# Models from current app
from .models import Alert



def public_home(request):
    """
    Landing page for non-logged-in users.
    Redirects to dashboard if already authenticated.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'dashboard/public_home.html')



class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 1. Resolve Firm safely
        firm = getattr(user, 'firm', None)
        if not firm:
            firm = getattr(user, 'firmprofile', None)
        
        # 2. Pre-define default values to ensure no variable is "missing"
        context.update({
            'firm': firm,
            'last_scan': None,
            'recent_scans': [],
            'top_priority_issue': None,
            'submission': None,
            'submission_id': None,
            'completion_percentage': 0,
            'unread_alerts': 0,
            'total_count': 0,      
            'completed_count': 0,
        })

        if firm:
            # Automated Scans: Force evaluation with list() to avoid lookup errors
            scans_qs = ScanResult.objects.filter(firm=firm).order_by('-scan_date')[:5]
            recent_scans = list(scans_qs)
            last_scan = recent_scans[0] if recent_scans else None
            
            
            
            # Extract Top Priority Issue safely
            top_issue = None
            if last_scan:
                # Assuming get_vulnerabilities returns a list of dicts
                vulnerabilities = last_scan.get_vulnerabilities() or []
                for v in vulnerabilities:
                    sev = str(v.get('severity', '')).upper()
                    if sev in ['HIGH', 'CRITICAL', '8', '9', '10']:
                        top_issue = v
                        break

            # Manual Audit (Roadmap) Logic
            last_sub = ChecklistSubmission.objects.filter(firm=firm).order_by('-created_at').first()
            percentage = 0
            total = 0
            completed = 0
            if last_sub:
                responses = last_sub.responses.all()
                total = responses.count()
                completed = responses.exclude(status='pending').count()
                percentage = int((completed / total) * 100) if total > 0 else 0

            # Update context with real data
            context.update({
                'last_scan': last_scan,
                'recent_scans': recent_scans,
                'top_priority_issue': top_issue,
                'submission': last_sub,
                'submission_id': last_sub.id if last_sub else None,
                'completion_percentage': percentage,
                'unread_alerts': Alert.objects.filter(firm=firm, read=False).count(),
                'total_count': total,       # <--- ADD THIS
                'completed_count': completed, # <--- ADD THIS
                            
            })
            
        return context

class AlertListView(LoginRequiredMixin, ListView):
    """
    View to list all security alerts for a firm.
    """
    model = Alert
    template_name = 'dashboard/alerts.html'
    context_object_name = 'alerts'
    paginate_by = 10

    def get_queryset(self):
        # Your models uses 'scan_date' or 'created_at'—matching your logic here:
        return Alert.objects.filter(firm=self.request.user.firm).order_by('-created_at')


class MarkAlertReadView(LoginRequiredMixin, TemplateView):
    """
    Endpoint to mark alerts as read. 
    NOTE: If this is an HTMX/AJAX call that doesn't need a full page, 
    it's better to inherit from 'View' rather than 'TemplateView'.
    """
    template_name = 'dashboard/includes/alert_row.html' # <--- This also needs a template or it will crash

    def post(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk, firm=request.user.firm)
            alert.read = True
            alert.save()
        except Alert.DoesNotExist:
            pass
        
        # If using HTMX to just update the row, you'd return a specific partial template here.
        # For now, this satisfies the TemplateView requirement:
        return self.render_to_response({'alert': alert})