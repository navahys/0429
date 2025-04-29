from django.core.management.base import BaseCommand, CommandError
from accounts.file_auth import create_superuser, find_user

class Command(BaseCommand):
    help = '파일 기반 인증을 위한 관리자 사용자 생성'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='관리자 사용자명')
        parser.add_argument('--email', required=True, help='관리자 이메일')
        parser.add_argument('--password', required=True, help='관리자 비밀번호')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        # 사용자명 중복 확인
        if find_user('username', username):
            raise CommandError(f"사용자명 '{username}'은(는) 이미 사용 중입니다.")
        
        # 이메일 중복 확인
        if find_user('email', email):
            raise CommandError(f"이메일 '{email}'은(는) 이미 사용 중입니다.")
        
        # 관리자 계정 생성
        success, result = create_superuser(username, email, password)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f"관리자 계정 '{username}'이(가) 생성되었습니다."))
        else:
            raise CommandError(f"관리자 계정 생성 실패: {result}")
