#!/usr/bin/env python
"""
빠른 시작 스크립트 - 마음챙김 대화 프로젝트

이 스크립트는 '마음챙김 대화' 프로젝트를 빠르게 설정하고 실행할 수 있도록 도와줍니다.
"""

import os
import sys
import subprocess
import shutil
import platform
import random
import string
from pathlib import Path

def generate_secret_key(length=50):
    """Django SECRET_KEY 생성"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

def create_env_file():
    """환경 변수 설정 파일(.env) 생성"""
    if os.path.exists('.env'):
        print("이미 .env 파일이 존재합니다.")
        return
    
    env_example_path = '.env.example'
    if not os.path.exists(env_example_path):
        print("경고: .env.example 파일을 찾을 수 없습니다.")
        return
    
    # .env.example 파일 복사 및 수정
    with open(env_example_path, 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    # SECRET_KEY 생성 및 설정
    env_content = env_content.replace('your_secret_key_here', generate_secret_key())
    
    # .env 파일 저장
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(".env 파일이 생성되었습니다. 필요한 API 키를 설정해주세요.")

def setup_virtual_environment():
    """가상 환경 설정"""
    if os.path.exists('venv'):
        print("이미 가상 환경(venv)이 존재합니다.")
        return
    
    print("가상 환경을 생성하는 중...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("가상 환경이 성공적으로 생성되었습니다.")
    except subprocess.CalledProcessError:
        print("가상 환경 생성에 실패했습니다. Python 3.6+ 버전이 설치되어 있는지 확인하세요.")
        sys.exit(1)

def install_dependencies():
    """의존성 설치"""
    print("필요한 패키지를 설치하는 중...")
    
    # 운영 체제에 따른 가상 환경 활성화 명령어
    if platform.system() == 'Windows':
        pip_cmd = ['venv\\Scripts\\pip']
    else:
        pip_cmd = ['./venv/bin/pip']
    
    try:
        # pip 업그레이드
        subprocess.run([*pip_cmd, 'install', '--upgrade', 'pip'], check=True)
        
        # 의존성 설치
        subprocess.run([*pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        print("필요한 패키지가 성공적으로 설치되었습니다.")
    except subprocess.CalledProcessError:
        print("패키지 설치에 실패했습니다.")
        sys.exit(1)

def setup_database():
    """데이터베이스 설정"""
    print("데이터베이스를 설정하는 중...")
    
    # 운영 체제에 따른 가상 환경 활성화 명령어
    if platform.system() == 'Windows':
        python_cmd = ['venv\\Scripts\\python']
    else:
        python_cmd = ['./venv/bin/python']
    
    try:
        # 마이그레이션 생성 및 적용
        subprocess.run([*python_cmd, 'manage.py', 'makemigrations'], check=True)
        subprocess.run([*python_cmd, 'manage.py', 'migrate'], check=True)
        print("데이터베이스가 성공적으로 설정되었습니다.")
    except subprocess.CalledProcessError:
        print("데이터베이스 설정에 실패했습니다.")
        sys.exit(1)

def create_superuser():
    """관리자 계정 생성"""
    print("\n관리자 계정을 생성하시겠습니까? (y/n)")
    choice = input().lower()
    
    if choice != 'y':
        print("관리자 계정 생성을 건너뜁니다.")
        return
    
    # 운영 체제에 따른 가상 환경 활성화 명령어
    if platform.system() == 'Windows':
        python_cmd = ['venv\\Scripts\\python']
    else:
        python_cmd = ['./venv/bin/python']
    
    try:
        # createsuperuser 명령 실행
        subprocess.run([*python_cmd, 'manage.py', 'createsuperuser'], check=False)
    except subprocess.CalledProcessError:
        print("관리자 계정 생성에 실패했습니다.")

def create_voice_profiles():
    """기본 음성 프로필 생성"""
    print("기본 음성 프로필을 생성하는 중...")
    
    # 운영 체제에 따른 가상 환경 활성화 명령어
    if platform.system() == 'Windows':
        python_cmd = ['venv\\Scripts\\python']
    else:
        python_cmd = ['./venv/bin/python']
    
    try:
        # 커스텀 명령어 실행
        subprocess.run([*python_cmd, 'manage.py', 'create_voice_profiles'], check=True)
        print("기본 음성 프로필이 성공적으로 생성되었습니다.")
    except subprocess.CalledProcessError:
        print("음성 프로필 생성에 실패했습니다. 서버 실행 후 관리자 페이지에서 수동으로 추가해주세요.")

def run_server():
    """개발 서버 실행"""
    print("\n개발 서버를 시작하시겠습니까? (y/n)")
    choice = input().lower()
    
    if choice != 'y':
        print("서버 시작을 건너뜁니다.")
        return
    
    # 운영 체제에 따른 가상 환경 활성화 명령어
    if platform.system() == 'Windows':
        python_cmd = ['venv\\Scripts\\python']
    else:
        python_cmd = ['./venv/bin/python']
    
    print("\n개발 서버를 시작합니다...")
    try:
        # runserver 명령 실행
        subprocess.run([*python_cmd, 'manage.py', 'runserver'], check=True)
    except KeyboardInterrupt:
        print("\n서버가 중지되었습니다.")
    except subprocess.CalledProcessError:
        print("서버 실행에 실패했습니다.")

def create_required_directories():
    """필요한
    디렉토리 생성"""
    print("필요한 디렉토리를 생성하는 중...")
    
    # 생성할 디렉토리 목록
    directories = [
        'media',
        'media/profile_images',
        'media/voice_messages',
        'media/voice_samples',
        'media/backups',
        'static/css',
        'static/js',
        'static/img',
        'vectorstore',
    ]
    
    # 디렉토리 생성
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("필요한 디렉토리가 성공적으로 생성되었습니다.")

def main():
    """메인 함수"""
    print("=" * 60)
    print("마음챙김 대화 프로젝트 빠른 시작 스크립트")
    print("=" * 60)
    
    # 현재 디렉토리가 프로젝트 루트인지 확인
    if not os.path.exists('manage.py'):
        print("오류: 이 스크립트는 프로젝트 루트 디렉토리에서 실행해야 합니다.")
        print("manage.py 파일이 있는 디렉토리에서 실행해주세요.")
        sys.exit(1)
    
    # 필요한 디렉토리 생성
    create_required_directories()
    
    # 가상 환경 설정
    setup_virtual_environment()
    
    # .env 파일 생성
    create_env_file()
    
    # 의존성 설치
    install_dependencies()
    
    # 데이터베이스 설정
    setup_database()
    
    # 관리자 계정 생성
    create_superuser()
    
    # 기본 음성 프로필 생성
    create_voice_profiles()
    
    # 개발 서버 실행
    run_server()
    
    print("\n설정이 완료되었습니다!")
    print("""
다음 단계:
1. .env 파일을 열고 API 키를 설정하세요.
2. 가상 환경 활성화:
   - Windows: venv\\Scripts\\activate
   - macOS/Linux: source venv/bin/activate
3. 서버 실행: python manage.py runserver
4. 브라우저에서 http://127.0.0.1:8000/ 접속
    """)

if __name__ == "__main__":
    main()
