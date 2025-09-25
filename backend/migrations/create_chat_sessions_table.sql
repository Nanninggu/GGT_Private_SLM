-- 채팅 세션 관리 테이블 생성
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    title_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON chat_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_is_active ON chat_sessions(is_active);

-- 사용자별 활성 세션 조회를 위한 뷰
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

-- 세션 통계를 위한 뷰
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

-- 세션 제목 업데이트 함수
CREATE OR REPLACE FUNCTION update_session_title(
    p_session_id VARCHAR(255),
    p_title VARCHAR(500),
    p_user_id VARCHAR(255) DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    -- 세션 존재 여부 확인
    IF NOT EXISTS (SELECT 1 FROM chat_sessions WHERE session_id = p_session_id) THEN
        -- 새 세션 생성
        INSERT INTO chat_sessions (session_id, user_id, title, title_edited, created_at, updated_at, last_activity)
        VALUES (p_session_id, COALESCE(p_user_id, 'default'), p_title, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
    ELSE
        -- 기존 세션 업데이트
        UPDATE chat_sessions 
        SET 
            title = p_title,
            title_edited = TRUE,
            updated_at = CURRENT_TIMESTAMP,
            last_activity = CURRENT_TIMESTAMP
        WHERE session_id = p_session_id;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- 세션 비활성화 함수
CREATE OR REPLACE FUNCTION deactivate_session(
    p_session_id VARCHAR(255)
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE chat_sessions 
    SET 
        is_active = FALSE,
        updated_at = CURRENT_TIMESTAMP
    WHERE session_id = p_session_id;
    
    RETURN FOUND;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- 메시지 수 업데이트 함수
CREATE OR REPLACE FUNCTION update_session_message_count(
    p_session_id VARCHAR(255)
) RETURNS BOOLEAN AS $$
DECLARE
    msg_count INTEGER;
BEGIN
    -- 실제 메시지 수 계산 (messages 테이블에서)
    SELECT COUNT(*) INTO msg_count 
    FROM messages 
    WHERE session_id = p_session_id;
    
    -- 세션 테이블 업데이트
    UPDATE chat_sessions 
    SET 
        message_count = msg_count,
        last_activity = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE session_id = p_session_id;
    
    RETURN FOUND;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;
