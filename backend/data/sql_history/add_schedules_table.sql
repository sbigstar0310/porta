-- Add schedule table for schedules
-- Created: 2025-09-30
-- PostgreSQL version

-- 스케줄 테이블 (스케줄 저장)
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    hour INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
    minute INTEGER NOT NULL CHECK (minute >= 0 AND minute <= 59),
    timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Seoul',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_schedule_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 인덱스 (조회 성능 위해)
CREATE INDEX idx_schedules_user_id ON public.schedules (user_id);
CREATE INDEX idx_schedules_enabled ON public.schedules (enabled);