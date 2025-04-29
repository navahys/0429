from rest_framework import serializers
from .models import Conversation, Message, VoiceProfile, ConversationFeedback

class MessageSerializer(serializers.ModelSerializer):
    """Serializer for message model"""
    class Meta:
        model = Message
        fields = ['id', 'content', 'content_type', 'message_type', 
                  'created_at', 'voice_file', 'voice_duration', 
                  'sentiment_score', 'voice_id']
        read_only_fields = ['id', 'created_at', 'sentiment_score']

class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversation model"""
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'is_active',
                 'overall_sentiment', 'total_messages', 'messages', 'message_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_messages']
    
    def get_message_count(self, obj):
        return obj.messages.count()

class ConversationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for conversation listing"""
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'is_active',
                 'overall_sentiment', 'total_messages', 'last_message']
    
    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None

class VoiceProfileSerializer(serializers.ModelSerializer):
    """Serializer for voice profiles"""
    class Meta:
        model = VoiceProfile
        fields = ['id', 'name', 'voice_id', 'description', 'category',
                 'is_premium', 'gender', 'age_range', 'accent', 'sample_audio']

class ConversationFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for conversation feedback"""
    class Meta:
        model = ConversationFeedback
        fields = ['id', 'conversation', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

class TextToSpeechRequestSerializer(serializers.Serializer):
    """Serializer for text-to-speech requests"""
    text = serializers.CharField(required=True)
    voice_id = serializers.CharField(required=True)
    speed = serializers.FloatField(default=1.0)
    
    def validate_speed(self, value):
        if value < 0.5 or value > 2.0:
            raise serializers.ValidationError("Speed must be between 0.5 and 2.0")
        return value

class SpeechToTextRequestSerializer(serializers.Serializer):
    """Serializer for speech-to-text requests"""
    audio_file = serializers.FileField(required=True)
    language = serializers.CharField(default="ko-KR")
