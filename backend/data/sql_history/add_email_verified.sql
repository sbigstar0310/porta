-- 이메일 인증 필드 추가
-- 실행 날짜: 2025-09-16
-- 목적: 이메일 인증 상태를 추적하여 사용자 경험 개선

-- users 테이블에 email_verified 필드 추가
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

-- 기존 사용자들의 기본값 설정 (기존 사용자는 인증된 것으로 간주)
UPDATE users SET email_verified = TRUE WHERE email_verified IS NULL OR email_verified = FALSE;

-- 인덱스 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified);
CREATE INDEX IF NOT EXISTS idx_users_uuid ON users(uuid);