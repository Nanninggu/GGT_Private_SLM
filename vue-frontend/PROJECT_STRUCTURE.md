# Vue Frontend 프로젝트 구조

## 📁 디렉토리 구조

```
vue-frontend/
├── src/
│   ├── components/          # 재사용 가능한 컴포넌트 (현재 비어있음)
│   ├── layouts/             # 레이아웃 컴포넌트
│   │   └── MainLayout.vue   # 메인 레이아웃 (사이드바 + 메인 컨텐츠)
│   ├── router/              # 라우터 설정
│   │   └── index.ts         # 라우트 정의 및 인증 가드
│   ├── services/            # API 서비스 레이어
│   │   ├── api.ts           # Axios 인스턴스 및 기본 설정
│   │   ├── auth.service.ts  # 인증 관련 API
│   │   ├── chat.service.ts  # 채팅 관련 API
│   │   ├── collection.service.ts  # 컬렉션 관련 API
│   │   ├── document.service.ts   # 문서 관련 API
│   │   └── web-search.service.ts # 웹 검색 관련 API
│   ├── stores/              # Pinia 스토어
│   │   ├── auth.ts          # 인증 상태 관리
│   │   └── chat.ts           # 채팅 상태 관리
│   ├── views/               # 페이지 컴포넌트
│   │   ├── Login.vue        # 로그인 페이지
│   │   ├── Register.vue     # 회원가입 페이지
│   │   ├── Chat.vue         # 채팅 메인 페이지
│   │   ├── Sessions.vue     # 세션 관리 페이지
│   │   ├── Documents.vue    # 문서 관리 페이지
│   │   ├── Collections.vue   # 컬렉션 관리 페이지
│   │   └── WebSearch.vue     # 웹 검색 페이지
│   ├── App.vue              # 루트 컴포넌트
│   ├── main.ts              # 애플리케이션 진입점
│   ├── style.css            # 전역 스타일 (Tailwind + shadcn 변수)
│   └── vite-env.d.ts        # TypeScript 타입 정의
├── public/                  # 정적 파일
├── index.html              # HTML 템플릿
├── package.json            # 의존성 및 스크립트
├── tsconfig.json           # TypeScript 설정
├── vite.config.ts          # Vite 설정
├── tailwind.config.js      # Tailwind CSS 설정
└── postcss.config.js       # PostCSS 설정
```

## 🎨 디자인 시스템

### Element Plus
- UI 컴포넌트 라이브러리로 사용
- 아이콘: `@element-plus/icons-vue`
- 폼 요소, 테이블, 카드 등 모든 UI 컴포넌트

### Tailwind CSS + shadcn 스타일
- shadcn의 CSS 변수 시스템 적용
- 다크 모드 지원
- 일관된 색상 팔레트

## 🔄 데이터 흐름

1. **사용자 액션** → Vue 컴포넌트
2. **컴포넌트** → Pinia Store (상태 관리)
3. **Store** → Service Layer (API 호출)
4. **Service** → Axios (HTTP 요청)
5. **백엔드 API** → 응답
6. **응답** → Store 업데이트
7. **Store** → 컴포넌트 리렌더링

## 🚀 주요 기능

### 인증 시스템
- JWT 기반 인증
- 자동 토큰 갱신
- 로그인/회원가입
- 라우트 가드

### 채팅 시스템
- 실시간 메시지 전송
- SSE 스트리밍 지원
- 세션 관리
- 메시지 히스토리
- RAG 모드 선택
- 모델 타입 선택 (fast/quality/complex)

### 문서 관리
- 파일 업로드 (단일/다중)
- 문서 목록 조회
- 문서 삭제
- 컬렉션별 관리

### 컬렉션 관리
- 컬렉션 생성/삭제
- 컬렉션 전환
- 개인/공유 컬렉션 구분

### 웹 검색
- DuckDuckGo/Google 검색
- 검색 결과 표시
- 자동 컬렉션 저장

## 📝 개발 가이드

### 새 페이지 추가
1. `src/views/`에 Vue 컴포넌트 생성
2. `src/router/index.ts`에 라우트 추가
3. 필요시 `src/layouts/MainLayout.vue`의 메뉴에 추가

### 새 API 서비스 추가
1. `src/services/`에 새 서비스 파일 생성
2. `apiService` 인스턴스 사용
3. 필요시 Pinia Store 생성

### 스타일 커스터마이징
- `src/style.css`에서 CSS 변수 수정
- `tailwind.config.js`에서 테마 확장

## 🔧 환경 설정

`.env` 파일:
```
VITE_API_BASE_URL=http://localhost:9502
```

## 📦 빌드 및 배포

```bash
# 개발 서버
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

