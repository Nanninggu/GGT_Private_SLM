-- Update existing chat_sessions table with new columns
ALTER TABLE chat_sessions 
ADD COLUMN IF NOT EXISTS user_id VARCHAR(255) DEFAULT 'default',
ADD COLUMN IF NOT EXISTS title VARCHAR(500) DEFAULT '새 대화',
ADD COLUMN IF NOT EXISTS title_edited BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Create additional indexes
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON chat_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_is_active ON chat_sessions(is_active);

-- Create views
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

-- Create session statistics view
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

-- Create session title update function
CREATE OR REPLACE FUNCTION update_session_title(
    p_session_id VARCHAR(255),
    p_title VARCHAR(500),
    p_user_id VARCHAR(255) DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    -- Check if session exists
    IF EXISTS (SELECT 1 FROM chat_sessions WHERE session_id = p_session_id) THEN
        -- Update existing session
        UPDATE chat_sessions 
        SET 
            title = p_title,
            title_edited = TRUE,
            updated_at = CURRENT_TIMESTAMP,
            last_activity = CURRENT_TIMESTAMP,
            user_id = COALESCE(p_user_id, user_id)
        WHERE session_id = p_session_id;
    ELSE
        -- Create new session
        INSERT INTO chat_sessions (session_id, user_id, title, title_edited, created_at, updated_at, last_activity)
        VALUES (p_session_id, COALESCE(p_user_id, 'default'), p_title, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Create session deactivation function
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

-- Create message count update function
CREATE OR REPLACE FUNCTION update_session_message_count(
    p_session_id VARCHAR(255)
) RETURNS BOOLEAN AS $$
DECLARE
    msg_count INTEGER;
BEGIN
    -- Calculate actual message count from messages table
    SELECT COUNT(*) INTO msg_count 
    FROM chat_messages 
    WHERE session_id = p_session_id;
    
    -- Update session table
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
