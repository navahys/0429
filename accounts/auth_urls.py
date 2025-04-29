from django.urls import path
from .views import (
    login_view, register_view, logout_view, 
    UserProfileView, UserProfileUpdateView,
    password_change_view, password_reset_view, password_reset_confirm_view,
    password_reset_complete_view, email_verification_sent_view, email_verification_confirm_view,
    delete_account_view, update_voice_setting_view
)

urlpatterns = [
    # 로그인/로그아웃
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    
    # 이메일 인증
    path('email-verification-sent/', email_verification_sent_view, name='email_verification_sent'),
    path('verify-email/<str:uidb64>/<str:token>/', email_verification_confirm_view, name='email_verification_confirm'),
    
    # 비밀번호 관리
    path('password-change/', password_change_view, name='password_change'),
    path('password-reset/', password_reset_view, name='password_reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset-complete/', password_reset_complete_view, name='password_reset_complete'),
    
    # 프로필 관리
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/edit/', UserProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/delete/', delete_account_view, name='delete_account'),
    path('profile/update-voice-setting/', update_voice_setting_view, name='update_voice_setting'),
]
