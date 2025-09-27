-- Add unique constraints to prevent duplicate sessions
-- This migration adds unique constraints to ensure session_id uniqueness

-- Add unique constraint on session_id in chat_sessions table
ALTER TABLE chat_sessions ADD CONSTRAINT unique_session_id UNIQUE (session_id);

-- Add unique constraint on user_id + session_id combination for additional safety
-- This ensures no duplicate sessions per user
ALTER TABLE chat_sessions ADD CONSTRAINT unique_user_session UNIQUE (user_id, session_id);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_created ON chat_sessions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);

-- Add comment
COMMENT ON CONSTRAINT unique_session_id ON chat_sessions IS 'Ensures each session_id is unique across all users';
COMMENT ON CONSTRAINT unique_user_session ON chat_sessions IS 'Ensures no duplicate sessions per user';
