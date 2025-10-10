# MVP Agent-Pipeline 설계서

> **목적**: 보유 포트폴리오와 신규 후보를 자동 분석하여 **프리마켓(KST 17:00 전)** 이메일 리포트를 발송한다.
> **비고**: 실제 매매 체결 없음.

---

## 파이프라인 개요

**실행 윈도우 (KST)**

- 대상: 애프터마켓 종료(06:00) \~ 프리마켓 시작(17:00) 사이
- 주기: 사용자 설정 시각에 1회 실행
- 데이터 기준시각: 파이프라인 시작 시 UTC 타임스탬프 고정

**흐름도**

1. START → (**Crawler Agent**, **Reviewer Agent**) [병렬]
   - Crawler Agent → (**Momo Agent**, **Fund Agent**) [병렬]
   - (**Momo Agent**, **Fund Agent**, **Reviewer Agent**) → **Risk Manager Agent**
     - RISK는 MOMO/FUND/REVIEWER가 모두 완료될 때까지 대기 (게이트)
   - Risk Manager Agent → Decider Agent → Reporter Agent → END

---

## 에이전트 정의

### 1. Crawler Agent

- **역할**: 신규 종목을 탐색 및 추천
- **출력**: `new_candidates[]` (티커, 종목명, 추천 사유)

### 2. Reviewer Agent

- **역할**: 지난 리포트의 권고안 성과 검증 → Momo/Fund 가중치 조정
- **출력**: `(opinion, preference, adjustment)`
- **예외**: 히스토리 부족 시 자동 스킵

### 3. Momo Agent

- **역할**: 뉴스·헤드라인·단기 가격 모멘텀 분석 → 후보 종목 스코어링
- **스코어링**
  - $trend = 0.4 \times z_{20} + 0.6 \times z_{60}$
  - $vol\_conf = 0.7 \times z_{vol} + 0.3 \times \ln(vol\_surge)$
  - $pattern = 0.5 \times ma\_cross + 0.5 \times break\_out$
  - $vol\_penalty = \frac{atr\_pct_{14}}{0.05}$
  - $s = 0.5 \times trend + 0.3 \times vol\_conf + 0.3 \times pattern - 0.2 \times vol\_penalty$
  - $momo\_score = \lfloor 100 \times \sigma(0.7 \times s) \rfloor$
- **입력**: 전종목 메타 + 뉴스 피드 + 단기 가격 시계열
- **출력**: `momo_score: MomoItem[]` (각 항목: `ticker`, `score = { MOMO, features, norm, data_confidence }`)

### 4. Fund Agent

- **역할**: 재무 지표 기반 FUND_SCORE 산출
- **스코어링**

  - Valuation V: 저평가 여부 (PE, EV/Sales z-score 등)
  - Growth G: 매출 성장률
  - Quality Q: 수익성 (영업이익률, FCF 마진 등)
  - Earnings E: 어닝 서프라이즈 반영

- **결합식**: `FUND_SCORE = 0.3V + 0.3G + 0.25Q + 0.15E`
- **라벨링**: `Strong ≥70 / Neutral 50–70 / Weak <50`
- **결측치**: 섹터 중앙값 대체 + `data_confidence` 플래그
- **출력**: `fund_score: FundItem[]` (각 항목: `ticker`, `FUND`, `scores={V,G,Q,E}`, `label`, `insights`, `data_confidence`)

### 5. Risk Manager Agent

- **역할**: 리스크 제약 및 종목별 최대 비중 계산
- **체크리스트**

  - 단일 종목 ≤ 15%, 섹터 ≤ 35%
  - 포트폴리오 β 추정
  - 변동성(ATR%) 상한
  - 유동성 필터 (ADV 하한)
  - 이벤트(어닝 D-3 증액 금지)

- **사이징 가이드**
  `max_weight_pct = base × min(1, 1 / max(1, beta, atr_pct / 4%))`

### 6. Decider Agent

- **역할**: Momo + Fund 점수 결합 → Risk 제약 반영 → Buy/Hold/Sell 결정
- **결합식**:
  `TOTAL = (0.50 + δ)·MOMO + (0.50 − δ)·FUND`
  (δ: Reviewer 조정, 범위 ±0.05)
- **룰 (업데이트)**

  - 기존 보유 종목(유니버스):
    - BUY/ADD: `TOTAL ≥ 65` 그리고 리스크 제약 충족
    - HOLD: `45 ≤ TOTAL < 65` 또는 제약으로 변경 불가
    - TRIM: `40 ≤ TOTAL < 45` 또는 일부 제약 초과
    - SELL: `TOTAL < 40` 또는 주요 리스크 플래그
  - 신규 후보(보유 아님):
    - BUY Only: `TOTAL ≥ 65` 그리고 리스크 제약 충족
    - No Action: `TOTAL < 65` 또는 제약 위반

### 7. Reporter Agent

- **역할**: 리포트 생성 및 이메일 발송 (Markdown/HTML)
- **섹션 구성**

  - TL;DR (5줄 요약)
  - 변경 요약표 (편입/증액/축소/청산, 목표비중, 사유)
  - 종목 카드 (점수, 결정, 근거, 리스크)
  - 주의 이벤트 (어닝, 매크로 일정)
  - 법적 고지 및 데이터 기준시각

- **언어 지시**: 입력 `language` 값에 따라 전체 리포트를 한국어("ko") 또는 영어("en")로 생성 (기본 한국어)
- **포맷 규칙**: 내부 컴포넌트/도구명은 리포트에 노출하지 않음
- **출처 표기**: 가격, 재무, 뉴스 소스

---

## MVP 단계 목표

- Reviewer: Hit rate & PnL 기반 소폭 가중치 조정 (δ ∈ \[−0.05, +0.05])
- Finder: 뉴스 키워드 + 단기 모멘텀 필터
- Crawler: 시세, 뉴스, 어닝 일정, 재무 스냅샷 수집
- Fundamental: V/G/Q/E 기반 FUND_SCORE 산출
- Risk Manager: 비중 제약·ATR/β 기반 사이징·ADV 필터·어닝 D-3 룰
- Decider: MOMO+FUND 결합 + Risk 반영
- Reporter: 이메일 리포트 발송

---

## 기본 파라미터 (권장값)

- 단일 종목 상한: 15%
- 섹터 상한: 35%
- 현금 최소: 5%
- ATR 필터: 신규 확대 시 ATR% ≤ 6%
- 유동성: ADV ≥ \$5M
- 이벤트 룰: 어닝 D-3 내 신규/증액 금지
- 결합 가중치: MOMO 0.55 / FUND 0.45 (Reviewer 조정 가능)

---

## 품질 지표 & 안전장치

- **품질 관리**: 결측 대체율 < 15%, 데이터 근거 충족률, 경고 탐지율
- **성과 평가**: Hit rate(@1D/@3D), SPY 대비 초과수익, 가정 PnL
- **안전장치**: Fail-Closed (데이터 장애 시 보수적 권고), 타임아웃/리트라이

---

## Non-Goals (MVP 범위 외)

- 실시간 주문 체결/라우팅
- 옵션·파생 전략
- 고급 팩터·정교 튜닝

---

## 에이전트 출력 (예시)

**Crawler 출력**

```json
{
  "new_candidates": [
    {
      "ticker": "NVDA",
      "name": "NVIDIA Corp",
      "reason": "최근 실적 발표에서 예상치를 크게 상회했으며, AI 데이터센터 수요 급증 소식으로 다수의 주요 언론이 집중 보도함. 단기 모멘텀 강세가 지속될 가능성이 있음."
    },
    {
      "ticker": "PLTR",
      "name": "Palantir Technologies",
      "reason": "미국 국방부와 다년간의 대형 계약을 체결했다는 보도가 이어지고 있으며, AI·정부 프로젝트 확대 기대감이 커지고 있음."
    }
  ]
}
```

**Reviewer Agent 출력**

```json
{
  "period": "2025-09-03..2025-09-06",
  "opinion": "지난 회차 권고의 성과가 벤치마크보다 다소 우수했습니다. 최근에는 단기 모멘텀 신호가 잘 작동하는 경향이 있으므로 momentum 쪽 가중치를 약간 더 주는 것이 합리적입니다.",
  "preference": "momentum",
  "adjustment": 0.02
}
```

**Momo Agent 출력 (업데이트: 리스트 스키마)**

```json
{
  "version": "1.0",
  "asof": "UTC ISO8601",
  "momo_score": [
    {
      "ticker": "AAPL",
      "score": {
        "MOMO": 63,
        "features": {
          "r20": 0.062,
          "r60": 0.118,
          "ma_cross": true,
          "breakout": true,
          "vol_surge": 1.8,
          "atr_pct_14": 0.032
        },
        "norm": {
          "z20": 0.7,
          "z60": 0.9,
          "zvol": 0.8
        },
        "data_confidence": "high"
      }
    },
    {
      "ticker": "TSLA",
      "score": {
        "MOMO": 72,
        "features": {
          "r20": 0.104,
          "r60": 0.155,
          "ma_cross": true,
          "breakout": true,
          "vol_surge": 2.5,
          "atr_pct_14": 0.075
        },
        "norm": {
          "z20": 1.2,
          "z60": 1.1,
          "zvol": 1.4
        },
        "data_confidence": "medium"
      }
    }
  ]
}
```

**Fund Agent 출력 (업데이트: 리스트 스키마)**

```json
{
  "version": "1.0",
  "asof": "2025-09-06T08:30:00Z",
  "fund_score": [
    {
      "ticker": "AAPL",
      "FUND": 68,
      "scores": { "V": 62, "G": 71, "Q": 78, "E": 55 },
      "label": "Neutral",
      "insights": [
        "EPS YoY +18% (섹터 상위권)",
        "ROE 30%+ → 수익성 강함",
        "최근 어닝 서프라이즈 제한적"
      ],
      "data_confidence": "high"
    },
    {
      "ticker": "TSLA",
      "FUND": 45,
      "scores": { "V": 40, "G": 60, "Q": 35, "E": 50 },
      "label": "Weak",
      "insights": [
        "밸류에이션 과열 (PER 70+)",
        "마진/ROE 낮음",
        "최근 컨센서스 하향"
      ],
      "data_confidence": "medium"
    }
  ]
}
```

**Risk Manager 출력 (업데이트: 리스트 스키마 + 게이트 동작)**

```json
{
  "risk_note": {
    "per_ticker": [
      {
        "ticker": "AAPL",
        "allowed": true,
        "max_weight_pct": 6.5,
        "beta": 1.2,
        "atr_pct": 3.2,
        "notes": ["liquidity ok", "vol normal"]
      },
      {
        "ticker": "TSLA",
        "allowed": true,
        "max_weight_pct": 3.0,
        "beta": 1.8,
        "atr_pct": 2.4,
        "notes": ["high volatility", "earnings T-2d (no_add)"]
      },
      {
        "ticker": "PLTR",
        "allowed": false,
        "max_weight_pct": 0.0,
        "beta": 0.2,
        "atr_pct": 3.2,
        "notes": ["ADV < $5M: insufficient liquidity"]
      }
    ],
    "portfolio_limits": {
      "single_stock_cap": 15.0,
      "sector_caps": [{ "sector": "Tech", "cap": 35.0 }],
      "cash_floor": 5.0
    },
    "portfolio_warnings": [
      {
        "type": "sector_concentration",
        "sector": "Tech",
        "actual": 42.0,
        "limit": 35.0
      }
    ],
    "overall_note": "Portfolio exhibits moderate risk profile."
  }
}
```

**Decider 출력 (업데이트: 의사결정/최종 포트폴리오 중심)**

```json
{
  "actions": [
    {
      "ticker": "AAPL",
      "action": "BUY",
      "target_weight_pct": 8.5,
      "current_weight_pct": 6.0,
      "shares_to_trade": 2.5,
      "trade_value": 568.5,
      "total_score": 72,
      "momo_score": 68,
      "fund_score": 75,
      "reason": "Strong combined signals (72/100), within risk limit",
      "risk_notes": ["Volatility normal"]
    },
    {
      "ticker": "TSLA",
      "action": "TRIM",
      "target_weight_pct": 3.0,
      "current_weight_pct": 8.0,
      "shares_to_trade": -2.1,
      "trade_value": -420.0,
      "total_score": 48,
      "momo_score": 55,
      "fund_score": 42,
      "reason": "Below hold threshold, reducing overweight position",
      "risk_notes": ["High volatility", "Sector overweight"]
    },
    {
      "ticker": "MSFT",
      "action": "HOLD",
      "shares_to_trade": 0,
      "trade_value": 0,
      "total_score": 73,
      "momo_score": 72,
      "fund_score": 75,
      "reason": "Maintain solid position",
      "risk_notes": []
    }
  ],
  "final_portfolio": {
    "id": 1,
    "user_id": 1,
    "base_currency": "USD",
    "cash": "1686.50",
    "updated_at": "2025-01-20T10:30:00Z",
    "positions": [
      {
        "id": 1,
        "portfolio_id": 1,
        "ticker": "AAPL",
        "total_shares": 10.5,
        "avg_buy_price": 207.1,
        "updated_at": "2025-01-20T09:30:00Z",
        "current_price": 227.4,
        "current_market_value": 2387.7,
        "unrealized_pnl": 160.12,
        "unrealized_pnl_pct": 8.4
      }
    ],
    "total_stock_value": 3635.4,
    "total_value": 5321.9,
    "total_unrealized_pnl": 160.12,
    "total_unrealized_pnl_pct": 10.15
  }
}
```

**Reporter 출력 (업데이트: 언어/템플릿 규칙 적용)**

```markdown
# 포트폴리오 분석 리포트 / Portfolio Analysis Report

_생성일시 / Generated: 2025-01-20T10:30:00Z_

## 요약 / TL;DR

<!-- 5줄 요약: 핵심 결정사항, 주요 변화, 리스크 경고 -->

## 포트폴리오 변경사항 / Portfolio Changes

| 액션/Action | 티커/Ticker | 목표비중/Target % | 현재비중/Current % | 근거/Rationale |
| ----------- | ----------- | ----------------- | ------------------ | -------------- |

## 종목 분석 / Stock Analysis

### [TICKER] - [BUY/HOLD/SELL/TRIM]

- **종합점수/Combined Score**: XX/100 (모멘텀/Momentum: XX, 펀더멘털/Fundamental: XX)
- **결정/Decision**: [action]
- **근거/Rationale**: [specific quantitative reasons]
- **리스크/Risk Notes**: [relevant warnings]

## 시장 전망 및 전략 / Market Outlook & Strategy

- 리뷰어 인사이트 및 비중 조정 / Reviewer insights and weight adjustments
- 리스크 환경 평가 / Risk environment assessment
- 다음 주기 고려사항 / Next period considerations

## 면책사항 / Legal Disclaimer

본 보고서는 정보 제공 목적으로만 작성되었으며, 투자 권유나 조언이 아닙니다. / This report is for informational purposes only and does not constitute investment advice.

**데이터 출처/Data Sources**: 가격 데이터 기준 2025-01-20T10:30:00Z, 펀더멘털 데이터는 지연될 수 있음
```
