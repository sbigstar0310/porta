-- 확장
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- users -----------------------------------------------------------------------
-- public.users.uuid 는 auth.users.id(UUID)와 매핑된다.
CREATE TABLE IF NOT EXISTS public.users (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email          VARCHAR(255) UNIQUE,
    uuid           UUID NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login     TIMESTAMPTZ NOT NULL DEFAULT now(),
    timezone       VARCHAR(50)  NOT NULL DEFAULT 'UTC',
    language       VARCHAR(2)   NOT NULL DEFAULT 'en'
);
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON public.users(email_verified);
CREATE INDEX IF NOT EXISTS idx_users_uuid          ON public.users(uuid);

-- portfolios ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.portfolios (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       BIGINT      NOT NULL,
    base_currency VARCHAR(3)  NOT NULL DEFAULT 'USD',
    cash          NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_portfolio_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE,
    CONSTRAINT uq_portfolios_user UNIQUE (user_id)
);

-- transactions ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.transactions (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    portfolio_id     BIGINT      NOT NULL,
    ticker           VARCHAR(10) NOT NULL,
    transaction_type VARCHAR(4)  NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
    shares           NUMERIC(18,2) NOT NULL,
    price            NUMERIC(18,2) NOT NULL,
    transaction_date DATE        NOT NULL,
    fee              NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    currency         VARCHAR(3)  NOT NULL DEFAULT 'USD',
    exchange         VARCHAR(50) NOT NULL DEFAULT '',
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_transaction_portfolio FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_ticker ON public.transactions(portfolio_id, ticker);
CREATE INDEX IF NOT EXISTS idx_transactions_date             ON public.transactions(transaction_date);

-- positions (집계된 현재 보유 포지션) ----------------------------------------
CREATE TABLE IF NOT EXISTS public.positions (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    portfolio_id  BIGINT      NOT NULL,
    ticker        VARCHAR(10) NOT NULL,
    total_shares  NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    avg_buy_price NUMERIC(18,2) NOT NULL,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_position_portfolio FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE,
    CONSTRAINT uq_positions_portfolio_ticker UNIQUE (portfolio_id, ticker)
);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON public.positions(portfolio_id);

-- reports -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.reports (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    report_md  TEXT NOT NULL,
    language   VARCHAR(2) NOT NULL DEFAULT 'ko',
    CONSTRAINT fk_reports_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_reports_user_id    ON public.reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON public.reports(created_at);

-- schedules -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.schedules (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    hour       INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
    minute     INTEGER NOT NULL CHECK (minute >= 0 AND minute <= 59),
    timezone   VARCHAR(50) NOT NULL DEFAULT 'Asia/Seoul',
    enabled    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_schedule_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_schedules_user_id ON public.schedules (user_id);
CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON public.schedules (enabled);

-- recommendations -------------------------------------------------------------
-- 추천 트랙레코드: 매 런의 매매 추천을 기록하고, 이후 런이 실현 수익률로 채점한다.
-- 채점 완료 여부는 각 창의 return_* 컬럼 null 여부로 판단한다 (창 경과 후 채점).
CREATE TABLE IF NOT EXISTS public.recommendations (
    id                   SERIAL PRIMARY KEY,
    user_id              INTEGER NOT NULL,
    report_id            INTEGER,
    ticker               VARCHAR(10) NOT NULL,
    action               VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL', 'HOLD', 'TRIM')),
    total_score          NUMERIC,
    momo_score           NUMERIC,
    fund_score           NUMERIC,
    target_weight_pct    NUMERIC,
    price_at_rec         NUMERIC NOT NULL CHECK (price_at_rec > 0),
    reason               TEXT,
    created_at           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    -- 채점 결과 (추천 시점 대비 실현 수익률; benchmark_*는 같은 기간 SPY 수익률)
    return_7d            NUMERIC,
    return_30d           NUMERIC,
    return_60d           NUMERIC,
    benchmark_return_7d  NUMERIC,
    benchmark_return_30d NUMERIC,
    benchmark_return_60d NUMERIC,
    CONSTRAINT fk_recommendations_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_recommendations_report_id FOREIGN KEY (report_id) REFERENCES public.reports(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id    ON public.recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON public.recommendations(created_at);

-- Functions -------------------------------------------------------------------
-- updated_at 자동 갱신용 (portfolios, positions 공용)
CREATE OR REPLACE FUNCTION public.set_portfolio_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

-- Triggers (재실행 안전) ------------------------------------------------------
DROP TRIGGER IF EXISTS portfolio_updated_at ON public.portfolios;
CREATE TRIGGER portfolio_updated_at
    BEFORE UPDATE ON public.portfolios
    FOR EACH ROW EXECUTE FUNCTION public.set_portfolio_updated_at();

DROP TRIGGER IF EXISTS position_updated_at ON public.positions;
CREATE TRIGGER position_updated_at
    BEFORE UPDATE ON public.positions
    FOR EACH ROW EXECUTE FUNCTION public.set_portfolio_updated_at();
