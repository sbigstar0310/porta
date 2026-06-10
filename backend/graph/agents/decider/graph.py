# agents/decider/graph.py
import asyncio
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from .schema import DeciderState, DeciderLLMOutput
from .validation import EARNINGS_BLACKOUT_DAYS, build_validated_decisions
from ...regime import regime_rules
from clients import get_finnhub_client, get_stock_client
from repo import get_portfolio_repo
from ...tools.db_data import get_current_portfolio, get_user_id_from_config
from ...tools.stock_data import get_stock_data
from ..utils import extract_structured_response, load_template, state_get
from langchain_core.runnables.config import RunnableConfig

logger = logging.getLogger(__name__)

DECIDER_SYSTEM_PROMPT = load_template(__file__)


def _fetch_earnings_blackout(tickers: list[str]) -> dict[str, str]:
    """실적 발표가 EARNINGS_BLACKOUT_DAYS 이내인 티커 → 발표일. 조회 불가 시 빈 dict."""
    client = get_finnhub_client()
    if not client.is_available():
        return {}
    try:
        return client.get_upcoming_earnings(tickers, days=EARNINGS_BLACKOUT_DAYS)
    except Exception as e:
        logger.warning(f"Failed to fetch earnings calendar (skipping blackout rule): {e}")
        return {}


def _fetch_company_names(tickers: list[str], new_candidates: list[dict]) -> dict[str, str]:
    """보고서 표기용 회사명. 후보는 크롤러가 찾은 이름, 보유 종목은 캐시된 종목 정보에서."""
    names = {str(c.get("ticker", "")).upper(): str(c.get("name", "")) for c in new_candidates if c.get("ticker")}
    client = get_stock_client()
    for ticker in tickers:
        if names.get(ticker):
            continue
        try:
            info = client.get_stock_data([ticker], period="6mo").get("stock_info", {}).get(ticker, {})
            names[ticker] = info.get("shortName") or info.get("longName") or ""
        except Exception:
            names[ticker] = ""
    return names


def _fetch_prices(tickers: list[str]) -> dict[str, float]:
    """티커별 현재가 조회. 실패한 티커는 제외(validation에서 포지션 가격으로 폴백)."""
    prices: dict[str, float] = {}
    client = get_stock_client()
    for ticker in tickers:
        try:
            prices[ticker] = float(client.get_stock_current_price([ticker])[ticker])
        except Exception as e:
            logger.warning(f"Failed to fetch current price for {ticker}: {e}")
    return prices


def build_decider_graph(llm_client):
    """LLM 클라이언트를 주입받는 decider graph 빌더"""

    def agent_wrapper(state: DeciderState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        # 이전 에이전트가 끝나지 않았으면 아무 것도 하지 않음
        if not state_get(state, "risk_end", False):
            return {}

        momo_score = state_get(state, "momo_score", [])
        fund_score = state_get(state, "fund_score", [])
        review_note = state_get(state, "review_note", {})
        new_candidates = state_get(state, "new_candidates", [])
        language = state_get(state, "language", "ko")
        market_regime = state_get(state, "market_regime", {}) or {}
        rules = regime_rules(market_regime.get("regime", "neutral"))

        prompt = DECIDER_SYSTEM_PROMPT.render(
            universe=state_get(state, "universe", []),
            asof=state_get(state, "asof", ""),
            new_candidates=new_candidates,
            momo_score=momo_score,
            fund_score=fund_score,
            review_note=review_note,
            risk_note=state_get(state, "risk_note", {}),
            market_regime=market_regime,
            buy_threshold=rules["buy_threshold"],
            candidate_buy_threshold=rules["candidate_buy_threshold"],
            cash_floor_pct=rules["cash_floor_pct"],
            language=language,
        )

        # 에이전트 생성 — LLM은 액션/목표비중/근거만 결정
        agent = create_react_agent(
            model=llm_client,
            tools=[get_current_portfolio, get_stock_data],
            name="decider",
            prompt=prompt,
            response_format=DeciderLLMOutput,
        )
        out = agent.invoke(messages=[], input=state, config=config)
        llm_decisions = extract_structured_response(out).get("decisions", [])
        if not llm_decisions:
            logger.error("Decider LLM returned no decisions")
            return {"decisions": [], "final_portfolio": {}}

        # ---- 코드 레벨 검증: 실제 포트폴리오/시세 기준으로 수량·금액·점수 재계산 ----
        try:
            user_id = get_user_id_from_config(config)
            portfolio = asyncio.run(get_portfolio_repo().get_by_user_id(user_id))
        except Exception as e:
            logger.error(f"Failed to fetch portfolio for decision validation: {e}")
            return {"decisions": [], "final_portfolio": {}}

        decision_tickers = {str(d.get("ticker", "")).upper().strip() for d in llm_decisions}
        position_tickers = {p.ticker for p in portfolio.positions}
        all_tickers = sorted((decision_tickers | position_tickers) - {""})
        prices = _fetch_prices(all_tickers)
        earnings_blackout = _fetch_earnings_blackout(all_tickers)
        company_names = _fetch_company_names(all_tickers, new_candidates)

        decisions, final_portfolio = build_validated_decisions(
            llm_decisions=llm_decisions,
            portfolio=portfolio,
            prices=prices,
            momo_by_ticker={m["ticker"]: m.get("score", {}).get("MOMO") for m in momo_score if isinstance(m, dict)},
            fund_by_ticker={f["ticker"]: f.get("FUND") for f in fund_score if isinstance(f, dict)},
            adjustment=review_note.get("adjustment", 0.0) if isinstance(review_note, dict) else 0.0,
            cash_floor_pct=rules["cash_floor_pct"],  # 국면별 현금 바닥 (코드 강제)
            earnings_blackout=earnings_blackout,  # 실적 임박 종목 매수 보류 (코드 강제)
            language=language,
            company_names=company_names,
            buy_threshold=rules["buy_threshold"],  # 점수 기준 미달 BUY 차단 (코드 강제)
            candidate_buy_threshold=rules["candidate_buy_threshold"],
        )

        return {
            "decisions": decisions,
            "final_portfolio": final_portfolio,
        }

    g = StateGraph(DeciderState)
    g.add_node("DECIDER", agent_wrapper)
    g.add_edge(START, "DECIDER")
    g.add_edge("DECIDER", END)
    return g.compile()


# ---- 부모<->자식 어댑터 ----
def adapt_parent_to_decider_in(parent) -> DeciderState:
    return {
        "universe": parent.get("universe", []),
        "new_candidates": parent.get("new_candidates", []),
        "momo_score": parent.get("momo_score", {}),
        "fund_score": parent.get("fund_score", {}),
        "review_note": parent.get("review_note", {}),
        "risk_note": parent.get("risk_note", {}),
        "market_regime": parent.get("market_regime", {}),
        "language": parent.get("language", "ko"),
        "asof": parent.get("asof"),
        "risk_end": parent.get("risk_end", False),
    }


def adapt_decider_to_parent_out(sub_out: DeciderState) -> dict:
    decisions = state_get(sub_out, "decisions")
    final_portfolio = state_get(sub_out, "final_portfolio")

    # 유효 값이 없으면 downstream 트리거를 만들지 않음
    if not decisions and not final_portfolio:
        return {}

    decisions = [d.model_dump() for d in decisions]
    if final_portfolio and hasattr(final_portfolio, "model_dump"):
        final_portfolio = final_portfolio.model_dump()
    else:
        final_portfolio = None

    return {
        "decisions": decisions,
        "final_portfolio": final_portfolio,
        "decider_end": True,
    }
