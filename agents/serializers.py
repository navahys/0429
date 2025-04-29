from rest_framework import serializers
from .models import EmailTemplate, ScheduledEmail, AgentTask

class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for email templates"""
    class Meta:
        model = EmailTemplate
        fields = ['id', 'name', 'template_type', 'subject', 'content', 
                  'variables', 'conditions', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ScheduledEmailSerializer(serializers.ModelSerializer):
    """Serializer for scheduled emails"""
    class Meta:
        model = ScheduledEmail
        fields = ['id', 'template', 'subject', 'content', 'scheduled_at', 
                  'status', 'created_at', 'sent_at', 'errors']
        read_only_fields = ['id', 'status', 'created_at', 'sent_at', 'errors']
    
    def validate_scheduled_at(self, value):
        """Ensure scheduled time is in the future"""
        from django.utils import timezone
        import datetime
        
        if value < timezone.now():
            raise serializers.ValidationError("예약 시간은 현재 시간 이후여야 합니다.")
        
        # Limit scheduling to 30 days in the future
        max_future = timezone.now() + datetime.timedelta(days=30)
        if value > max_future:
            raise serializers.ValidationError("예약은 최대 30일 이내로만 가능합니다.")
        
        return value

class AgentTaskSerializer(serializers.ModelSerializer):
    """Serializer for agent tasks"""
    class Meta:
        model = AgentTask
        fields = ['id', 'task_type', 'parameters', 'created_at', 'scheduled_at',
                  'started_at', 'completed_at', 'status', 'result', 'errors']
        read_only_fields = ['id', 'created_at', 'started_at', 'completed_at', 
                           'status', 'result', 'errors']
