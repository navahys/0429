from django.urls import path, include
from rest_framework.routers import DefaultRouter

# API ViewSets
from .views import UserViewSet, MoodRecordViewSet, record_mood_view, mood_history_view

# 파일 기반 인증 뷰
from .file_views import (
    file_login_view, file_register_view, 
    file_email_verification_confirm_view, 
    file_password_reset_view, file_password_reset_confirm_view,
    file_create_superuser
)

# API router
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'moods', MoodRecordViewSet)

urlpatterns = [
    # 로그인/로그아웃 (파일 기반)
    path('login/', file_login_view, name='login'),
    path('logout/', file_login_view, name='logout'),  # 로그아웃은 Django 기본 뷰 사용
    path('register/', file_register_view, name='register'),
    
    # 이메일 인증 (파일 기반)
    path('email-verification-sent/', lambda request: render(request, 'accounts/email_verification_sent.html'), 
         name='email_verification_sent'),
    path('verify-email/<str:uidb64>/<str:token>/', file_email_verification_confirm_view, 
         name='email_verification_confirm'),
    
    # 비밀번호 관리 (파일 기반)
    path('password-reset/', file_password_reset_view, name='password_reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', file_password_reset_confirm_view, 
         name='password_reset_confirm'),
    path('password-reset-complete/', lambda request: render(request, 'accounts/password_reset_complete.html'), 
         name='password_reset_complete'),
    
    # 관리자 계정 생성 (개발용)
    path('create-superuser/', file_create_superuser, name='create_superuser'),
    
    # 감정 기록 관련
    path('mood/record/', record_mood_view, name='record_mood'),
    path('mood/history/', mood_history_view, name='mood_history'),
    
    # API URLs
    path('api/', include(router.urls)),
]

# 필요한 렌더 함수 임포트
from django.shortcuts import render
