#reports/admin.py

from django.contrib import admin, messages
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.utils.html import format_html

from .models import ComplianceReport
from checklists.models import ChecklistResponse, ChecklistTemplate


# This inline is needed here so we can edit responses directly inside the Report
class ChecklistResponseInline(admin.TabularInline):
    model = ChecklistResponse
    extra = 0
    fields = ('template', 'status', 'auditor_comment', 'verified_by')
    readonly_fields = ('template',)

@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ('scan', 'generated_at', 'get_tech_score', 'audit_progress_bar')
    list_filter = ('generated_at', 'scan__grade')
    search_fields = ('scan__domain',)
    inlines = [ChecklistResponseInline]
    actions = ['bulk_add_standards']

    def get_tech_score(self, obj):
        score = obj.scan.risk_score
        color = "green" if score < 30 else "orange" if score < 70 else "red"
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, score)
    get_tech_score.short_description = 'Scan Risk'

    def audit_progress_bar(self, obj):
        progress = obj.get_audit_progress()
        color = "#e74c3c" if progress < 30 else "#f1c40f" if progress < 100 else "#2ecc71"
        return format_html(
            '<div style="width:100px;background:#eee;border-radius:4px;overflow:hidden;border:1px solid #ccc;">'
            '<div style="width:{}px;background:{};height:12px;"></div>'
            '</div><div style="font-size:10px;">{}% Complete</div>',
            progress, color, progress
        )
    audit_progress_bar.short_description = 'Audit Progress'

    def bulk_add_standards(self, request, queryset):
        if 'apply' in request.POST:
            standard_name = request.POST.get('standard_name')
            templates = ChecklistTemplate.objects.filter(standard=standard_name, active=True)
            for report in queryset:
                for template in templates:
                    ChecklistResponse.objects.get_or_create(
                        report=report, template=template,
                        defaults={'status': 'NON_COMPLIANT'}
                    )
                try:
                    from .compliance_logic import run_auto_audit
                    run_auto_audit(report)
                except ImportError:
                    pass
            self.message_user(request, f"Applied {standard_name} to selected reports.")
            return HttpResponseRedirect(request.get_full_path())

        standards = ChecklistTemplate.objects.values_list('standard', flat=True).distinct()
        return render(request, 'admin/reports/bulk_add_standard.html', {
            'reports': queryset, 'standards': standards,
        })
    bulk_add_standards.short_description = "🚀 Bulk Add Standard & Run Smart Audit"