# billing/admin.py
from django.contrib import admin
from .models import ChurnFeedback

@admin.register(ChurnFeedback)
class ChurnFeedbackAdmin(admin.ModelAdmin):
    list_display = ('email', 'reason', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('email', 'reason')
