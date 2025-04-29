from rest_framework import serializers
from .models import CustomUser, MoodRecord

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'birth_date', 'profile_image',
            'mood_tracking_enabled', 'preferred_voice',
            'email_notifications', 'daily_check_in_reminder', 
            'weekly_summary_enabled'
        )
        read_only_fields = ('id', 'username', 'email')

class MoodRecordSerializer(serializers.ModelSerializer):
    """Serializer for mood records"""
    mood_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MoodRecord
        fields = ('id', 'mood', 'mood_display', 'notes', 'recorded_at')
        read_only_fields = ('id', 'recorded_at')
    
    def get_mood_display(self, obj):
        """Return the human-readable mood value"""
        return obj.get_mood_display()
