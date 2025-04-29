from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import EmailTemplate, ScheduledEmail, AgentTask
from .serializers import EmailTemplateSerializer, ScheduledEmailSerializer, AgentTaskSerializer
from .services.comfort_mail_agent import (
    analyze_user_mood, generate_comfort_email, schedule_comfort_email,
    send_scheduled_emails, check_users_needing_comfort
)

# Web views
@login_required
def comfort_email_preview(request):
    """Preview a comfort email for the current user"""
    analysis = analyze_user_mood(request.user)
    email = generate_comfort_email(request.user, analysis)
    
    return render(request, 'agents/comfort_email_preview.html', {
        'email': email,
        'analysis': analysis
    })

@login_required
@require_POST
def send_comfort_email(request):
    """Manually send a comfort email to the current user"""
    try:
        # Schedule an email to be sent immediately
        scheduled_email = schedule_comfort_email(request.user, days_ahead=0)
        
        # Send it
        send_scheduled_emails()
        
        return JsonResponse({
            'success': True,
            'message': '위로 이메일이 성공적으로 전송되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'이메일 전송 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@login_required
def scheduled_emails_view(request):
    """View scheduled emails for the current user"""
    emails = ScheduledEmail.objects.filter(user=request.user).order_by('-scheduled_at')
    
    return render(request, 'agents/scheduled_emails.html', {
        'emails': emails
    })

@login_required
@require_POST
def cancel_scheduled_email(request, email_id):
    """Cancel a scheduled email"""
    email = get_object_or_404(ScheduledEmail, id=email_id, user=request.user)
    
    if email.status == 'pending':
        email.status = 'cancelled'
        email.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({
            'success': False,
            'message': '이미 처리된 이메일은 취소할 수 없습니다.'
        }, status=400)

# API ViewSets
class EmailTemplateViewSet(viewsets.ModelViewSet):
    """API endpoint for email templates"""
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [permissions.IsAdminUser]

class ScheduledEmailViewSet(viewsets.ModelViewSet):
    """API endpoint for scheduled emails"""
    serializer_class = ScheduledEmailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ScheduledEmail.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scheduled email"""
        email = self.get_object()
        
        if email.status == 'pending':
            email.status = 'cancelled'
            email.save()
            return Response({'status': 'email cancelled'})
        else:
            return Response({
                'error': '이미 처리된 이메일은 취소할 수 없습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

class AgentTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for agent tasks (read-only)"""
    serializer_class = AgentTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AgentTask.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def request_comfort_email(self, request):
        """Request a comfort email to be sent"""
        try:
            # Create a task
            task = AgentTask.objects.create(
                user=request.user,
                task_type='comfort_email',
                scheduled_at=timezone.now(),
                status='pending'
            )
            
            # Schedule the email
            email = schedule_comfort_email(request.user, days_ahead=0)
            
            # Save the result
            task.result = {'email_id': email.id}
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save()
            
            return Response({
                'task_id': task.id,
                'email_id': email.id,
                'status': 'scheduled'
            })
            
        except Exception as e:
            # Log the error
            if 'task' in locals():
                task.status = 'failed'
                task.errors = str(e)
                task.save()
            
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def analyze_mood(self, request):
        """Analyze the user's mood"""
        try:
            # Create a task
            task = AgentTask.objects.create(
                user=request.user,
                task_type='mood_analysis',
                scheduled_at=timezone.now(),
                status='in_progress'
            )
            
            # Do the analysis
            analysis = analyze_user_mood(request.user)
            
            # Save the result
            task.result = analysis
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save()
            
            return Response(analysis)
            
        except Exception as e:
            # Log the error
            if 'task' in locals():
                task.status = 'failed'
                task.errors = str(e)
                task.save()
            
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
