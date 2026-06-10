# 포트폴리오 분석 리포트 / Portfolio Analysis Report

_생성일시 / Generated: {{ asof }}_

## 요약 / TL;DR

{{ narrative.tldr }}

## 포트폴리오 변경사항 / Portfolio Changes

| 액션/Action | 티커/Ticker | 목표비중/Target % | 현재비중/Current % | 수량/Shares | 금액/Value |
| ----------- | ----------- | ----------------- | ------------------ | ----------- | ---------- |
{% for d in decisions -%}
| {{ d.action }} | {{ d.ticker }} | {{ "%.1f"|format(d.target_weight_pct) }}% | {{ "%.1f"|format(d.current_weight_pct) }}% | {{ "%+.4g"|format(d.shares_to_trade) if d.shares_to_trade else "-" }} | {{ "${:+,.2f}".format(d.trade_value) if d.trade_value else "-" }} |
{% endfor %}
{% if final_portfolio %}
{% if language == "ko" -%}
**포트폴리오 요약**: 총 가치 {{ "${:,.2f}".format(final_portfolio.total_value or 0) }} (현금 {{ "${:,.2f}".format(final_portfolio.cash or 0) }}, 주식 {{ "${:,.2f}".format(final_portfolio.total_stock_value or 0) }})
{%- else -%}
**Portfolio Summary**: Total value {{ "${:,.2f}".format(final_portfolio.total_value or 0) }} (cash {{ "${:,.2f}".format(final_portfolio.cash or 0) }}, stocks {{ "${:,.2f}".format(final_portfolio.total_stock_value or 0) }})
{%- endif %}
{% endif %}

## 종목 분석 / Stock Analysis

{% for d in decisions %}
### {{ d.ticker }} - {{ d.action }}

- **종합점수/Combined Score**: {{ "%.0f"|format(d.total_score) }}/100 (모멘텀/Momentum: {{ "%.0f"|format(d.momo_score) }}, 펀더멘털/Fundamental: {{ "%.0f"|format(d.fund_score) }})
- **결정/Decision**: {{ d.action }}
- **근거/Rationale**: {{ comments.get(d.ticker) or d.reason }}
{% if d.risk_notes -%}
- **리스크/Risk Notes**: {{ d.risk_notes | join("; ") }}
{% endif %}
{% endfor %}

## 추천 성적표 / Track Record

{% set sc = review_note.get("scorecard", {}) if review_note else {} %}
{% set overall = sc.get("overall", {}) %}
{% set delta = review_note.get("adjustment", 0) if review_note else 0 %}
{% set has_signal_stats = sc.get("momentum_led", {}).get("hit_rate") is not none and sc.get("fundamental_led", {}).get("hit_rate") is not none %}
{% if overall.get("calls") %}
{% if language == "ko" -%}
- 최근 {{ sc.get("lookback_days", 90) }}일간 채점된 추천 {{ overall.calls }}건 — 적중률 {{ "%.0f"|format(overall.hit_rate * 100) }}%, 평균 초과수익 {{ "%+.1f"|format(overall.avg_excess_return_pct) }}%p (같은 기간 S&P 500 대비, {{ sc.get("window_days", 30) }}일 기준)
{% if has_signal_stats -%}
- 추세 분석(모멘텀) 주도 추천 적중률 {{ "%.0f"|format(sc.momentum_led.hit_rate * 100) }}% ({{ sc.momentum_led.calls }}건) vs 기업 가치 분석(펀더멘털) 주도 {{ "%.0f"|format(sc.fundamental_led.hit_rate * 100) }}% ({{ sc.fundamental_led.calls }}건) → 이번 분석 가중치: 추세 {{ "%.1f"|format(50 + delta * 100) }}% / 기업 가치 {{ "%.1f"|format(50 - delta * 100) }}%
{% endif -%}
{% if sc.get("best_call") -%}
- 최고 추천: {{ sc.best_call.ticker }} {{ sc.best_call.action }} ({{ "%+.1f"|format(sc.best_call.excess_return_pct) }}%p) / 아쉬운 추천: {{ sc.worst_call.ticker }} {{ sc.worst_call.action }} ({{ "%+.1f"|format(sc.worst_call.excess_return_pct) }}%p)
{% endif -%}

_용어 안내: **적중률**은 추천 방향이 같은 기간 S&P 500 지수보다 나은 결과로 이어진 비율입니다. **추세 분석(모멘텀)**은 주가의 흐름과 거래량을, **기업 가치 분석(펀더멘털)**은 기업의 실적과 재무 건전성을 근거로 합니다._
{%- else -%}
- Last {{ sc.get("lookback_days", 90) }} days: {{ overall.calls }} scored calls — {{ "%.0f"|format(overall.hit_rate * 100) }}% hit rate, {{ "%+.1f"|format(overall.avg_excess_return_pct) }}%p average excess return (vs S&P 500, {{ sc.get("window_days", 30) }}-day basis)
{% if has_signal_stats -%}
- Trend-led (momentum) calls: {{ "%.0f"|format(sc.momentum_led.hit_rate * 100) }}% hit rate ({{ sc.momentum_led.calls }} calls) vs business-value-led (fundamental): {{ "%.0f"|format(sc.fundamental_led.hit_rate * 100) }}% ({{ sc.fundamental_led.calls }} calls) → current weighting: trend {{ "%.1f"|format(50 + delta * 100) }}% / business value {{ "%.1f"|format(50 - delta * 100) }}%
{% endif -%}
{% if sc.get("best_call") -%}
- Best call: {{ sc.best_call.ticker }} {{ sc.best_call.action }} ({{ "%+.1f"|format(sc.best_call.excess_return_pct) }}%p) / Worst call: {{ sc.worst_call.ticker }} {{ sc.worst_call.action }} ({{ "%+.1f"|format(sc.worst_call.excess_return_pct) }}%p)
{% endif -%}

_Glossary: **Hit rate** is how often a call beat the S&P 500 over the same period. **Trend analysis (momentum)** looks at price action and volume; **business-value analysis (fundamentals)** looks at earnings and financial health._
{%- endif %}
{% else %}
{% if language == "ko" -%}
- 추천 성적을 쌓는 중입니다. 각 추천은 {{ sc.get("window_days", 30) }}일이 지난 뒤 실제 수익률로 채점되며, 충분한 표본이 모이면 적중률과 분석 가중치 조정 근거가 여기에 표시됩니다.
{%- else -%}
- Track record is still building — each call is scored against realized returns {{ sc.get("window_days", 30) }} days after it is made. Hit rates and weighting rationale will appear here once enough calls are scored.
{%- endif %}
{% endif %}

## 시장 전망 및 전략 / Market Outlook & Strategy

{{ narrative.market_outlook }}

## 면책사항 / Legal Disclaimer

본 보고서는 정보 제공 목적으로만 작성되었으며, 투자 권유나 조언이 아닙니다. / This report is for informational purposes only and does not constitute investment advice.

**데이터 출처/Data Sources**: 가격 데이터 기준 {{ asof }}, 펀더멘털 데이터는 지연될 수 있음 / Price data as of {{ asof }}, fundamental data may lag
