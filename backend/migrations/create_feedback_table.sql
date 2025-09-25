-- 피드백 테이블 생성
CREATE TABLE IF NOT EXISTS feedback (
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

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_message_id ON feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);

-- 피드백 통계를 위한 뷰 생성
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

-- 피드백 타입별 통계 뷰
CREATE OR REPLACE VIEW feedback_type_stats AS
SELECT 
    feedback_type,
    COUNT(*) as count,
    AVG(CASE WHEN feedback_type = 'rating' THEN rating END) as avg_rating,
    COUNT(CASE WHEN is_positive = true THEN 1 END) as positive_count,
    COUNT(CASE WHEN is_positive = false THEN 1 END) as negative_count
FROM feedback 
GROUP BY feedback_type;
