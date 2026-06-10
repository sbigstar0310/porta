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
