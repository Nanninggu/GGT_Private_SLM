# 데이터베이스 설정 가이드 (Database Setup Guide)

이 문서는 GGT Private SLM 애플리케이션의 데이터베이스 설정 및 구조에 대한 완전한 가이드입니다.

## 📋 목차
- [데이터베이스 개요](#데이터베이스-개요)
- [PostgreSQL + pgvector 설정](#postgresql--pgvector-설정)
- [테이블 구조](#테이블-구조)
- [인덱스 및 성능 최적화](#인덱스-및-성능-최적화)
- [마이그레이션 스크립트](#마이그레이션-스크립트)
- [데이터베이스 초기화](#데이터베이스-초기화)
- [환경 변수 설정](#환경-변수-설정)
- [데이터베이스 스키마 검증](#데이터베이스-스키마-검증)
- [문제 해결](#문제-해결)

## 🗄️ 데이터베이스 개요

### 사용 기술 스택
- **데이터베이스**: PostgreSQL 15+
- **벡터 확장**: pgvector 0.3.0+
- **ORM**: SQLAlchemy 2.0+
- **벡터 검색**: LangChain + PGVector
- **임베딩**: Ollama (mxbai-embed-large)

### 연결 정보
```sql
-- 기본 연결 정보
Host: 127.0.0.1
Port: 5433
Database: postgres
Username: postgres
Password: test1234
```

## 🐘 PostgreSQL + pgvector 설정

### 1. PostgreSQL 설치
```bash
# macOS (Homebrew)
brew install postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql-15 postgresql-contrib-15

# CentOS/RHEL
sudo yum install postgresql15-server postgresql15-contrib
```

### 2. pgvector 확장 설치
```bash
# macOS
brew install pgvector

# Ubuntu/Debian
sudo apt-get install postgresql-15-pgvector

# 또는 소스에서 빌드
git clone --branch v0.3.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### 3. 데이터베이스 생성 및 확장 활성화
```sql
-- 데이터베이스 생성
CREATE DATABASE postgres;

-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 확장 확인
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## 📊 테이블 구조

### 1. 채팅 세션 테이블 (`chat_sessions`)
```sql
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    title_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 제약조건
    CONSTRAINT unique_session_id UNIQUE (session_id),
    CONSTRAINT unique_user_session UNIQUE (user_id, session_id)
);
```

### 2. 피드백 테이블 (`feedback`)
```sql
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    message_id VARCHAR(255) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL CHECK (feedback_type IN ('rating', 'thumbs_up', 'thumbs_down', 'comment')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    is_positive BOOLEAN,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 문서 벡터 테이블 (`documents`)
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1024),
    collection_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. 사용자 테이블 (`users`)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### 5. 채팅 메시지 테이블 (`chat_messages`)
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);
```

### 6. LangChain 컬렉션 테이블 (`langchain_pg_collection`)
```sql
-- LangChain에서 자동 생성되는 테이블
CREATE TABLE langchain_pg_collection (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    cmetadata JSONB,
    user_id VARCHAR(255)  -- 사용자별 컬렉션 격리를 위한 컬럼
);
```

### 7. LangChain 임베딩 테이블 (`langchain_pg_embedding`)
```sql
-- LangChain에서 자동 생성되는 테이블
CREATE TABLE langchain_pg_embedding (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE CASCADE,
    embedding vector(1024),
    document TEXT,
    cmetadata JSONB,
    custom_id VARCHAR
);
```

## 🚀 인덱스 및 성능 최적화

### 1. 채팅 세션 인덱스
```sql
-- 기본 인덱스
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX idx_chat_sessions_last_activity ON chat_sessions(last_activity);
CREATE INDEX idx_chat_sessions_is_active ON chat_sessions(is_active);

-- 복합 인덱스
CREATE INDEX idx_chat_sessions_user_created ON chat_sessions(user_id, created_at DESC);
```

### 2. 사용자 테이블 인덱스
```sql
CREATE INDEX users_username_idx ON users (username);
CREATE INDEX users_email_idx ON users (email);
CREATE INDEX users_role_idx ON users (role);
```

### 3. 채팅 메시지 인덱스
```sql
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_role ON chat_messages(role);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
```

### 4. 피드백 인덱스
```sql
CREATE INDEX idx_feedback_user_id ON feedback(user_id);
CREATE INDEX idx_feedback_session_id ON feedback(session_id);
CREATE INDEX idx_feedback_message_id ON feedback(message_id);
CREATE INDEX idx_feedback_type ON feedback(feedback_type);
CREATE INDEX idx_feedback_created_at ON feedback(created_at);
```

### 5. 벡터 검색 인덱스 (HNSW)
```sql
-- 문서 임베딩 HNSW 인덱스 (최적화된 설정)
CREATE INDEX documents_embedding_idx 
ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 12, ef_construction = 100);

-- 컬렉션 이름 인덱스
CREATE INDEX documents_collection_name_idx ON documents (collection_name);

-- LangChain 임베딩 인덱스
CREATE INDEX langchain_pg_embedding_embedding_idx 
ON langchain_pg_embedding USING hnsw (embedding vector_cosine_ops)
WITH (m = 12, ef_construction = 100);

-- LangChain 컬렉션 인덱스
CREATE INDEX idx_langchain_pg_collection_user_id ON langchain_pg_collection (user_id);
```

### 6. 성능 최적화 인덱스
```sql
-- JSONB 메타데이터 GIN 인덱스 (빠른 필터링)
CREATE INDEX documents_metadata_gin_idx ON documents USING gin (metadata);

-- 컬렉션 + 임베딩 복합 인덱스
CREATE INDEX documents_collection_embedding_idx 
ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 12, ef_construction = 100);

-- 시간 기반 쿼리 인덱스
CREATE INDEX documents_created_at_idx ON documents (created_at DESC);

-- 문서 크기 필터링 인덱스
CREATE INDEX documents_content_length_idx ON documents (length(content));

-- 활성 문서 부분 인덱스
CREATE INDEX documents_active_collection_idx 
ON documents (collection_name, created_at DESC) 
WHERE collection_name IS NOT NULL;
```

### 7. 성능 최적화 설정
```sql
-- PostgreSQL 벡터 검색 최적화
SET random_page_cost = 1.1;  -- SSD 최적화
SET effective_cache_size = '4GB';  -- 캐시 크기
SET shared_buffers = '256MB';  -- 공유 버퍼
SET work_mem = '64MB';  -- 작업 메모리
```

## 📋 마이그레이션 스크립트

### 마이그레이션 실행 순서
```bash
# 1. 기본 테이블 생성
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -f backend/migrations/create_chat_sessions_table.sql

# 2. 피드백 테이블 생성
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -f backend/migrations/create_feedback_table.sql

# 3. 테이블 업데이트
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -f backend/migrations/update_chat_sessions_table.sql

# 4. 유니크 제약조건 추가
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -f backend/migrations/add_unique_constraints.sql

# 5. 사용자 ID 컬럼 추가
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -f backend/migrations/add_user_id_to_collections.sql

# 6. 공유 컬렉션 마이그레이션
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -f backend/migrations/migrate_shared_collections.sql
```

### 자동 마이그레이션 (권장)
애플리케이션 시작 시 자동으로 마이그레이션이 실행됩니다:
```bash
# Backend 시작 (자동 마이그레이션 포함)
cd backend
python main.py
```

### 수동 마이그레이션 실행
```bash
# 데이터베이스 서비스 초기화 스크립트 실행
cd backend
python -c "
import asyncio
from services.database_service import db_service
asyncio.run(db_service.initialize())
"
```

## 🔧 데이터베이스 초기화

### 1. 자동 초기화 (권장)
애플리케이션 시작 시 자동으로 테이블이 생성되고 마이그레이션이 실행됩니다:

```bash
# Backend 시작 (자동 초기화 + 마이그레이션)
cd backend
python main.py
```

### 2. 수동 초기화
```bash
# 데이터베이스 서비스 초기화 스크립트 실행
cd backend
python -c "
import asyncio
from services.database_service import db_service
asyncio.run(db_service.initialize())
"
```

### 3. 완전한 데이터베이스 재구축
```bash
# 기존 데이터베이스 삭제 후 재생성
psql -h 127.0.0.1 -p 5433 -U postgres -c "DROP DATABASE IF EXISTS postgres;"
psql -h 127.0.0.1 -p 5433 -U postgres -c "CREATE DATABASE postgres;"
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 애플리케이션 재시작으로 테이블 자동 생성
cd backend
python main.py
```

## ⚙️ 환경 변수 설정

### `.env` 파일 생성
```bash
# backend/.env 파일 생성
cat > backend/.env << EOF
# 데이터베이스 설정
DATABASE_URL=postgresql://postgres:test1234@127.0.0.1:5433/postgres
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=test1234

# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large:latest

# JWT 설정
JWT_SECRET_KEY=your-secret-key-change-in-production-2024

# Google Search API (선택사항)
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-cse-id
EOF
```

### 환경 변수 설명
| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 연결 URL | `postgresql://postgres:test1234@127.0.0.1:5433/postgres` |
| `DATABASE_USERNAME` | 데이터베이스 사용자명 | `postgres` |
| `DATABASE_PASSWORD` | 데이터베이스 비밀번호 | `test1234` |
| `OLLAMA_BASE_URL` | Ollama 서버 URL | `http://localhost:11434` |
| `OLLAMA_EMBEDDING_MODEL` | 임베딩 모델명 | `mxbai-embed-large:latest` |
| `JWT_SECRET_KEY` | JWT 토큰 암호화 키 | `your-secret-key-change-in-production-2024` |

## 🔍 뷰 및 함수

### 1. 사용자 활성 세션 뷰
```sql
CREATE OR REPLACE VIEW user_active_sessions AS
SELECT 
    session_id,
    user_id,
    title,
    title_edited,
    created_at,
    updated_at,
    last_activity,
    message_count,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY last_activity DESC) as activity_rank
FROM chat_sessions 
WHERE is_active = TRUE
ORDER BY last_activity DESC;
```

### 2. 세션 통계 뷰
```sql
CREATE OR REPLACE VIEW session_stats AS
SELECT 
    user_id,
    COUNT(*) as total_sessions,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_sessions,
    COUNT(CASE WHEN title_edited = TRUE THEN 1 END) as edited_sessions,
    SUM(message_count) as total_messages,
    MAX(last_activity) as last_session_activity,
    AVG(message_count) as avg_messages_per_session
FROM chat_sessions 
GROUP BY user_id;
```

### 3. 피드백 통계 뷰
```sql
CREATE OR REPLACE VIEW feedback_stats AS
SELECT 
    user_id,
    COUNT(*) as total_feedback,
    COUNT(CASE WHEN feedback_type = 'rating' THEN 1 END) as rating_count,
    COUNT(CASE WHEN feedback_type = 'thumbs_up' THEN 1 END) as thumbs_up_count,
    COUNT(CASE WHEN feedback_type = 'thumbs_down' THEN 1 END) as thumbs_down_count,
    AVG(CASE WHEN feedback_type = 'rating' THEN rating END) as average_rating,
    MAX(created_at) as last_feedback_date
FROM feedback 
GROUP BY user_id;
```

### 4. 유틸리티 함수들
```sql
-- 세션 제목 업데이트 함수
CREATE OR REPLACE FUNCTION update_session_title(
    p_session_id VARCHAR(255),
    p_title VARCHAR(500),
    p_user_id VARCHAR(255) DEFAULT NULL
) RETURNS BOOLEAN;

-- 세션 비활성화 함수
CREATE OR REPLACE FUNCTION deactivate_session(
    p_session_id VARCHAR(255)
) RETURNS BOOLEAN;

-- 메시지 수 업데이트 함수
CREATE OR REPLACE FUNCTION update_session_message_count(
    p_session_id VARCHAR(255)
) RETURNS BOOLEAN;
```

## 🚨 주의사항

### 1. 보안 설정
- 프로덕션 환경에서는 기본 비밀번호를 반드시 변경하세요
- JWT 시크릿 키를 안전한 값으로 변경하세요
- 데이터베이스 접근 권한을 적절히 제한하세요

### 2. 성능 최적화
- 벡터 인덱스는 대용량 데이터에서 최적의 성능을 발휘합니다
- 정기적으로 `VACUUM ANALYZE`를 실행하여 성능을 유지하세요
- 메모리 설정을 시스템 사양에 맞게 조정하세요

### 3. 백업 및 복구
```bash
# 데이터베이스 백업
pg_dump -h 127.0.0.1 -p 5433 -U postgres postgres > backup_$(date +%Y%m%d_%H%M%S).sql

# 데이터베이스 복구
psql -h 127.0.0.1 -p 5433 -U postgres postgres < backup_20241201_120000.sql
```

## 🔍 데이터베이스 스키마 검증

### 테이블 존재 확인
```sql
-- 모든 테이블 목록 확인
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 특정 테이블 스키마 확인
\d chat_sessions
\d feedback
\d users
\d chat_messages
\d documents
\d langchain_pg_collection
\d langchain_pg_embedding
```

### 인덱스 확인
```sql
-- 모든 인덱스 목록 확인
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 벡터 인덱스 확인
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE indexdef LIKE '%hnsw%' 
   OR indexdef LIKE '%vector%';
```

### 확장 프로그램 확인
```sql
-- pgvector 확장 확인
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 확장 프로그램 목록
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

### 테이블 크기 및 통계
```sql
-- 테이블 크기 확인
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 테이블 행 수 확인
SELECT 
    'chat_sessions' as table_name, COUNT(*) as row_count FROM chat_sessions
UNION ALL
SELECT 'feedback', COUNT(*) FROM feedback
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'chat_messages', COUNT(*) FROM chat_messages
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'langchain_pg_collection', COUNT(*) FROM langchain_pg_collection
UNION ALL
SELECT 'langchain_pg_embedding', COUNT(*) FROM langchain_pg_embedding;
```

## 📞 문제 해결

### 일반적인 문제들
1. **pgvector 확장 오류**: PostgreSQL 버전과 pgvector 버전 호환성 확인
2. **연결 오류**: 방화벽 설정 및 포트 확인
3. **성능 문제**: 인덱스 생성 및 PostgreSQL 설정 확인
4. **메모리 부족**: `shared_buffers` 및 `work_mem` 설정 조정
5. **테이블 누락**: 마이그레이션 스크립트 실행 확인
6. **인덱스 누락**: 성능 최적화 인덱스 생성 확인

### 로그 확인
```bash
# PostgreSQL 로그 확인
tail -f /var/log/postgresql/postgresql-15-main.log

# 애플리케이션 로그 확인
tail -f backend/logs/app.log
```

### 데이터베이스 연결 테스트
```bash
# PostgreSQL 연결 테스트
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -c "SELECT version();"

# pgvector 확장 테스트
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres -c "SELECT vector_dims('[1,2,3]'::vector);"
```

---

이 가이드를 따라하면 다른 PC에서도 동일한 데이터베이스 환경을 구축할 수 있습니다. 추가 질문이나 문제가 있으면 개발팀에 문의하세요.
