from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.utils import timezone
import datetime

from accounts.models import MoodRecord
from conversations.models import Conversation, Message
from agents.models import ScheduledEmail

def index_view(request):
    """Main landing page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'core/index.html')

def about_view(request):
    """About page view"""
    return render(request, 'core/about.html')

def privacy_view(request):
    """Privacy policy view"""
    return render(request, 'core/privacy.html')

def terms_view(request):
    """Terms of service view"""
    return render(request, 'core/terms.html')

@login_required
def dashboard_view(request):
    """User dashboard view"""
    # Get recent conversations
    recent_conversations = Conversation.objects.filter(
        user=request.user
    ).order_by('-updated_at')[:5]
    
    # Get mood data for chart
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
    mood_records = MoodRecord.objects.filter(
        user=request.user,
        recorded_at__gte=thirty_days_ago
    ).order_by('recorded_at')
    
    # Prepare mood data for charts
    mood_data = {
        'labels': [],
        'values': []
    }
    
    for record in mood_records:
        mood_data['labels'].append(record.recorded_at.strftime('%Y-%m-%d'))
        
        # Convert mood to numeric value
        mood_values = {
            'very_bad': -2,
            'bad': -1,
            'neutral': 0,
            'good': 1,
            'very_good': 2
        }
        mood_data['values'].append(mood_values.get(record.mood, 0))
    
    # Get scheduled emails
    scheduled_emails = ScheduledEmail.objects.filter(
        user=request.user,
        status='pending'
    ).order_by('scheduled_at')
    
    # Get overall statistics
    stats = {
        'total_conversations': Conversation.objects.filter(user=request.user).count(),
        'total_messages': Message.objects.filter(conversation__user=request.user).count(),
        'avg_sentiment': Message.objects.filter(
            conversation__user=request.user,
            sentiment_score__isnull=False
        ).aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0
    }
    
    return render(request, 'core/dashboard.html', {
        'recent_conversations': recent_conversations,
        'mood_data': mood_data,
        'scheduled_emails': scheduled_emails,
        'stats': stats
    })

@login_required
def voice_settings_view(request):
    """Voice settings view"""
    from conversations.models import VoiceProfile
    
    # Get available voice profiles
    voice_profiles = VoiceProfile.objects.all()
    
    # Get user's current voice setting
    current_voice = request.user.preferred_voice
    
    return render(request, 'core/voice_settings.html', {
        'voice_profiles': voice_profiles,
        'current_voice': current_voice
    })

@login_required
def support_resources_view(request):
    """Mental health support resources view"""
    return render(request, 'core/support_resources.html')

def handler404(request, exception):
    """Custom 404 page"""
    return render(request, 'core/404.html', status=404)

def handler500(request):
    """Custom 500 page"""
    return render(request, 'core/500.html', status=500)
