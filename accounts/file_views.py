from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from .file_auth import (
    register_user, authenticate_user, find_user, update_user_field,
    create_verification_token, verify_email, 
    create_password_reset_token, reset_password
)

User = get_user_model()

def file_login_view(request):
    """파일 기반 로그인 뷰"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        # 커스텀 인증
        user_data = authenticate_user(email, password)
        
        if user_data:
            # 이메일 인증 확인
            if not user_data.get('is_active', False):
                messages.error(request, "계정이 아직 활성화되지 않았습니다. 이메일을 확인해주세요.")
                return redirect('login')
            
            # Django 로그인을 위한 사용자 가져오기
            try:
                django_user = User.objects.get(username=user_data['username'])
                
                # 로그인 처리
                login(request, django_user, backend='accounts.auth_backend.FileAuthBackend')
                
                # 로그인 상태 유지 설정
                if not remember:
                    request.session.set_expiry(0)  # 브라우저 종료 시 세션 만료
                
                # 리디렉트
                next_url = request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
                
            except User.DoesNotExist:
                messages.error(request, "사용자 계정에 문제가 발생했습니다. 관리자에게 문의하세요.")
        else:
            messages.error(request, "이메일 또는 비밀번호가 올바르지 않습니다.")
    
    return render(request, 'accounts/login.html')

def file_register_view(request):
    """파일 기반 회원가입 뷰"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email_notifications = request.POST.get('email_notifications') == 'on'
        
        # 입력 검증
        errors = []
        if not username:
            errors.append("사용자 이름을 입력해주세요.")
        if not email:
            errors.append("이메일을 입력해주세요.")
        if not password1:
            errors.append("비밀번호를 입력해주세요.")
        if password1 != password2:
            errors.append("비밀번호가 일치하지 않습니다.")
        
        # 사용자명/이메일 중복 확인
        if find_user('username', username):
            errors.append("이미 사용 중인 사용자 이름입니다.")
        if find_user('email', email):
            errors.append("이미 사용 중인 이메일 주소입니다.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'accounts/register.html')
        
        # 사용자 등록 (비활성 상태로)
        success, result = register_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
            email_notifications=email_notifications
        )
        
        if success:
            # 이메일 인증 토큰 생성
            token = create_verification_token(result['id'])
            
            # 인증 이메일 발송
            current_site = get_current_site(request)
            mail_subject = '마음챙김 대화 - 이메일 주소 확인'
            
            message = render_to_string('accounts/email_verification_email.html', {
                'user': result,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(result['id'])),
                'token': token,
            })
            
            try:
                send_mail(
                    mail_subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False
                )
                
                # 세션에 이메일 저장
                request.session['verification_email'] = email
                
                return redirect('email_verification_sent')
            except Exception as e:
                # 이메일 전송 실패 시 콘솔에 출력 (개발용)
                print(f"이메일 전송 실패: {e}")
                messages.warning(request, "인증 메일을 발송하는데 문제가 발생했습니다. 관리자에게 문의하세요.")
                
                # 개발 환경에서는 인증 없이 활성화 (테스트용)
                if settings.DEBUG:
                    update_user_field(result['id'], 'is_active', True)
                    messages.success(request, "개발 모드: 계정이 자동으로 활성화되었습니다.")
                    return redirect('login')
                
                return redirect('register')
        else:
            messages.error(request, result)  # 오류 메시지
    
    return render(request, 'accounts/register.html')

def file_email_verification_confirm_view(request, uidb64, token):
    """이메일 인증 확인 뷰"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        success = verify_email(uid, token)
        
        if success:
            # Django 사용자 데이터도 업데이트
            user_data = find_user('id', uid)
            if user_data:
                try:
                    django_user = User.objects.get(username=user_data['username'])
                    django_user.is_active = True
                    django_user.save()
                except User.DoesNotExist:
                    pass  # 로그인 시 생성될 것임
            
            return render(request, 'accounts/email_verification_confirm.html', {'success': True})
        else:
            return render(request, 'accounts/email_verification_confirm.html', {'success': False})
    except Exception:
        return render(request, 'accounts/email_verification_confirm.html', {'success': False})

def file_password_reset_view(request):
    """비밀번호 재설정 요청 뷰"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # 비밀번호 재설정 토큰 생성
        result = create_password_reset_token(email)
        
        # 이메일 존재 여부와 상관없이 동일한 메시지 표시 (보안상)
        messages.success(request, "비밀번호 재설정 링크가 이메일로 발송되었습니다.")
        
        # 이메일이 존재하는 경우에만 메일 발송
        if result:
            # 인증 이메일 발송
            current_site = get_current_site(request)
            mail_subject = '마음챙김 대화 - 비밀번호 재설정'
            
            message = render_to_string('accounts/password_reset_email_plain.html', {
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(result['user_id'])),
                'token': result['token'],
            })
            
            html_message = render_to_string('accounts/password_reset_email.html', {
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(result['user_id'])),
                'token': result['token'],
            })
            
            try:
                send_mail(
                    mail_subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=html_message,
                    fail_silently=False
                )
            except Exception as e:
                # 이메일 전송 실패 시 콘솔에 출력 (개발용)
                print(f"비밀번호 재설정 메일 전송 실패: {e}")
        
        return redirect('login')
        
    return render(request, 'accounts/password_reset.html')

def file_password_reset_confirm_view(request, uidb64, token):
    """비밀번호 재설정 확인 뷰"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user_data = find_user('id', uid)
        
        if not user_data or user_data.get('reset_token') != token:
            return render(request, 'accounts/password_reset_confirm.html', {'validlink': False})
        
        if request.method == 'POST':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if not new_password1 or not new_password2:
                messages.error(request, "새 비밀번호를 입력해주세요.")
                return render(request, 'accounts/password_reset_confirm.html', {'validlink': True})
                
            if new_password1 != new_password2:
                messages.error(request, "비밀번호가 일치하지 않습니다.")
                return render(request, 'accounts/password_reset_confirm.html', {'validlink': True})
            
            # 비밀번호 재설정
            success = reset_password(uid, token, new_password1)
            
            if success:
                messages.success(request, "비밀번호가 성공적으로 변경되었습니다. 이제 로그인할 수 있습니다.")
                return redirect('password_reset_complete')
            else:
                messages.error(request, "비밀번호 재설정에 실패했습니다.")
        
        return render(request, 'accounts/password_reset_confirm.html', {'validlink': True})
    except Exception as e:
        print(f"비밀번호 재설정 확인 오류: {e}")
        return render(request, 'accounts/password_reset_confirm.html', {'validlink': False})

def file_create_superuser(request):
    """관리자 계정 생성 페이지 (개발용)"""
    if not settings.DEBUG:
        return redirect('index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not username or not email or not password:
            messages.error(request, "모든 필드를 입력해주세요.")
            return render(request, 'accounts/create_superuser.html')
        
        from .file_auth import create_superuser
        success, result = create_superuser(username, email, password)
        
        if success:
            messages.success(request, "관리자 계정이 생성되었습니다.")
            return redirect('login')
        else:
            messages.error(request, result)
    
    return render(request, 'accounts/create_superuser.html')
