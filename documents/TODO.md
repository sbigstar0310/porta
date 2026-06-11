# TODOs

> 2026-06-11 기준 전면 갱신. 완료 항목은 ✅로 이력 유지, 신규 로드맵은 우선순위순.

## 에이전트 로드맵 (다음 작업)

### 1. Bull/Bear 토론 에이전트
현재 파이프라인엔 반대 논거를 생성하는 단계가 없음(전부 한 방향: 발굴→점수→결정). XOM 48점 BUY 사건이 실증한 구조적 맹점 — 임계값 게이트는 증상 차단, 토론은 나쁜 결정이 덜 나오게 하는 원인 치료. 토론 결과는 보고서 "강세/약세 논리" 섹션으로 그대로 사용자 가치가 됨.
- [ ] MOMO/FUND ↔ RISK 사이 토론 서브그래프 (강세/약세 연구원, 2라운드, 구조화 요약 교환)
- [ ] 비용 제어: 결정 경계 종목만 토론 (점수 55~75 또는 신호 불일치 또는 신규 후보 상위 N)
- [ ] 보고서 "강세 논리 / 약세 논리" 섹션 (SELL 권고의 감정적 수용성 개선 포함)

### 2. Phase 4. 백테스트 하네스
- [ ] 과거 시점 리플레이로 상수 검증·튜닝: δ 계수(0.75)·shrink(n/20)·클램프(±0.15), 국면 임계값, 매수 기준(62/65/72), 채점 창(30일)
- [ ] 룩어헤드 차단: 모델 컷오프 이후 기간으로만 평가 (LLM 암기 효과 배제)
- [ ] 트랙레코드 수 주 축적 후 착수 권장

### 3. OpenRouter 멀티 프로바이더 — 저비용·고효율 모델 운용
현재 파이프라인이 OpenAI API 단일 의존. OpenRouter를 붙여 상황에 따라 저비용 모델로도 구동 가능하게.
- [ ] `graph/llm_clients/openrouter_client.py` — OpenRouter는 OpenAI 호환 API라 `ChatOpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)`로 기존 클라이언트 재사용 가능
- [ ] tier→모델 매핑을 프로바이더별 설정으로 분리 (`LLM_PROVIDER` env로 전환, `AGENT_TIERS`/`build_root_graph(llm_factory=...)` 구조는 그대로)
- [ ] 저비용 모델 후보 선정: tier별 평가 — **tool calling + structured output 지원 여부가 필수 조건** (create_react_agent 의존), LIGHT/MIDDLE 티어부터 교체 실험
- [ ] 품질 게이트: 모델 교체는 `run_e2e.py` 통과 + 트랙레코드/백테스트 적중률 비교 후 적용 (싸졌는데 적중률 떨어지면 본전도 못 찾음 — Phase 4와 연계)
- [ ] (확장) 상황별 동적 라우팅: 평시는 저비용, risk_off 국면이나 신규 후보 多 시기엔 상위 모델로 승급하는 규칙 검토

## 프론트엔드

### 디자인 시스템 고도화
현재 UI가 AI 생성 티가 나는 범용 디자인이라 실 서비스 같은 완성도가 부족함. 신뢰가 핵심인 금융 서비스 특성상 시각적 완성도 = 제품 신뢰도.
- [ ] 디자인 토큰 정립: 컬러 팔레트(브랜드 컬러 결정)·타이포그래피 스케일·간격/라운딩 체계를 `constants/`에 일원화 — 화면별 임의 스타일 제거
- [ ] 공용 위젯 정비: 카드·버튼·입력·상태(로딩/빈/에러) 컴포넌트를 디자인 토큰 기반으로 통일
- [ ] 금융 앱 레퍼런스 벤치마킹 (토스·로빈후드 등): 정보 밀도, 숫자 표기(등락 색·포맷), 시각적 계층
- [ ] 핵심 가치 화면 우선 적용: 보고서 열람 → 포트폴리오 대시보드 → 설정 순
- [ ] 라이트/다크 모드 일관성 점검
- 참고: 인증·세션 등 기능 이슈 잔여분은 프론트 세션에서 별도 트래킹 중

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
