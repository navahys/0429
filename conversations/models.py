from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Conversation(models.Model):
    """Model to store conversation sessions"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Sentiment analysis results
    overall_sentiment = models.FloatField(null=True, blank=True)
    
    # Metadata
    total_messages = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Conversation {self.id} - {self.title or 'Untitled'}"
    
    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    """Model to store individual messages in a conversation"""
    
    TYPE_CHOICES = [
        ('user', _('User')),
        ('assistant', _('Assistant')),
        ('system', _('System')),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    content_type = models.CharField(max_length=10, default='text')
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Voice related fields
    voice_file = models.FileField(upload_to='voice_messages/', null=True, blank=True)
    voice_duration = models.FloatField(null=True, blank=True)
    
    # Sentiment analysis
    sentiment_score = models.FloatField(null=True, blank=True)
    
    # For assistant messages: which agent/voice was used
    voice_id = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.message_type} message in conversation {self.conversation.id}"
    
    class Meta:
        ordering = ['created_at']

class VoiceProfile(models.Model):
    """Model to store voice profiles that can be used by the system"""
    
    CATEGORY_CHOICES = [
        ('calm', _('Calm')),
        ('cheerful', _('Cheerful')),
        ('empathetic', _('Empathetic')),
        ('motivational', _('Motivational')),
        ('soothing', _('Soothing')),
    ]
    
    name = models.CharField(max_length=100)
    voice_id = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_premium = models.BooleanField(default=False)
    
    # Voice characteristics
    gender = models.CharField(max_length=10)
    age_range = models.CharField(max_length=20)
    accent = models.CharField(max_length=50, blank=True)
    
    # Sample audio
    sample_audio = models.FileField(upload_to='voice_samples/', blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.category})"

class ConversationFeedback(models.Model):
    """Model to store user feedback on conversations"""
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback on conversation {self.conversation.id}: {self.rating}/5"
