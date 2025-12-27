# billing/management/commands/export_churn.py
import csv
from django.core.management.base import BaseCommand
from django.http import HttpResponse
from billing.models import ChurnFeedback
from django.utils import timezone

class Command(BaseCommand):
    help = 'Exports churn feedback to a CSV file for analysis'

    def handle(self, *args, **kwargs):
        filename = f"churn_report_{timezone.now().strftime('%Y-%m-%d')}.csv"
        
        # Define the fields to export
        fields = ['created_at', 'email', 'reason', 'plan_at_cancellation']
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write Header
            writer.writerow([f.replace('_', ' ').title() for f in fields])
            
            # Write Data
            feedbacks = ChurnFeedback.objects.all().order_by('-created_at')
            for fb in feedbacks:
                writer.writerow([
                    fb.created_at.strftime('%Y-%m-%d %H:%M'),
                    fb.email,
                    fb.reason,
                    fb.plan_at_cancellation
                ])
                
        self.stdout.write(self.style.SUCCESS(f'Successfully exported report to {filename}'))