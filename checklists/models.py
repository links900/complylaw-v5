# checklists/models.py

import uuid
from django.db import models
from django.conf import settings
from scanner.models import ScanResult
from dashboard.models import FirmProfile

class RiskImpact(models.TextChoices):
    HIGH = 'HIGH', 'High'
    MEDIUM = 'MEDIUM', 'Medium'
    LOW = 'LOW', 'Low'

class ChecklistTemplate(models.Model):
    standard = models.CharField(max_length=50, db_index=True)
    code = models.CharField(max_length=50)
    reference_article = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    risk_impact = models.CharField(max_length=10, choices=RiskImpact.choices, default=RiskImpact.MEDIUM)
    weight = models.FloatField(default=1.0)
    requires_evidence = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    how_to_check = models.TextField(
        blank=True, 
        help_text="Detailed instructions for the auditor on how to verify this control."
    )
    recommendations = models.TextField(
        blank=True, 
        help_text="Guidance on how to fix the issue if the control is not compliant."
    )

    class Meta:
        unique_together = ('standard', 'code')

    def __str__(self):
        return f"[{self.standard}] {self.code}"

class ChecklistSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # CHANGE: From OneToOneField to ForeignKey
    # This allows Scan #8 to have Submission A, Submission B, etc.
    scan = models.ForeignKey(
        ScanResult, 
        on_delete=models.CASCADE, 
        related_name='manual_audits'
    )
    
    # ADD: This identifies which standard this specific submission belongs to
    standard = models.CharField(max_length=50, db_index=True)
    
       
    firm = models.ForeignKey(FirmProfile, on_delete=models.CASCADE)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # IMPORTANT: This ensures a scan cannot have TWO submissions 
        # for the SAME standard (e.g., two GDPR audits for one scan)
        unique_together = ('scan', 'standard')

    def __str__(self):
        return f"Audit: {self.scan.domain} ({self.created_at.date()})"

    @property
    def score(self):
        """Helper to call score in templates as {{ submission.score }}"""
        return self.calculate_compliance_score()

    def calculate_compliance_score(self):
        """
        Formula: (Sum of earned weights / Total possible weights) * 100
        """
        responses = self.responses.select_related('template').all()
        if not responses.exists():
            return 0

        total_possible_weight = 0
        earned_weight = 0

        for resp in responses:
            weight = resp.template.weight
            total_possible_weight += weight

            if resp.status == 'yes':
                earned_weight += weight
            elif resp.status == 'partial':
                earned_weight += (weight * 0.5)
            # 'no' and 'pending' contribute 0

        if total_possible_weight == 0:
            return 0

        return round((earned_weight / total_possible_weight) * 100, 0)

    def get_risk_breakdown(self):
        """
        Returns a structured dictionary for the SaaS Dashboard.
        Aligns with keys used in the HTML: 'percentage', 'completed', 'total'
        """
        stats = {}
        # Prefetch responses to avoid 3 separate queries in the loop
        all_responses = self.responses.select_related('template').all()

        for level in RiskImpact.values:
            level_responses = [r for r in all_responses if r.template.risk_impact == level]
            total = len(level_responses)
            # Count 'yes' as completed
            completed = len([r for r in level_responses if r.status == 'yes'])
            
            stats[level] = {
                'total': total,
                'completed': completed,
                'percentage': round((completed / total * 100), 0) if total > 0 else 0
            }
        return stats
        
        
        
    @property
    def completion_stats(self):
        total = self.responses.count()
        completed = self.responses.exclude(status='pending').count()
        percent = int((completed / total) * 100) if total > 0 else 0
        return {'total': total, 'completed': completed, 'percent': percent}
        

class ChecklistResponse(models.Model):
    # This must point to the ComplianceReport model in the reports app
    report = models.ForeignKey(
        'reports.ComplianceReport', 
        on_delete=models.CASCADE, 
        related_name='checklist_responses'
    )
    template = models.ForeignKey(
        'ChecklistTemplate', 
        on_delete=models.CASCADE,
        related_name='responses' # Added related_name to solve the E304 clash
    )
    
    # Added 'pending' as default to match your Wizard logic
    STATUS_CHOICES = [
        ("yes", "Yes"), 
        ("no", "No"), 
        ("partial", "Partial"), 
        ("pending", "Pending"),
        ("na", "N/A")
    ]
    submission = models.ForeignKey(ChecklistSubmission, on_delete=models.CASCADE, related_name='responses')
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('submission', 'template')
        ordering = ['template__code']

    def __str__(self):
        return f"{self.template.code} - {self.status}"

class EvidenceFile(models.Model):
    response = models.ForeignKey(ChecklistResponse, on_delete=models.CASCADE, related_name='evidence_files')
    file = models.FileField(upload_to="evidence/%Y/%m/%d/")
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    

