# checklists/admin.py
#checklists/admin.py

from django.contrib import admin
from .models import ChecklistTemplate, ChecklistSubmission, ChecklistResponse, EvidenceFile

@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ('standard', 'code', 'title', 'risk_impact', 'active')
    list_filter = ('standard', 'risk_impact', 'active')
    search_fields = ('code', 'title', 'description')
    ordering = ('standard', 'code')

class ChecklistResponseInline(admin.TabularInline):
    model = ChecklistResponse
    extra = 0
    # Keep this inline simple for the Submission view
    fields = ('template', 'status', 'comment')
    readonly_fields = ('template',)

@admin.register(ChecklistSubmission)
class ChecklistSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'scan', 'firm', 'created_at', 'is_locked')
    list_filter = ('is_locked', 'created_at')
    inlines = [ChecklistResponseInline]

@admin.register(EvidenceFile)
class EvidenceFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'response', 'uploaded_by', 'uploaded_at')