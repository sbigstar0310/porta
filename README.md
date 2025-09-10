# (Porta) LangGraph 기반 멀티-에이전트 투자 보고 시스템 설계 문서

## 1. 프로젝트 개요

본 시스템은 **LangGraph 기반 멀티 에이전트 파이프라인**을 통해 사용자의 주식 포트폴리오를 분석하고, 매일 장외 시간(KST 09:00\~17:00) 중 사용자가 지정한 시각에 이메일로 \*\*투자 리포트(매수/매도/보유 제안 및 근거)\*\*를 발송한다.
사용자는 리포트를 기반으로 **직접 투자 결정을 내리고**, 이후 웹사이트에서 자신의 포트폴리오를 업데이트할 수 있다.
**자동 매매는 수행하지 않으며**, 리포트 제공 및 포트폴리오 관리 기능에 집중한다.

---

## 2. 주요 기능

- **포트폴리오 관리**

  - 보유 현금, 종목, 주식 수량, 평균 매입가, 수익률 저장
  - 웹에서 CRUD 가능

- **자동 분석 리포트 발송**

  - 사용자가 설정한 시간에 LangGraph 파이프라인 실행
  - 멀티 에이전트 기반 분석 → 이메일 발송(Resend)

- **수동 실행**

  - 사용자가 원할 때 즉시 파이프라인 실행 가능

- **시각화**

  - 웹에서 보유 종목 비중, 자산 추이, 수익률 차트 제공

- **로그인 및 데이터 보안**

  - Supabase Auth 기반 이메일 로그인
  - 사용자별 포트폴리오/기록 DB 저장, RLS(Row Level Security) 적용

---

## 3. 기술 스택

- **프론트엔드**: React (또는 Next.js), 차트 라이브러리(d3, recharts 등)
- **백엔드**: Python 3.10, FastAPI, uvicorn, uv
- **에이전트 프레임워크**: LangGraph
- **DB**: Supabase(Postgres)
- **이메일 발송**: Resend
- **스케줄링**: APScheduler(FastAPI 내), 또는 Supabase pg_cron

---

## 4. 시스템 아키텍처

```
 ┌─────────────┐          ┌───────────────┐
 │   프론트엔드   │──HTTP──▶│    FastAPI     │──┐
 │ (React/웹)   │          │  (백엔드 API)   │  │
 └─────┬───────┘          └─────┬─────────┘  │
       │                        │            │
       │                        ▼            │
       │              ┌──────────────────┐   │
       │              │   LangGraph      │   │
       │              │ (멀티 에이전트)      │   │
       │              └───────┬──────────┘   │
       │                      │              │
       ▼                      ▼              │
 ┌─────────────┐      ┌─────────────┐       │
 │   Supabase  │◀────▶│  Price API  │       │
 │ (DB & Auth) │      │ (Yahoo 등)  │       │
 └─────────────┘      └─────────────┘       │
       ▲                                    │
       │                                    │
       └───────────────────────Resend───────┘
                              (이메일 발송)
```

---

## 5. 데이터 모델 (DB 스키마)

(TODO)

---

## 6. LangGraph 파이프라인

### 상태 (State)

(TODO)

---

## 7. API 설계 (FastAPI)

- `GET /portfolio` : 포트폴리오 조회
- `PATCH /portfolio` : 현금·기본통화 수정
- `GET /positions` / `POST /positions` / `PATCH /positions/{symbol}` / `DELETE /positions/{symbol}`
- `POST /agent-feedback` : LangGraph 파이프라인 수동 실행
- `GET /agent-feedback/{id}` : 실행 결과 조회
- `POST /schedules` : 분석 스케줄 등록
- `GET /report/preview` : 이메일 HTML 미리보기

---

## 8. 이메일 리포트 구조

- **상단 요약**: 총 자산, 현금 비율, 수익률
- **표**: `Symbol | Price | Current Weight | Target Weight | Action | Confidence`
- **분석 근거**: 각 에이전트의 설명 요약
- **웹 링크**: "웹에서 반영하기"
- **디스클레이머**: 투자자문 아님, 정보 제공용

---

## 9. 스케줄링 전략

- **APScheduler**: 백엔드 워커에서 분 단위 확인 후 실행
- **Supabase pg_cron**: DB 스케줄러가 주기적으로 API 호출
- UTC 저장 후 `Asia/Seoul` 변환하여 실행

---

## 10. 보안 및 운영 고려사항

- Supabase RLS 적용 (유저별 데이터 격리)
- 서비스 키는 서버 전용, 프론트에 노출 금지
- API 실패 시 재시도 로직
- 로그/모니터링(run_id 기반 추적)
- 이메일 실패 시 알림

---

## 11. 개발 로드맵

1. **DB 구축** (Supabase schema, RLS 설정)
2. **FastAPI 기본 API** (포트폴리오 CRUD, 실행 엔드포인트)
3. **LangGraph MVP** (가격 데이터 + MomentumAgent → 이메일 발송)
4. **스케줄링 구현** (09\~17시 사이 실행 보장)
5. **프론트엔드 CRUD/시각화** (React + Supabase Auth)
6. **Factor Agents 확장** (Value/Quality/News)
7. **리스크 매니저 고도화**
8. **리포트 디자인 개선 & 실사용 피드백 반영**
