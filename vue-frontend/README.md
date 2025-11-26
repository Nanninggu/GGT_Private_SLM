# Vue Frontend - SLM Chat

Vue.js 3 + Element Plus + Tailwind CSS로 구성된 모던한 챗봇 프론트엔드입니다.

## 기술 스택

- **Vue 3** - Composition API
- **TypeScript** - 타입 안정성
- **Vite** - 빠른 개발 서버
- **Element Plus** - UI 컴포넌트 라이브러리
- **Tailwind CSS** - 유틸리티 우선 CSS 프레임워크
- **Vue Router** - 라우팅
- **Pinia** - 상태 관리
- **Axios** - HTTP 클라이언트

## 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

## 환경 변수

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```
VITE_API_BASE_URL=http://localhost:9502
```

## 프로젝트 구조

```
src/
├── components/      # 재사용 가능한 컴포넌트
├── layouts/         # 레이아웃 컴포넌트
├── router/          # 라우터 설정
├── services/        # API 서비스 레이어
├── stores/          # Pinia 스토어
├── views/           # 페이지 컴포넌트
├── App.vue          # 루트 컴포넌트
└── main.ts          # 진입점
```

## 주요 기능

- ✅ 사용자 인증 (로그인/회원가입)
- ✅ 실시간 채팅 (스트리밍 지원)
- ✅ 세션 관리
- ✅ 문서 업로드 및 관리
- ✅ 컬렉션 관리
- ✅ 웹 검색 및 자동 저장
- ✅ RAG (Retrieval-Augmented Generation) 지원
- ✅ 다크 모드 지원

## 백엔드 연동

백엔드 서버가 `http://localhost:9502`에서 실행 중이어야 합니다.

## 개발 가이드

### 새로운 페이지 추가

1. `src/views/`에 새 Vue 컴포넌트 생성
2. `src/router/index.ts`에 라우트 추가

### API 서비스 추가

1. `src/services/`에 새 서비스 파일 생성
2. `src/services/api.ts`의 ApiService 클래스 활용

### 상태 관리

Pinia 스토어는 `src/stores/`에 위치합니다.

## 라이선스

MIT
