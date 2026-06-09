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
