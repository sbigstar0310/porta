# TODOs

> 2026-06-11 기준 전면 갱신. 완료 항목은 ✅로 이력 유지, 신규 로드맵은 우선순위순.

## 에이전트 로드맵 (다음 작업)

### 1. 2-2. 사용자별 리스크 성향 + 투자 경험 수준 (풀스택)
- [ ] `users`에 `risk_tolerance`(conservative/moderate/aggressive), `experience_level`(beginner/advanced) 컬럼 + 마이그레이션
- [ ] 설정 API (GET/PATCH) + 프론트 설정 화면
- [ ] 성향별 코드 규칙: 종목 상한·현금 바닥·매수 임계값 차등 (validation 강제, regime 규칙과 합성)
- [ ] RISK/DECIDER/REPORTER 프롬프트 페르소나 반영, 경험 수준별 보고서 상세도 조절

### 2. 2-3. Bull/Bear 토론 에이전트
- [ ] MOMO/FUND ↔ RISK 사이 토론 서브그래프 (강세/약세 연구원, 2라운드, 구조화 요약 교환)
- [ ] 비용 제어: 결정 경계 종목만 토론 (점수 55~75 또는 신호 불일치 또는 신규 후보 상위 N)
- [ ] 보고서 "강세 논리 / 약세 논리" 섹션 (토론 결과 = 사용자 가치)

### 3. Phase 4. 백테스트 하네스
- [ ] 과거 시점 리플레이로 상수 검증·튜닝: δ 계수(0.75)·shrink(n/20)·클램프(±0.15), 국면 임계값, 매수 기준(62/65/72), 채점 창(30일)
- [ ] 룩어헤드 차단: 모델 컷오프 이후 기간으로만 평가 (LLM 암기 효과 배제)
- [ ] 트랙레코드 수 주 축적 후 착수 권장

## 소규모 개선 (백로그)

- [ ] MOMO ToolMessage 파싱 폴백 원인 추적 (E2E 2회 연속 발동 — 안전망은 정상 작동, 직렬화 형식 확인)
- [ ] 보고서 회사명 한글화 (현재 영문 공식명 `Apple Inc.` — 주요 종목 한글명 매핑 테이블 검토)
- [ ] 죽은 코드 정리: `UserRepo.update`/`PortfolioRepo.update`/`TransactionRepo.update`(호출처 없음 + 버그 내재), `user_usecase.get_user_profile_sync`(항상 None인 죽은 경로) — 수정 또는 삭제
- [ ] `clients/__init__.py` `__all__`에 `get_supabase_admin_client` 누락
- [ ] 종목 검색 한글 회사명 지원 (Yahoo API 한글 미지원 — Finnhub symbol lookup 검토)
- [ ] Cache를 적극적으로 활용해서 비용 최적화하기

## 운영 / 비즈니스 (과금 전 필수 포함)

- [ ] **(과금 전 필수) Finnhub 상용 라이선스 협의** — 무료 티어는 개인용 한정. 대안: Tiingo 상용 $50/월. yfinance도 동일한 상용 리스크 (장기 정리 대상)
- [ ] prod Supabase에 `add_recommendation_confidence.sql` 적용 여부 확인 (recommendations 테이블은 적용 완료)
- [ ] dev Supabase Auth 설정(Site URL, 리다이렉트)을 prod와 동기화 — 프론트 Auth 플로우 검수 전 필요
- [ ] dev Supabase 무료 프로젝트 1주 미사용 시 일시정지 → 통합 테스트 실패 시 대시보드에서 Restore

## 인프라 / CI

- [ ] GitHub Actions Node 20 deprecation 대응 (actions/checkout, setup-uv 버전 업 — 2026-09 전)
- [ ] 통합 테스트 CI 잡 검토 (dev Supabase secrets 등록 + `RUN_INTEGRATION=1`, 스케줄 실행)
- [ ] pre-commit 적용하기 (lint/format 훅)

## ✅ 완료 (2026-06-11)

- [x] 테스트 코드 작성 및 실행 검증 — unit 363 + 통합 21 그린, CI 게이트 가동
- [x] 종목 검색 API (`/stock/search`)
- [x] Token 만료 시 자동 refresh — 프론트 인증 개선에서 처리 (`17fe015`)
- [x] 에이전트 Phase 0~3: 숫자 환각 차단, 트랙레코드·δ, 국면 신호, 확신도 보정, Finnhub, 매수 임계값 게이트
- [x] dev Supabase 분리 + E2E 도구, 보안 취약점 4건 수정
