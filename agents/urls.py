from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API router
router = DefaultRouter()
router.register(r'email-templates', views.EmailTemplateViewSet)
router.register(r'scheduled-emails', views.ScheduledEmailViewSet, basename='scheduled-email')
router.register(r'tasks', views.AgentTaskViewSet, basename='agent-task')

urlpatterns = [
    # Web views
    path('comfort-email/preview/', views.comfort_email_preview, name='comfort_email_preview'),
    path('comfort-email/send/', views.send_comfort_email, name='send_comfort_email'),
    path('scheduled-emails/', views.scheduled_emails_view, name='scheduled_emails'),
    path('scheduled-emails/<int:email_id>/cancel/', views.cancel_scheduled_email, name='cancel_scheduled_email'),
    
    # API routes
    path('api/', include(router.urls)),
]
