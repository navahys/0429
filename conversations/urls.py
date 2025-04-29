from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API router
router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'voice-profiles', views.VoiceProfileViewSet, basename='voice-profile')
router.register(r'feedback', views.ConversationFeedbackViewSet, basename='feedback')

urlpatterns = [
    # Web views
    path('conversations/', views.conversation_list_view, name='conversation_list'),
    path('conversations/<int:conversation_id>/', views.conversation_detail_view, name='conversation_detail'),
    path('conversations/new/', views.new_conversation_view, name='new_conversation'),
    
    # API routes
    path('', include(router.urls)),
    path('tts/', views.TextToSpeechAPIView.as_view(), name='text-to-speech'),
    path('stt/', views.SpeechToTextAPIView.as_view(), name='speech-to-text'),
]
