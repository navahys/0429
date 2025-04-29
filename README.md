# 마음챙김 대화 (Mental Health Support)

정서적 지원과 도움이 필요한 사용자를 위한 음성 기반 대화 시스템입니다. 이 프로젝트는 AI 대화 에이전트와 음성 상호작용을 통해 사용자에게 정서적 지원을 제공합니다.

## 주요 기능

- 🗣️ **음성 기반 대화**: 네이버 Clova API와 OpenAI API를 활용한 자연스러운 음성 대화
- 🧠 **맞춤형 AI 상담**: LangChain과 LangGraph를 활용한 정서적 지원 대화
- 📊 **감정 상태 추적**: 대화 및 사용자 입력을 통한 감정 상태 분석
- 📧 **위로 이메일**: 사용자의 감정 상태에 따른 맞춤형 위로 메일 발송
- 🔄 **다양한 음성 선택**: 사용자의 선호도에 맞는 다양한 음성 프로필

## 기술 스택

- **백엔드**: Django, Django REST Framework, Channels (WebSockets)
- **프론트엔드**: HTML, CSS, JavaScript
- **AI**: LangChain, LangGraph, OpenAI API
- **음성 처리**: 네이버 Clova API (음성 합성 및 인식)
- **데이터베이스**: SQLite (개발), PostgreSQL (배포)
- **비동기 처리**: Django Channels, ASGI

## 설치 방법

1. 저장소 클론:
   ```bash
   git clone https://github.com/yourusername/mental-health-support.git
   cd mental-health-support
   ```

2. 가상 환경 생성 및 활성화:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```

4. 환경 변수 설정 (.env 파일 생성):
   ```
   DJANGO_SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # OpenAI API 키
   OPENAI_API_KEY=your_openai_api_key
   
   # 네이버 클라우드 API 키
   NAVER_CLIENT_ID=your_naver_client_id
   NAVER_CLIENT_SECRET=your_naver_client_secret
   NAVER_CLOVA_API_KEY=your_naver_clova_api_key
   
   # 이메일 설정
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_email_password
   ```

5. 데이터베이스 초기화:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. 관리자 계정 생성:
   ```bash
   python manage.py createsuperuser
   ```

7. 서버 실행:
   ```bash
   python manage.py runserver
   ```

## 프로젝트 구조

- `mental_health_project/`: 주 Django 프로젝트 디렉토리
- `core/`: 메인 페이지 및 공통 기능
- `accounts/`: 사용자 계정 및 감정 상태 관리
- `conversations/`: 대화 관리 및 음성 처리
- `agents/`: AI 에이전트 및 자동화 기능
- `templates/`: HTML 템플릿 파일들
- `static/`: 정적 파일 (CSS, JS, 이미지 등)
- `media/`: 사용자 업로드 파일 및 음성 파일

## API 엔드포인트

본 프로젝트는 다음과 같은 주요 API 엔드포인트를 제공합니다:

- `/api/conversations/`: 대화 세션 관리
- `/api/messages/`: 메시지 조회
- `/api/tts/`: 텍스트를 음성으로 변환
- `/api/stt/`: 음성을 텍스트로 변환
- `/api/agents/tasks/`: AI 에이전트 태스크 관리

## WebSocket 엔드포인트

실시간 음성 대화를 위한 WebSocket 엔드포인트:

- `ws/conversations/<conversation_id>/`: 실시간 음성 대화 처리

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`).
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 제출합니다.

## 라이선스

이 프로젝트는 MIT 라이선스에 따라 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 연락처

프로젝트 관리자 - your-email@example.com

프로젝트 링크: [https://github.com/yourusername/mental-health-support](https://github.com/yourusername/mental-health-support)
