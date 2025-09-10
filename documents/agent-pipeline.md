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

1. START → (**Crawler Agent**, **Reviewer Agent**)
   1.1. Crawler Agent → (Momo Agent, Fund Agent)
   1.2. Reviewer Agent → Risk Manager Agent
   2.1. Momo Agent → Risk Manager Agent
   2.2. Fund Agent → Risk Manager Agent
2. Risk Manager Agent → Decider Agent
3. Decider Agent → Reporter Agent
4. Reporter Agent → END

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
- **출력**: `scores[ticker] = { MOMO, features, norm, data_confidence }`

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
  `TOTAL = (0.55 + δ)·MOMO + (0.45 − δ)·FUND`
  (δ: Reviewer 조정, 범위 ±0.05)
- **룰**

  - BUY: `TOTAL ≥ 70` & Risk 제약 충족
  - HOLD: `50 ≤ TOTAL < 70` 또는 제약으로 증액 불가
  - TRIM/SELL: `TOTAL < 45` 또는 제약 초과

### 7. Reporter Agent

- **역할**: 리포트 생성 및 이메일 발송 (Markdown/HTML)
- **섹션 구성**

  - TL;DR (5줄 요약)
  - 변경 요약표 (편입/증액/축소/청산, 목표비중, 사유)
  - 종목 카드 (점수, 결정, 근거, 리스크)
  - 주의 이벤트 (어닝, 매크로 일정)
  - 법적 고지 및 데이터 기준시각

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

**Momo Agent 출력**

```json
{
  "version": "1.0",
  "asof": "UTC ISO8601",
  "momo_score": {
    "AAPL": {
      "MOMO": 63,
      "features": {
        "r20": 0.062,  # 최근 20일 수익률 (단기)
        "r60": 0.118,  # 최근 60일 수익률 (장기)
        "ma_cross": 1, # 이동평균선 교차 여부
        "breakout": true,  # 돌파 여부
        "vol_surge": 1.8,  # 거래량 급증 비율
        "atr_pct_14": 0.032  # 14일간 변동성 비율
      },
      "norm": {
        "z20": 0.7,
        "z60": 0.9,
        "zvol": 0.8
      },
      "data_confidence": "high"
    },
    "TSLA": {
      "MOMO": 72,
      "features": {
        "r20": 0.104,
        "r60": 0.155,
        "ma_cross": 1,
        "breakout": true,
        "vol_surge": 2.5,
        "atr_pct_14": 0.075
      },
      "norm": {
        "z20": 1.2,
        "z60": 1.1,
        "zvol": 1.4
      },
      "data_confidence": "medium" // 결측 대체/이상치 클립 등
    }
  }
}
```

**Fund Agent 출력**

```json
{
  "version": "1.0",
  "asof": "2025-09-06T08:30:00Z",
  "scores": {
    "AAPL": {
      "FUND": 68,
      "scores": {
        "V": 62,
        "G": 71,
        "Q": 78,
        "E": 55
      },
      "label": "Neutral",
      "insights": [
        "EPS YoY +18% (섹터 상위권)",
        "ROE 30%+ → 수익성 강함",
        "최근 어닝 서프라이즈 제한적"
      ],
      "data_confidence": "high"
    },
    "TSLA": {
      "FUND": 45,
      "scores": {
        "V": 40,
        "G": 60,
        "Q": 35,
        "E": 50
      },
      "label": "Weak",
      "insights": [
        "밸류에이션 과열 (PER 70+)",
        "마진/ROE 낮음",
        "최근 컨센서스 하향"
      ],
      "data_confidence": "medium"
    }
  }
}
```

**Risk Manager 출력**

```json
{
  "asof": "2025-09-06T08:30:00Z",
  "per_ticker": {
    "AAPL": {
      "allowed": true,
      "max_weight_pct": 6.5,
      "beta": 1.2,
      "atr_pct": 3.2,
      "notes": ["liquidity ok", "vol normal"]
    },
    "TSLA": {
      "allowed": true,
      "max_weight_pct": 3.0,
      "beta": 1.8,
      "atr_pct": 2.4,
      "notes": ["high volatility", "earnings T-2d (no_add)"]
    },
    "PLTR": {
      "allowed": false,
      "max_weight_pct": 0.0,
      "beta": 0.2,
      "atr_pct": 3.2,
      "notes": ["ADV < $5M: insufficient liquidity"]
    }
  },
  "portfolio_limits": {
    "single_stock_cap": 15,
    "sector_caps": { "Tech": 35 },
    "cash_floor": 5
  },
  "portfolio_warnings": [
    { "type": "sector_cap", "sector": "Tech", "actual": 42, "limit": 35 }
  ]
}
```

**Decider 출력**

```json
{
  "portfolio_before": {
    "summary_view": [
      {
        "ticker": "AAPL",
        "shares": 8.0,
        "avg_buy_price": 205.0,
        "current_price": 227.4,
        "total_value": 1819.2,
        "unrealized_pnl_pct": 10.9
      },
      {
        "ticker": "MSFT",
        "shares": 3.0,
        "avg_buy_price": 390.0,
        "current_price": 415.9,
        "total_value": 1247.7,
        "unrealized_pnl_pct": 6.6
      }
    ],
    "lot_details": [
      {
        "ticker": "AAPL",
        "lots": [
          {
            "buy_date": "2025-08-01",
            "shares": 5.0,
            "buy_price": 200.0,
            "current_price": 227.4,
            "value": 1137.0,
            "pnl_pct": 13.7
          },
          {
            "buy_date": "2025-08-15",
            "shares": 3.0,
            "buy_price": 210.0,
            "current_price": 227.4,
            "value": 682.2,
            "pnl_pct": 8.4
          }
        ]
      }
    ],
    "cash_value": 2000.0,
    "portfolio_value": 5000.0
  },

  "actions": [
    {
      "ticker": "AAPL",
      "action": "BUY",
      "shares_to_trade": 2.5,
      "trade_value": 568.5,
      "reason": "MOMO 상승 + FUND 안정적"
    },
    {
      "ticker": "TSLA",
      "action": "SELL",
      "shares_to_trade": 1.0,
      "trade_value": 245.0,
      "reason": "리스크 경고 + 추세 하락"
    },
    {
      "ticker": "MSFT",
      "action": "HOLD",
      "shares_to_trade": 0,
      "trade_value": 0,
      "reason": "펀더멘털 강세지만 추가 매수 제한"
    }
  ],

  "portfolio_after": {
    "summary_view": [
      {
        "ticker": "AAPL",
        "shares": 10.5,
        "avg_buy_price": 207.1,
        "current_price": 227.4,
        "total_value": 2387.7,
        "unrealized_pnl_pct": 8.4
      },
      {
        "ticker": "MSFT",
        "shares": 3.0,
        "avg_buy_price": 390.0,
        "current_price": 415.9,
        "total_value": 1247.7,
        "unrealized_pnl_pct": 6.6
      }
    ],
    "cash_value": 1686.5,
    "portfolio_value": 5321.9
  },

  "explanations": [
    "AAPL은 모멘텀 지표가 강세로 전환되어 추가 매수",
    "TSLA는 변동성 리스크가 커서 전량 매도 권고",
    "MSFT는 안정적 펀더멘털 유지, 현 수준 보유"
  ]
}
```

**Reporter 출력**

```markdown
# Portfolio Analysis Report

_Generated: 2025-01-20T10:30:00Z_

## TL;DR

- Added NVDA position (5%) based on strong momentum signals
- Increased AAPL allocation to 8.5% on combined strength
- Maintained MSFT position with solid fundamentals
- Current strategy slightly favors momentum (adjustment: +0.02)
- No significant risk warnings

## Portfolio Changes

| Action | Ticker | Target Weight | Current Weight | Rationale                      |
| ------ | ------ | ------------- | -------------- | ------------------------------ |
| BUY    | NVDA   | 5.0%          | 0.0%           | High momentum score, AI growth |
| BUY    | AAPL   | 8.5%          | 6.0%           | Strong combined signals        |
| HOLD   | MSFT   | 10.0%         | 10.0%          | Maintain solid position        |

## Stock Analysis

### NVDA - BUY

- **Combined Score**: 78/100 (Momentum: 85, Fundamental: 65)
- **Decision**: BUY new position at 5% weight
- **Rationale**: Exceptional momentum driven by AI datacenter demand
- **Risk Notes**: High volatility (6.5% ATR), position size limited

### AAPL - BUY

- **Combined Score**: 72/100 (Momentum: 68, Fundamental: 68)
- **Decision**: Increase position to 8.5%
- **Rationale**: Balanced strength across momentum and fundamentals
- **Risk Notes**: Normal volatility profile

### MSFT - HOLD

- **Combined Score**: 73/100 (Momentum: 72, Fundamental: 75)
- **Decision**: Maintain current 10% allocation
- **Rationale**: Strong fundamentals, cloud growth continues
- **Risk Notes**: Stable, low-risk holding

## Market Outlook & Strategy

Reviewer analysis indicates momentum signals performing well in current environment.
Strategy adjustment: +0.02 toward momentum weighting (55% → 57% momentum, 45% → 43% fundamental).

## Legal Disclaimer

This report is for informational purposes only and should not be considered as investment advice.

**Data Sources**: Price data as of 2025-01-20T10:30:00Z
```
