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

## 시장 전망 및 전략 / Market Outlook & Strategy

{{ narrative.market_outlook }}

## 면책사항 / Legal Disclaimer

본 보고서는 정보 제공 목적으로만 작성되었으며, 투자 권유나 조언이 아닙니다. / This report is for informational purposes only and does not constitute investment advice.

**데이터 출처/Data Sources**: 가격 데이터 기준 {{ asof }}, 펀더멘털 데이터는 지연될 수 있음 / Price data as of {{ asof }}, fundamental data may lag
