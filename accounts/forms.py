from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, MoodRecord

class CustomUserCreationForm(UserCreationForm):
    """회원가입 폼"""
    email = forms.EmailField(
        label=_('이메일'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap 클래스 추가
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # 필드 라벨 변경
        self.fields['username'].label = _('사용자 이름')
        self.fields['first_name'].label = _('이름')
        self.fields['last_name'].label = _('성')
        self.fields['password1'].label = _('비밀번호')
        self.fields['password2'].label = _('비밀번호 확인')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(_('이미 사용 중인 이메일 주소입니다.'))
        return email

class CustomUserChangeForm(UserChangeForm):
    """관리자용 사용자 수정 폼"""
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name')

class UserProfileForm(forms.ModelForm):
    """사용자 프로필 수정 폼"""
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'email', 'phone_number', 
            'birth_date', 'profile_image', 'email_notifications',
            'daily_check_in_reminder', 'weekly_summary_enabled'
        )
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap 클래스 추가
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # 현재 사용자의 이메일과 다른 경우만 중복 검사
        if email != self.instance.email and CustomUser.objects.filter(email=email).exists():
            raise ValidationError(_('이미 사용 중인 이메일 주소입니다.'))
        return email

class MoodRecordForm(forms.ModelForm):
    """감정 기록 폼"""
    class Meta:
        model = MoodRecord
        fields = ('mood', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': '오늘 어떤 감정을 느끼셨나요? (선택 사항)'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap 클래스 추가
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # 필드 라벨 변경
        self.fields['mood'].label = _('감정 상태')
        self.fields['notes'].label = _('메모')

class CustomPasswordChangeForm(PasswordChangeForm):
    """비밀번호 변경 폼"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap 클래스 추가
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # 필드 라벨 변경
        self.fields['old_password'].label = _('현재 비밀번호')
        self.fields['new_password1'].label = _('새 비밀번호')
        self.fields['new_password2'].label = _('새 비밀번호 확인')

class CustomPasswordResetForm(PasswordResetForm):
    """비밀번호 재설정 요청 폼"""
    email = forms.EmailField(
        label=_('이메일'),
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        # 이메일이 존재하는지 확인은 보안상 view에서 처리 (존재하지 않아도 동일한 메시지 표시)
        return email

class CustomSetPasswordForm(SetPasswordForm):
    """비밀번호 재설정 폼 (새 비밀번호 설정)"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap 클래스 추가
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # 필드 라벨 변경
        self.fields['new_password1'].label = _('새 비밀번호')
        self.fields['new_password2'].label = _('새 비밀번호 확인')
