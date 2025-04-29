import json
import datetime
from typing import Dict, Any, List
from django.conf import settings
from django.core.mail import send_mail
from django.template import Template, Context
from django.db.models import Q, Avg
from django.utils import timezone

from accounts.models import CustomUser, MoodRecord
from conversations.models import Conversation, Message
from ..models import EmailTemplate, ScheduledEmail

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

def analyze_user_mood(user: CustomUser) -> Dict[str, Any]:
    """
    Analyze user's mood based on recent mood records and conversations
    
    Args:
        user: The user to analyze
        
    Returns:
        Dict containing mood analysis results
    """
    # Get recent mood records
    two_weeks_ago = timezone.now() - datetime.timedelta(days=14)
    recent_moods = MoodRecord.objects.filter(
        user=user, 
        recorded_at__gte=two_weeks_ago
    ).order_by('-recorded_at')
    
    # Get average sentiment from recent conversations
    recent_messages = Message.objects.filter(
        conversation__user=user,
        created_at__gte=two_weeks_ago,
        message_type='user',
        sentiment_score__isnull=False
    )
    
    avg_sentiment = recent_messages.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0
    
    # Count different mood categories
    mood_counts = {
        'very_bad': recent_moods.filter(mood='very_bad').count(),
        'bad': recent_moods.filter(mood='bad').count(),
        'neutral': recent_moods.filter(mood='neutral').count(),
        'good': recent_moods.filter(mood='good').count(),
        'very_good': recent_moods.filter(mood='very_good').count(),
    }
    
    # Calculate the most frequent mood
    most_frequent_mood = max(mood_counts.items(), key=lambda x: x[1])[0] if mood_counts else 'neutral'
    
    # Calculate overall mood score (from -1 to 1)
    total_records = sum(mood_counts.values())
    if total_records > 0:
        mood_score = (
            mood_counts['very_good'] * 1.0 + 
            mood_counts['good'] * 0.5 + 
            mood_counts['neutral'] * 0 + 
            mood_counts['bad'] * -0.5 + 
            mood_counts['very_bad'] * -1.0
        ) / total_records
    else:
        mood_score = 0
    
    # Determine trend (getting better, worse, or stable)
    if recent_moods.count() >= 3:
        # Get oldest and newest records for comparison
        oldest_records = list(recent_moods.reverse()[:3])
        newest_records = list(recent_moods[:3])
        
        # Convert mood strings to numeric values
        mood_values = {
            'very_bad': -1.0,
            'bad': -0.5,
            'neutral': 0,
            'good': 0.5,
            'very_good': 1.0
        }
        
        old_avg = sum(mood_values.get(r.mood, 0) for r in oldest_records) / len(oldest_records)
        new_avg = sum(mood_values.get(r.mood, 0) for r in newest_records) / len(newest_records)
        
        if new_avg - old_avg > 0.2:
            trend = "improving"
        elif old_avg - new_avg > 0.2:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "unknown"
    
    return {
        "mood_score": mood_score,
        "sentiment_score": avg_sentiment,
        "most_frequent_mood": most_frequent_mood,
        "mood_counts": mood_counts,
        "total_records": total_records,
        "trend": trend,
        "needs_comfort_mail": mood_score < -0.3 or avg_sentiment < -0.3
    }

def generate_comfort_email(user: CustomUser, analysis: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate a personalized comfort email for the user
    
    Args:
        user: The user to generate email for
        analysis: Optional mood analysis results
        
    Returns:
        Dict containing email subject and content
    """
    # If no analysis provided, generate one
    if analysis is None:
        analysis = analyze_user_mood(user)
    
    # Get recent conversations to extract topics
    recent_messages = Message.objects.filter(
        conversation__user=user,
        message_type='user'
    ).order_by('-created_at')[:20]
    
    recent_content = "\n".join([msg.content for msg in recent_messages])
    
    # Initialize the language model
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY
    )
    
    # Create prompt for comfort email
    if analysis["mood_score"] < -0.3:
        # For users who seem to be struggling
        email_prompt = PromptTemplate.from_template(
            """사용자를 위한 따뜻한 위로 이메일을 작성해주세요. 사용자는 최근에 부정적인 감정을 경험하고 있습니다.
            
            다음 정보를 참고하세요:
            - 사용자 이름: {user_name}
            - 감정 상태: {mood}
            - 감정 추세: {trend}
            
            다음은 사용자가 최근에 나눈 대화의 일부입니다:
            {recent_content}
            
            이메일 작성 지침:
            1. 따뜻하고 공감적인 인사로 시작하세요.
            2. 사용자의 감정을 인정하고 정상화하세요.
            3. 긍정적인 관점이나 작은 희망의 메시지를 포함하세요.
            4. 간단하고 실행 가능한 자기 관리 제안을 1-2개 포함하세요.
            5. 따뜻하고 지지적인 마무리로 끝내세요.
            6. 제목과 본문을 모두 작성하세요.
            7. 한국어로 작성하세요.
            
            응답 형식:
            제목: [이메일 제목]
            
            [이메일 본문]
            """
        )
    elif analysis["mood_score"] > 0.3:
        # For users who are doing well
        email_prompt = PromptTemplate.from_template(
            """사용자를 위한 긍정적인 격려 이메일을 작성해주세요. 사용자는 최근에 긍정적인 감정을 경험하고 있습니다.
            
            다음 정보를 참고하세요:
            - 사용자 이름: {user_name}
            - 감정 상태: {mood}
            - 감정 추세: {trend}
            
            다음은 사용자가 최근에 나눈 대화의 일부입니다:
            {recent_content}
            
            이메일 작성 지침:
            1. 축하와 격려의 인사로 시작하세요.
            2. 사용자의 긍정적인 상태를 인정하세요.
            3. 이 긍정적인 모멘텀을 유지하기 위한 제안을 포함하세요.
            4. 더 높은 목표를 위한 영감을 주는 메시지를 포함하세요.
            5. 따뜻하고 지지적인 마무리로 끝내세요.
            6. 제목과 본문을 모두 작성하세요.
            7. 한국어로 작성하세요.
            
            응답 형식:
            제목: [이메일 제목]
            
            [이메일 본문]
            """
        )
    else:
        # For users with neutral mood
        email_prompt = PromptTemplate.from_template(
            """사용자를 위한 지지적인 이메일을 작성해주세요. 사용자의 감정 상태는 중립적이거나 약간 변동이 있습니다.
            
            다음 정보를 참고하세요:
            - 사용자 이름: {user_name}
            - 감정 상태: {mood}
            - 감정 추세: {trend}
            
            다음은 사용자가 최근에 나눈 대화의 일부입니다:
            {recent_content}
            
            이메일 작성 지침:
            1. 친근하고 따뜻한 인사로 시작하세요.
            2. 사용자의 현재 상태를 인정하세요.
            3. 마음챙김과 자기 성찰에 관한 아이디어를 공유하세요.
            4. 일상에 작은 긍정적인 변화를 만들 수 있는 제안을 포함하세요.
            5. 따뜻하고 지지적인 마무리로 끝내세요.
            6. 제목과 본문을 모두 작성하세요.
            7. 한국어로 작성하세요.
            
            응답 형식:
            제목: [이메일 제목]
            
            [이메일 본문]
            """
        )
    
    # Make LLMChain
    email_chain = LLMChain(llm=llm, prompt=email_prompt)
    
    # Generate email
    email_result = email_chain.run(
        user_name=user.first_name or user.username,
        mood=analysis["most_frequent_mood"],
        trend=analysis["trend"],
        recent_content=recent_content[:1000]  # Limit content length
    )
    
    # Parse the result into subject and body
    try:
        lines = email_result.split('\n')
        subject = lines[0].replace('제목:', '').strip()
        body = '\n'.join(lines[2:])
    except Exception:
        # Fallback if parsing fails
        subject = "당신을 위한 위로의 메시지"
        body = email_result
    
    return {
        "subject": subject,
        "body": body
    }

def schedule_comfort_email(user: CustomUser, days_ahead: int = 1) -> ScheduledEmail:
    """
    Schedule a comfort email to be sent in the future
    
    Args:
        user: The user to schedule email for
        days_ahead: Number of days in the future to schedule
        
    Returns:
        Created ScheduledEmail object
    """
    # Generate analysis and email content
    analysis = analyze_user_mood(user)
    email = generate_comfort_email(user, analysis)
    
    # Calculate scheduled time
    scheduled_time = timezone.now() + datetime.timedelta(days=days_ahead)
    
    # Create scheduled email record
    scheduled_email = ScheduledEmail.objects.create(
        user=user,
        subject=email["subject"],
        content=email["body"],
        scheduled_at=scheduled_time,
        status='pending'
    )
    
    return scheduled_email

def send_scheduled_emails() -> Dict[str, int]:
    """
    Send all scheduled emails that are due
    
    Returns:
        Dict with counts of emails processed
    """
    now = timezone.now()
    pending_emails = ScheduledEmail.objects.filter(
        status='pending',
        scheduled_at__lte=now
    )
    
    results = {
        "total": pending_emails.count(),
        "sent": 0,
        "failed": 0
    }
    
    for email in pending_emails:
        try:
            # Send the email
            send_mail(
                subject=email.subject,
                message=email.content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email.user.email],
                fail_silently=False,
            )
            
            # Update email status
            email.status = 'sent'
            email.sent_at = timezone.now()
            email.save()
            
            results["sent"] += 1
            
        except Exception as e:
            # Log error and update status
            email.status = 'failed'
            email.errors = str(e)
            email.save()
            
            results["failed"] += 1
    
    return results

def check_users_needing_comfort() -> List[CustomUser]:
    """
    Identify users who might benefit from a comfort email
    
    Returns:
        List of users who might need comfort emails
    """
    # Get all active users with email notifications enabled
    users = CustomUser.objects.filter(
        is_active=True,
        email_notifications=True,
        email__isnull=False
    )
    
    users_needing_comfort = []
    
    for user in users:
        # Check if user already has a pending email
        has_pending = ScheduledEmail.objects.filter(
            user=user,
            status='pending'
        ).exists()
        
        if has_pending:
            continue
        
        # Analyze user mood
        analysis = analyze_user_mood(user)
        
        # If user needs comfort and doesn't have a recent email
        if analysis["needs_comfort_mail"]:
            # Check if we sent an email in the last week
            one_week_ago = timezone.now() - datetime.timedelta(days=7)
            recent_email = ScheduledEmail.objects.filter(
                user=user,
                status='sent',
                sent_at__gte=one_week_ago
            ).exists()
            
            if not recent_email:
                users_needing_comfort.append(user)
    
    return users_needing_comfort
