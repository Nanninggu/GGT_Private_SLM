-- chat_sessions 테이블 스키마 수정
-- 누락된 컬럼 추가

-- user_id 컬럼 추가
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS user_id VARCHAR(255) DEFAULT 'default';

-- title 컬럼 추가
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS title VARCHAR(500) DEFAULT '새 대화';

-- title_edited 컬럼 추가
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS title_edited BOOLEAN DEFAULT FALSE;

-- last_activity 컬럼 추가
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- message_count 컬럼 추가
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;

-- is_active 컬럼 추가
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 인덱스 생성 (존재하지 않는 경우)
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON chat_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_is_active ON chat_sessions(is_active);

