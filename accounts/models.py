from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    
    # Additional fields for the user profile
    phone_number = models.CharField(_("Phone Number"), max_length=15, blank=True)
    birth_date = models.DateField(_("Birth Date"), null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    
    # Mental health related fields
    mood_tracking_enabled = models.BooleanField(default=True)
    preferred_voice = models.CharField(max_length=50, default='default')
    
    # User preferences
    email_notifications = models.BooleanField(default=True)
    daily_check_in_reminder = models.BooleanField(default=False)
    weekly_summary_enabled = models.BooleanField(default=True)
    
    # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username

class MoodRecord(models.Model):
    """Model to track user's mood over time"""
    
    MOOD_CHOICES = [
        ('very_bad', _('Very Bad')),
        ('bad', _('Bad')),
        ('neutral', _('Neutral')),
        ('good', _('Good')),
        ('very_good', _('Very Good')),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mood_records')
    mood = models.CharField(max_length=10, choices=MOOD_CHOICES)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s mood: {self.mood} on {self.recorded_at.strftime('%Y-%m-%d')}"
    
    class Meta:
        ordering = ['-recorded_at']
