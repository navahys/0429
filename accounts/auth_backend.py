from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from .file_auth import authenticate_user, find_user

User = get_user_model()

class FileAuthBackend(BaseBackend):
    """
    파일 기반 사용자 인증 백엔드
    DB 대신 JSON 파일에 사용자 데이터를 저장하고 인증하는 시스템
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        파일 기반 인증 시스템으로 사용자 인증
        
        Args:
            request: HTTP 요청 객체
            username: 사용자명 또는 이메일
            password: 비밀번호
            
        Returns:
            인증 성공 시 CustomUser 객체, 실패 시 None
        """
        if not username or not password:
            return None
            
        # 파일에서 사용자 인증
        file_user = authenticate_user(username, password)
        
        if not file_user:
            return None
            
        # 인증된 경우 Django User 객체 생성 또는 가져오기
        try:
            # 기존 사용자 찾기 시도
            django_user = User.objects.get(username=file_user['username'])
            
            # 파일 데이터로 사용자 정보 업데이트
            django_user.email = file_user['email']
            django_user.first_name = file_user['first_name']
            django_user.last_name = file_user['last_name']
            django_user.is_active = file_user['is_active']
            django_user.is_staff = file_user['is_staff']
            django_user.is_superuser = file_user['is_superuser']
            
            if 'last_login' in file_user and file_user['last_login']:
                django_user.last_login = file_user['last_login']
                
            django_user.save()
            return django_user
            
        except User.DoesNotExist:
            # 없는 경우 새로 생성 (비밀번호 설정 없이)
            django_user = User(
                username=file_user['username'],
                email=file_user['email'],
                first_name=file_user['first_name'],
                last_name=file_user['last_name'],
                is_active=file_user['is_active'],
                is_staff=file_user['is_staff'],
                is_superuser=file_user['is_superuser']
            )
            
            # 비밀번호 검증을 건너뛰기 위해 직접 설정
            django_user.set_password(None)
            django_user.save()
            
            # 기본 설정 적용
            django_user.preferred_voice = file_user['preferences'].get('preferred_voice', 'default')
            django_user.email_notifications = file_user['preferences'].get('email_notifications', True)
            django_user.daily_check_in_reminder = file_user['preferences'].get('daily_check_in_reminder', False)
            django_user.weekly_summary_enabled = file_user['preferences'].get('weekly_summary_enabled', True)
            django_user.save()
            
            return django_user
            
    def get_user(self, user_id):
        """
        사용자 ID로 사용자 가져오기
        
        Args:
            user_id: Django User ID
            
        Returns:
            User 객체 또는 None
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
