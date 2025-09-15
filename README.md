# SLM Pattern 챗봇 프로젝트 🚀

Spring Boot에서 Python으로 마이그레이션된 RAG(Retrieval-Augmented Generation) 기반 챗봇 프로젝트입니다. 
벡터 데이터베이스, Ollama LLM, Google Search API를 통합한 고성능 AI 챗봇 시스템입니다.

## 🏗️ 프로젝트 구조

### 백엔드 (Spring Boot → Python 마이그레이션)
```
backend/
├── config/              # 설정 관리 (Spring Boot properties 변환)
│   └── settings.py      # 통합 설정 파일
├── controllers/         # API 컨트롤러 (프레젠테이션 계층)
├── services/            # 비즈니스 로직 (서비스 계층)
│   ├── database_service.py    # PostgreSQL + pgvector
│   ├── vector_service.py      # 벡터 검색 서비스
│   ├── ollama_service.py      # Ollama LLM 통합
│   ├── rag_service.py         # RAG 서비스
│   └── search_service.py      # Google Search API
├── repositories/        # 데이터 접근 (데이터 계층)
├── models/              # 데이터 모델
├── utils/               # 유틸리티 함수
├── main.py              # FastAPI 애플리케이션 진입점
├── test_configuration.py # 설정 테스트 스크립트
└── env.example          # 환경 변수 예제
```

### 프론트엔드 (MVC 패턴)
```
frontend/streamlit/
├── controllers/     # 뷰 컨트롤러
├── components/      # UI 컴포넌트 (뷰)
├── services/        # API 서비스
├── pages/           # 페이지 구성
├── utils/           # 유틸리티 함수
└── main.py          # Streamlit 애플리케이션 진입점
```

## 🚀 빠른 시작

### 1. 사전 요구사항
- Python 3.8+
- PostgreSQL 12+ (pgvector 확장 포함)
- Ollama (로컬 LLM 서버)
- Google Custom Search API 키 (선택사항)

### 2. 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate     # Windows
```

### 3. 데이터베이스 설정
```bash
# PostgreSQL에 pgvector 확장 설치
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 데이터베이스 생성
createdb -U postgres sllm_pattern
```

### 4. Ollama 설정
```bash
# Ollama 설치 (macOS)
brew install ollama

# Ollama 서버 시작
ollama serve

# 모델 다운로드 (새 터미널)
ollama pull llama2
ollama pull mxbai-embed-large
```

### 5. 환경 변수 설정
```bash
# 환경 변수 파일 생성
cp backend/env.example backend/.env

# .env 파일 편집하여 실제 값으로 업데이트
# - DATABASE_URL: PostgreSQL 연결 정보
# - GOOGLE_SEARCH_API_KEY: Google Search API 키
# - GOOGLE_SEARCH_ENGINE_ID: Google Search Engine ID
```

### 6. 백엔드 실행
```bash
# 백엔드 서버 시작 (자동 설정 테스트 포함)
./start_backend.sh
```

### 7. 프론트엔드 실행 (새 터미널)
```bash
# 프론트엔드 앱 시작
./start_frontend.sh
```

## 📋 주요 기능

- **RAG (Retrieval-Augmented Generation)**: 벡터 데이터베이스 기반 지식 검색
- **벡터 검색**: pgvector를 활용한 고성능 유사도 검색
- **Ollama 통합**: 로컬 LLM 서버 연동
- **Google Search API**: 실시간 웹 검색 기능
- **Deep Search**: 향상된 검색 결과 처리
- **문서 관리**: 지식 베이스 문서 추가/삭제/검색
- **세션 관리**: 채팅 기록 저장 및 관리
- **PDF 내보내기**: 채팅 대화를 PDF로 저장하는 기능
  - 전체 채팅 기록 PDF
  - 요약 보고서 PDF
  - 개별 메시지 PDF
- **RESTful API**: FastAPI 기반 백엔드 API
- **직관적 UI**: Streamlit 기반 사용자 인터페이스

## 🔧 기술 스택

### 백엔드
- **FastAPI**: 고성능 웹 프레임워크
- **PostgreSQL + pgvector**: 벡터 데이터베이스
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **Ollama**: 로컬 LLM 서버
- **httpx**: 비동기 HTTP 클라이언트
- **Pydantic**: 데이터 검증 및 직렬화

### 프론트엔드
- **Streamlit**: 웹 애플리케이션 프레임워크
- **Requests**: HTTP 클라이언트
- **ReportLab**: PDF 생성 라이브러리
- **WeasyPrint**: HTML to PDF 변환

### AI/ML
- **Ollama**: 로컬 LLM 서버
- **mxbai-embed-large**: 임베딩 모델
- **RAG**: 검색 증강 생성

## 📁 상세 아키텍처

### 백엔드 계층 구조
1. **프레젠테이션 계층**: Controllers - HTTP 요청/응답 처리
2. **서비스 계층**: Services - 비즈니스 로직 및 AI 모델 통합
3. **데이터 계층**: Repositories - 데이터 저장 및 검색

### 프론트엔드 MVC 패턴
1. **Model**: API 서비스를 통한 데이터 관리
2. **View**: Streamlit 컴포넌트 기반 UI
3. **Controller**: 사용자 입력 처리 및 상태 관리

## ⚙️ 설정

### Exaone 모델 설정
`backend/config/settings.py`에서 모델 경로 및 설정을 수정할 수 있습니다:

```python
MODEL_PATH = "./models/exaone3.5-2.4"  # 모델 경로
MAX_TOKENS = 2048                       # 최대 토큰 수
TEMPERATURE = 0.7                       # 생성 온도
```

### API 설정
- 백엔드 서버: `http://localhost:8000`
- Streamlit 앱: `http://localhost:8501`

## 📝 API 엔드포인트

- `POST /api/chat/session`: 새 채팅 세션 생성
- `POST /api/chat/message`: 메시지 전송
- `GET /api/chat/history/{session_id}`: 채팅 기록 조회
- `GET /api/chat/sessions`: 모든 세션 목록
- `DELETE /api/chat/session/{session_id}`: 세션 삭제

## 📄 PDF 내보내기 기능

HAI Portal은 채팅 대화를 PDF로 저장하는 다양한 옵션을 제공합니다:

### 1. 전체 채팅 기록 PDF
- 모든 메시지를 시간순으로 정렬
- 사용자와 AI 메시지를 구분하여 표시
- 메타데이터 포함 (신뢰도 점수, 참조 문서 등)
- 세션 정보 및 생성 일시 포함

### 2. 요약 보고서 PDF
- 채팅 통계 (총 메시지 수, 사용자/AI 메시지 수)
- 주요 토픽 키워드 추출
- 최근 메시지 미리보기
- 세션 정보 요약

### 3. 개별 메시지 PDF
- 특정 메시지만을 PDF로 저장
- 메타데이터 및 컨텍스트 정보 포함
- 사용자 메시지와 AI 응답 모두 지원

### 사용 방법
1. **사이드바에서 PDF 내보내기**: 전체 대화 또는 요약 보고서 생성
2. **개별 메시지 PDF**: 각 메시지 옆의 "📄 PDF" 버튼 클릭
3. **메인 화면에서**: "📄 전체 대화 PDF로 저장" 버튼 사용

### PDF 특징
- 한국어 텍스트 지원
- 깔끔한 레이아웃과 색상 구분
- 메타데이터 및 참조 문서 정보 포함
- 자동 파일명 생성 (세션 ID 및 타임스탬프 포함)

## 🔍 트러블슈팅

1. **백엔드 연결 실패**: 백엔드 서버가 실행 중인지 확인
2. **모델 로딩 실패**: 모델 경로 및 권한 확인
3. **의존성 오류**: requirements.txt 재설치

## 📊 개발 가이드

프로젝트 확장 시 다음 구조를 따라주세요:

- 새로운 API: `controllers` → `services` → `repositories` 순서로 구현
- 새로운 UI: `components` → `controllers` → `services` 순서로 구현
- 설정 변경: `config/settings.py` 수정
- 데이터 모델: `models/` 디렉토리에 추가
