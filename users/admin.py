# users/admin.py

from django.contrib import admin
from .models import RegulatoryStandard, TierStandard, FirmProfile

@admin.register(RegulatoryStandard)
class RegulatoryStandardAdmin(admin.ModelAdmin):
    """Admin for the library of all available standards."""
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(TierStandard)
class TierStandardAdmin(admin.ModelAdmin):
    """Admin to map standards to Basic, Professional, and Enterprise tiers."""
    list_display = ('tier',)
    # This creates a side-by-side selection box which is better for ManyToMany
    filter_horizontal = ('standards',)

# Update your existing FirmProfile registration or replace it
@admin.register(FirmProfile)
class FirmProfileAdmin(admin.ModelAdmin):
    """Admin to manage specific firms and assign extra standards."""
    list_display = ('firm_name', 'subscription_tier', 'user', 'is_active')
    list_filter = ('subscription_tier', 'is_active')
    search_fields = ('firm_name', 'email', 'domain')
    
    # This allows the admin to assign specific standards to a specific user
    filter_horizontal = ('additional_standards',)
    
    fieldsets = (
        ('Identity', {'fields': ('firm_name', 'email', 'domain', 'user', 'logo')}),
        ('Subscription & Access', {'fields': ('subscription_tier', 'additional_standards', 'is_active')}),
        ('Compliance Settings', {'fields': ('active_standard', 'scan_mode', 'retention_days')}),
        ('Localization', {'fields': ('timezone', 'currency', 'date_format')}),
    )