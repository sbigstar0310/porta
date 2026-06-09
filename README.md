# (Porta) LangGraph 기반 멀티-에이전트 투자 보고 시스템 설계 문서

<details>
<summary><strong><h2>0. 수동 시작 방법 (How to run on your local device)</h2></strong></summary>

- 직접 수동(local)으로 애플리케이션을 구동하고 싶은 경우 아래 사항을 따라해주세요.

### 📋 사전 요구사항

시작하기 전에 다음이 설치되어 있는지 확인하세요:

- **Python 3.10 이상** - [다운로드](https://www.python.org/downloads/)
- **Node.js & npm** - [다운로드](https://nodejs.org/)
- **Flutter SDK** - [설치 가이드](https://docs.flutter.dev/get-started/install)
- **Redis** - [설치 가이드](https://redis.io/docs/install/)
- **uv** (Python 패키지 매니저) - [설치 가이드](https://docs.astral.sh/uv/getting-started/installation/)

### 🔑 1단계: 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# OpenAI API (필수)
OPENAI_API_KEY="sk-your-openai-api-key-here"

# LangSmith (선택사항 - 에이전트 추적용)
LANGSMITH_API_KEY="ls__your-langsmith-api-key"

# Supabase (필수 - 데이터베이스 & 인증)
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_KEY="your-supabase-anon-key"              # anon public 키 (인증/GoTrue용)
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"  # service_role 키 (데이터 계층, RLS 우회)

# Resend (필수 - 이메일 발송)
RESEND_API_KEY="re_your-resend-api-key"
```

#### 🔐 API 키 발급 방법:

1. **OpenAI API**: [OpenAI 플랫폼](https://platform.openai.com/api-keys)에서 발급
2. **LangSmith**: [LangSmith](https://smith.langchain.com/)에서 가입 후 발급 (선택사항)
3. **Supabase**: [Supabase](https://supabase.com/)에서 새 프로젝트 생성 후 Settings → API에서 확인
4. **Resend**: [Resend](https://resend.com/)에서 가입 후 API Keys에서 발급

### 🚀 2단계: 백엔드 실행

```bash
# 프로젝트 루트에서 백엔드 디렉토리로 이동
cd backend

# Python 의존성 설치
uv sync

# 데이터베이스 초기화 (Supabase 설정 후)
uv run python -c "from data.db import Database; import asyncio; asyncio.run(Database.initialize())"

# Redis 서버 시작 (별도 터미널)
redis-server

# Celery 워커 시작 (별도 터미널)
uv run ./scripts/run-celery.sh

# FastAPI 서버 시작
uv run ./scripts/run-server.sh
```

백엔드가 성공적으로 실행되면 `http://localhost:8000`에서 접속 가능합니다.

### 📱 3단계: 프론트엔드 실행

```bash
# 프로젝트 루트에서 프론트엔드 디렉토리로 이동
cd frontend

# Flutter 의존성 설치
flutter pub get

# 웹에서 실행
flutter run -d web-server --web-port 3000

# 또는 모바일 디바이스에서 실행
flutter run
```

프론트엔드가 성공적으로 실행되면 `http://localhost:3000`에서 접속 가능합니다.

### 🔧 4단계: Supabase 데이터베이스 설정

1. [Supabase 대시보드](https://supabase.com/dashboard)에서 새 프로젝트 생성
2. **SQL Editor**에서 `backend/data/sql_history/latest.sql` 내용을 붙여넣고 실행 (테이블 + 트리거 일괄 생성, 재실행 안전)
3. **Settings → API**에서 `Project URL`, `anon public` 키, `service_role` 키를 복사해 위 `.env`에 입력
4. (이메일 인증 사용 시) **Authentication → URL Configuration**에 Site URL/Redirect URL 설정, **SMTP Settings**에 Resend 연동
</details>

## 1. 프로젝트 개요

- 본 시스템은 **LangGraph 기반 멀티 에이전트 파이프라인**을 통해 사용자의 주식 포트폴리오를 분석하고, 매일 사용자가 지정한 시각에 이메일로 **투자 리포트**(매수/매도/보유 제안 및 근거)를 발송한다.
- 사용자는 리포트를 기반으로 **직접 투자 결정을 내리고**, 이후 웹사이트에서 자신의 포트폴리오를 업데이트할 수 있다.
- **자동 매매는 수행하지 않으며**, 리포트 제공 및 포트폴리오 관리 기능에 집중한다.
- 포트폴리오 및 주식의 경우 미국 주식으로 한정한다.

---

## 2. 주요 기능

- **포트폴리오 관리**

  - 보유 현금, 종목, 주식 수량, 평균 매입가, 수익률 저장
  - 웹에서 CRUD 가능

- **자동 분석 리포트 발송**

  - 사용자가 설정한 시간에 LangGraph 파이프라인 실행
  - 멀티 에이전트 기반 분석 → PDF 보고서 생성 → 이메일 발송(Resend)

- **수동 실행**

  - 사용자가 원할 때 즉시 파이프라인 실행 가능

- **시각화**

  - 웹에서 보유 종목 비중, 자산 추이, 수익률 차트 제공

- **로그인 및 데이터 보안**

  - Supabase Auth 기반 이메일 로그인
  - 사용자별 포트폴리오/기록 DB 저장, RLS(Row Level Security) 적용

---

## 3. 기술 스택

- **프론트엔드**: Flutter (flutter_bloc, go_router)
- **백엔드**: Python 3.10, FastAPI, uvicorn, uv
- **에이전트**: LangGraph + LangChain, OpenAI GPT
- **데이터베이스**: Supabase (PostgreSQL + Auth)
- **백그라운드 작업**: Celery + Redis
- **외부 API**: Yahoo Finance (주식 데이터), DuckDuckGo (웹 검색)
- **이메일**: Resend + WeasyPrint (PDF 생성)
- **인프라**: Docker Compose, Nginx (리버스 프록시 + Flutter web 정적 서빙, API는 `/api`)

---

## 4. 시스템 아키텍처
<img width="1998" height="1034" alt="Image" src="https://github.com/user-attachments/assets/2c84a1fc-8a7b-4166-a073-21ca80534782" />

---

## 5. 데이터 모델 (DB 스키마)

자세한 DB 스키마는 `backend/data/sql_history/latest.sql` 파일을 참고하세요 (신규 Supabase 프로젝트 초기화용 정본 스크립트).

**주요 테이블:**

- `users`: 사용자 정보 (이메일, 언어, 타임존)
- `portfolios`: 포트폴리오 (현금, 기본통화)
- `transactions`: 거래 내역 (매수/매도, 가격, 수량)
- `reports`: 에이전트 분석 보고서

---

## 6. LangGraph 파이프라인

자세한 에이전트 파이프라인 구조는 `documents/agent-pipeline.md` 파일을 참고하세요.

**에이전트 구성:**

- **Crawler**: 뉴스/시장 데이터 수집
- **Momo**: 모멘텀 분석
- **Fund**: 펀더멘털 분석
- **Reviewer**: 포트폴리오 리뷰
- **Risk**: 리스크 관리
- **Decider**: 투자 결정
- **Reporter**: 보고서 생성

---

## 7. API 엔드포인트

자세한 API 문서는 다음을 참고하세요:

- **코드**: `backend/routers/` 폴더의 각 라우터 파일
- **인터랙티브 문서**: `http://localhost:8000/docs` (Swagger UI)

**주요 엔드포인트:**

- `/auth`: 인증 관련
- `/portfolio`: 포트폴리오 관리
- `/positions`: 보유 종목 관리
- `/agent`: 에이전트 실행 및 상태 조회
- `/reports`: 분석 보고서 조회
- `/stocks`: 종목 검색
