--==================================================================================================
-- PostgreSQL schema
--==================================================================================================

-- 확장/설정 (필요 시)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- users -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email        VARCHAR(255) UNIQUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login   TIMESTAMPTZ NOT NULL DEFAULT now(),
    timezone     VARCHAR(50)  NOT NULL DEFAULT 'UTC',
    language     VARCHAR(2)   NOT NULL DEFAULT 'en'
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS uuid UUID NOT NULL DEFAULT uuid_generate_v4();

-- portfolios ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS portfolios (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       BIGINT      NOT NULL,
    base_currency VARCHAR(3)  NOT NULL DEFAULT 'USD',
    cash          NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_portfolio_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_portfolios_user UNIQUE (user_id)
);


-- transactions ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
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
    CONSTRAINT fk_transaction_portfolio
        FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
);
-- Functions -------------------------------------------------------------------

-- updated_at 자동 갱신용 함수 (portfolios)
CREATE OR REPLACE FUNCTION set_portfolio_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

-- auth.users -> public.users 자동 업데이트 함수
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
security definer set search_path = ''
AS $$
BEGIN
  insert into public.users (uuid, email)
  values (NEW.uuid, NEW.email);
  return NEW;
END;
$$;


-- Triggers -------------------------------------------------------------------
DO $$
BEGIN
    create trigger portfolio_updated_at
    BEFORE UPDATE ON portfolios
    FOR EACH ROW EXECUTE FUNCTION set_portfolio_updated_at();

    create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();
END $$;