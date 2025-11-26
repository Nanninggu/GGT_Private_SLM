-- 세션 설명(description) 컬럼 추가
ALTER TABLE chat_sessions 
ADD COLUMN IF NOT EXISTS description TEXT DEFAULT NULL;

-- 설명 업데이트 함수 생성
CREATE OR REPLACE FUNCTION update_session_description(
    p_session_id VARCHAR(255),
    p_description TEXT,
    p_user_id VARCHAR(255) DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    -- 세션 존재 여부 확인
    IF EXISTS (SELECT 1 FROM chat_sessions WHERE session_id = p_session_id) THEN
        -- 기존 세션 업데이트
        UPDATE chat_sessions 
        SET 
            description = p_description,
            updated_at = CURRENT_TIMESTAMP,
            last_activity = CURRENT_TIMESTAMP,
            user_id = COALESCE(p_user_id, user_id)
        WHERE session_id = p_session_id;
    ELSE
        -- 새 세션 생성
        INSERT INTO chat_sessions (session_id, user_id, title, description, title_edited, created_at, updated_at, last_activity)
        VALUES (p_session_id, COALESCE(p_user_id, 'default'), '새 대화', p_description, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

