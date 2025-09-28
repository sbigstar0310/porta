-- Add reports table for multi-agent analysis reports
-- Created: 2025-09-16
-- PostgreSQL version

-- 보고서 테이블 (multi-agent 분석 보고서 저장)
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    report_md TEXT NOT NULL,
    language VARCHAR(2) NOT NULL DEFAULT 'ko',
    CONSTRAINT fk_reports_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 보고서 테이블 인덱스 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_reports_user_id 
    ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at 
    ON reports(created_at);