import os
import json
import hashlib
import uuid
from datetime import datetime
from django.conf import settings

# 사용자 데이터 파일 경로
USER_DATA_FILE = os.path.join(settings.BASE_DIR, 'users.json')

# 기본 사용자 데이터 구조 초기화
def init_user_data_file():
    """사용자 데이터 파일이 없으면 생성"""
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({"users": []}, f, ensure_ascii=False)

# 비밀번호 해싱
def hash_password(password, salt=None):
    """비밀번호를 안전하게 해싱"""
    if salt is None:
        salt = uuid.uuid4().hex
    
    # 비밀번호와 솔트를 합쳐서 해싱
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    return {'hash': hashed_password, 'salt': salt}

# 모든 사용자 불러오기
def load_users():
    """사용자 데이터 파일에서 모든 사용자 정보 불러오기"""
    init_user_data_file()
    
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('users', [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []

# 사용자 데이터 저장
def save_users(users):
    """사용자 데이터를 파일에 저장"""
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({"users": users}, f, ensure_ascii=False, indent=4)

# 사용자 검색
def find_user(field, value):
    """지정된 필드와 값으로 사용자 찾기"""
    users = load_users()
    for user in users:
        if user.get(field) == value:
            return user
    return None

# 사용자 등록
def register_user(username, email, password, **extra_fields):
    """새 사용자 등록"""
    users = load_users()
    
    # 사용자명 또는 이메일 중복 검사
    if find_user('username', username) or find_user('email', email):
        return False, "이미 존재하는 사용자명 또는 이메일입니다."
    
    # 비밀번호 해싱
    password_data = hash_password(password)
    
    # 기본 사용자 데이터
    user = {
        'id': str(uuid.uuid4()),
        'username': username,
        'email': email,
        'password_hash': password_data['hash'],
        'password_salt': password_data['salt'],
        'first_name': extra_fields.get('first_name', ''),
        'last_name': extra_fields.get('last_name', ''),
        'is_active': extra_fields.get('is_active', True),
        'is_staff': extra_fields.get('is_staff', False),
        'is_superuser': extra_fields.get('is_superuser', False),
        'date_joined': datetime.now().isoformat(),
        'last_login': None,
        'preferences': {
            'email_notifications': extra_fields.get('email_notifications', True),
            'daily_check_in_reminder': extra_fields.get('daily_check_in_reminder', False),
            'weekly_summary_enabled': extra_fields.get('weekly_summary_enabled', True),
            'preferred_voice': extra_fields.get('preferred_voice', 'default'),
        }
    }
    
    # 사용자 추가
    users.append(user)
    save_users(users)
    
    return True, user

# 사용자 인증
def authenticate_user(username_or_email, password):
    """사용자명 또는 이메일과 비밀번호로 인증"""
    # 사용자명 또는 이메일로 사용자 찾기
    user = find_user('username', username_or_email)
    if not user:
        user = find_user('email', username_or_email)
    
    if not user:
        return None
    
    # 비밀번호 검증
    password_data = hash_password(password, user['password_salt'])
    if password_data['hash'] == user['password_hash']:
        # 마지막 로그인 시간 업데이트
        update_user_field(user['id'], 'last_login', datetime.now().isoformat())
        return user
    
    return None

# 사용자 정보 업데이트
def update_user_field(user_id, field, value):
    """사용자의 특정 필드 업데이트"""
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            if '.' in field:  # 중첩 필드 (e.g., 'preferences.email_notifications')
                parts = field.split('.')
                target = user
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = value
            else:
                user[field] = value
            save_users(users)
            return True
    return False

# 관리자 계정 생성
def create_superuser(username, email, password):
    """관리자 계정 생성"""
    success, result = register_user(
        username=username,
        email=email,
        password=password,
        is_staff=True,
        is_superuser=True
    )
    
    return success, result

# 이메일 인증 토큰 생성
def create_verification_token(user_id):
    """이메일 인증용 토큰 생성"""
    token = uuid.uuid4().hex
    users = load_users()
    
    for user in users:
        if user['id'] == user_id:
            user['verification_token'] = token
            user['token_created_at'] = datetime.now().isoformat()
            save_users(users)
            return token
    
    return None

# 이메일 인증 확인
def verify_email(user_id, token):
    """이메일 인증 토큰 확인"""
    user = find_user('id', user_id)
    if not user:
        return False
    
    if user.get('verification_token') == token:
        update_user_field(user_id, 'is_active', True)
        update_user_field(user_id, 'verification_token', None)
        return True
    
    return False

# 비밀번호 재설정 토큰 생성
def create_password_reset_token(email):
    """비밀번호 재설정 토큰 생성"""
    user = find_user('email', email)
    if not user:
        return None
    
    token = uuid.uuid4().hex
    users = load_users()
    
    for u in users:
        if u['id'] == user['id']:
            u['reset_token'] = token
            u['reset_token_created_at'] = datetime.now().isoformat()
            save_users(users)
            return {'token': token, 'user_id': user['id']}
    
    return None

# 비밀번호 재설정
def reset_password(user_id, token, new_password):
    """비밀번호 재설정 토큰 확인 및 비밀번호 변경"""
    user = find_user('id', user_id)
    if not user or user.get('reset_token') != token:
        return False
    
    # 비밀번호 해싱
    password_data = hash_password(new_password)
    users = load_users()
    
    for u in users:
        if u['id'] == user_id:
            u['password_hash'] = password_data['hash']
            u['password_salt'] = password_data['salt']
            u['reset_token'] = None
            save_users(users)
            return True
    
    return False

# 시스템 초기화 시 사용자 데이터 파일 생성
init_user_data_file()
