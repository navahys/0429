from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import CustomUser
from .forms import CustomUserCreationForm, UserProfileForm, CustomPasswordChangeForm, CustomPasswordResetForm, CustomSetPasswordForm

def login_view(request):
    """이메일 로그인 기능"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        # 이메일로 사용자 확인
        try:
            user = CustomUser.objects.get(email=email)
            username = user.username
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # 로그인 상태 유지 설정
                if not remember:
                    request.session.set_expiry(0)  # 브라우저 종료 시 세션 만료
                    
                # 이전 페이지로 리디렉션 또는 대시보드로 이동
                next_url = request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                messages.error(request, '비밀번호가 올바르지 않습니다.')
        except CustomUser.DoesNotExist:
            messages.error(request, '해당 이메일로 등록된 계정이 없습니다.')
            
    return render(request, 'accounts/login.html')

def register_view(request):
    """이메일 회원가입 기능"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # 사용자 생성 (비활성 상태로)
            user = form.save(commit=False)
            user.is_active = False
            user.email_notifications = request.POST.get('email_notifications') == 'on'
            user.save()
            
            # 이메일 인증 링크 발송
            current_site = get_current_site(request)
            mail_subject = '마음챙김 대화 - 이메일 주소 확인'
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            message = render_to_string('accounts/email_verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
            })
            
            send_mail(
                mail_subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False
            )
            
            return redirect('email_verification_sent')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def logout_view(request):
    """로그아웃 기능"""
    logout(request)
    messages.success(request, "성공적으로 로그아웃되었습니다.")
    return redirect('login')

def email_verification_sent_view(request):
    """이메일 인증 안내 페이지"""
    email = request.session.get('verification_email', '')
    return render(request, 'accounts/email_verification_sent.html', {'email': email})

def email_verification_confirm_view(request, uidb64, token):
    """이메일 인증 확인 기능"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user, token):
        # 사용자 계정 활성화
        user.is_active = True
        user.save()
        
        # 인증 성공 페이지 렌더링
        return render(request, 'accounts/email_verification_confirm.html', {'success': True})
    else:
        # 인증 실패 페이지 렌더링
        return render(request, 'accounts/email_verification_confirm.html', {'success': False})

@login_required
def password_change_view(request):
    """비밀번호 변경 기능"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # 세션 유지
            messages.success(request, '비밀번호가 성공적으로 변경되었습니다.')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(request.user)
        
    return render(request, 'accounts/password_change.html', {'form': form})

def password_reset_view(request):
    """비밀번호 재설정 요청 기능"""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                
                # 비밀번호 재설정 이메일 발송
                current_site = get_current_site(request)
                mail_subject = '마음챙김 대화 - 비밀번호 재설정'
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                
                html_message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': uid,
                    'token': token,
                })
                
                plain_message = render_to_string('accounts/password_reset_email_plain.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': uid,
                    'token': token,
                })
                
                email = EmailMultiAlternatives(
                    mail_subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email]
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
                
                messages.success(request, '비밀번호 재설정 링크가 이메일로 발송되었습니다.')
                return redirect('login')
            except CustomUser.DoesNotExist:
                # 사용자가 존재하지 않아도 동일한 메시지 표시 (보안상)
                messages.success(request, '비밀번호 재설정 링크가 이메일로 발송되었습니다.')
                return redirect('login')
    else:
        form = CustomPasswordResetForm()
        
    return render(request, 'accounts/password_reset.html', {'form': form})

def password_reset_confirm_view(request, uidb64, token):
    """비밀번호 재설정 확인 기능"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
        
        # 토큰 유효성 검사
        if not default_token_generator.check_token(user, token):
            return render(request, 'accounts/password_reset_confirm.html', {
                'validlink': False
            })
            
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
        return render(request, 'accounts/password_reset_confirm.html', {
            'validlink': False
        })
        
    if request.method == 'POST':
        form = CustomSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '비밀번호가 성공적으로 변경되었습니다. 이제 로그인할 수 있습니다.')
            return redirect('password_reset_complete')
    else:
        form = CustomSetPasswordForm(user)
        
    return render(request, 'accounts/password_reset_confirm.html', {
        'validlink': True,
        'form': form
    })

def password_reset_complete_view(request):
    """비밀번호 재설정 완료 페이지"""
    return render(request, 'accounts/password_reset_complete.html')

@method_decorator(login_required, name='dispatch')
class UserProfileView(DetailView):
    """사용자 프로필 페이지"""
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 음성 프로필 추가
        from conversations.models import VoiceProfile
        context['voice_profiles'] = VoiceProfile.objects.all()
        
        return context

@method_decorator(login_required, name='dispatch')
class UserProfileUpdateView(UpdateView):
    """사용자 프로필 수정 페이지"""
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, "프로필이 성공적으로 업데이트되었습니다.")
        return super().form_valid(form)

@login_required
@require_POST
def update_voice_setting_view(request):
    """음성 설정 업데이트 기능"""
    voice_id = request.POST.get('preferred_voice')
    if voice_id:
        try:
            user = request.user
            user.preferred_voice = voice_id
            user.save()
            messages.success(request, "음성 설정이 업데이트되었습니다.")
            return redirect('profile')
        except Exception as e:
            messages.error(request, f"음성 설정 업데이트 중 오류가 발생했습니다: {str(e)}")
    else:
        messages.error(request, "유효하지 않은 음성 ID입니다.")
    
    return redirect('profile')

@login_required
@require_POST
def delete_account_view(request):
    """계정 삭제 기능"""
    password = request.POST.get('password')
    user = request.user
    
    # 비밀번호 확인
    if user.check_password(password):
        try:
            # 사용자 데이터 삭제
            user.delete()
            messages.success(request, "계정이 성공적으로 삭제되었습니다.")
            return redirect('index')
        except Exception as e:
            messages.error(request, f"계정 삭제 중 오류가 발생했습니다: {str(e)}")
    else:
        messages.error(request, "비밀번호가 올바르지 않습니다.")
    
    return redirect('profile')
