# billing/models.py


from django.db import models
from django.conf import settings

class ChurnFeedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField()
    reason = models.CharField(max_length=255)
    plan_at_cancellation = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.reason}"