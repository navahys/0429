from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class EmailTemplate(models.Model):
    """Model for email templates used by comfort mail agent"""
    
    TEMPLATE_TYPES = [
        ('comfort', _('Comfort Message')),
        ('motivation', _('Motivational Message')),
        ('reminder', _('Wellness Reminder')),
        ('congratulation', _('Congratulations')),
        ('weekly_summary', _('Weekly Summary')),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    # Template variables and parameters
    variables = models.JSONField(default=dict, blank=True)
    conditions = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

class ScheduledEmail(models.Model):
    """Model for scheduled comfort emails"""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scheduled_emails')
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # If custom content (not using template)
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)
    
    # Scheduling information
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    errors = models.TextField(blank=True)
    
    def __str__(self):
        return f"Email to {self.user.username} scheduled for {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"

class AgentTask(models.Model):
    """Model for tracking agent tasks"""
    
    TASK_TYPES = [
        ('comfort_email', _('Comfort Email')),
        ('mood_analysis', _('Mood Analysis')),
        ('wellness_check', _('Wellness Check')),
        ('content_recommendation', _('Content Recommendation')),
        ('conversation_summary', _('Conversation Summary')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agent_tasks')
    task_type = models.CharField(max_length=30, choices=TASK_TYPES)
    parameters = models.JSONField(default=dict, blank=True)
    
    # Scheduling and status
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Results and errors
    result = models.JSONField(default=dict, blank=True, null=True)
    errors = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_task_type_display()} for {self.user.username} - {self.get_status_display()}"
