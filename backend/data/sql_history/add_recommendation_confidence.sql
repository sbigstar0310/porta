-- 추천 확신도(0-100): DECIDER가 콜마다 스스로 매기는 적중 확률.
-- 채점 시 Brier score로 보정 상태(과신/신중)를 측정한다.
ALTER TABLE public.recommendations ADD COLUMN IF NOT EXISTS confidence NUMERIC;
