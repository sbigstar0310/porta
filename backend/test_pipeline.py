# test_pipeline.py
"""
Multi-agent pipeline 테스트 스크립트
"""

from datetime import datetime
from graph.agents.reporter.schema import ReporterState
from graph.agents.decider.schema import DeciderState
from graph.agents.risk.schema import RiskState
from graph.agents.reviewer.schema import ReviewerState
from graph.agents.fund.schema import FundState
from graph.agents.momo.schema import MomoState
from graph.agents.crawler.schema import CrawlerState
from graph.root_graph import build_root_graph
from graph.schemas import ParentState

from repo.portfolio_repo import PortfolioRepo
from schemas import PortfolioOut


def test_individual_agent(llm_client, agent_name):
    """개별 에이전트 테스트

    Args:
        llm_client: LLMClient
        agent_name: str
    """
    from graph.agents.crawler.graph import build_crawler_graph
    from graph.agents.momo.graph import build_momo_graph
    from graph.agents.fund.graph import build_fund_graph
    from graph.agents.reviewer.graph import build_reviewer_graph
    from graph.agents.risk.graph import build_risk_graph
    from graph.agents.decider.graph import build_decider_graph
    from graph.agents.reporter.graph import build_reporter_graph

    print(f"test_individual_agent: {agent_name}")

    try:
        if agent_name == "crawler":
            state_schema = CrawlerState(
                asof=datetime.utcnow().isoformat(),
                universe=["AAPL", "MSFT", "GOOGL", "NVDA"],
                new_candidates=[],
            )
            graph = build_crawler_graph(llm_client)
        elif agent_name == "momo":
            state_schema = MomoState(
                asof=datetime.utcnow().isoformat(),
                universe=["AAPL", "MSFT", "GOOGL", "NVDA"],
                new_candidates=[
                    {
                        "ticker": "AVGO",
                        "name": "Broadcom Inc.",
                        "reason": "Q2 FY2025 results: reported an earnings beat with revenue/earnings expansion driven by AI-related semiconductor and networking products (company reported AI revenue growth and management pointed to robust AI demand). Management gave strong near-term guidance and commentary about large customer engagements (press coverage cites reports of material new orders/ties to major AI customers). Technical/momentum: shares recently broke out of a trading range into new highs following the results and guidance, reflecting sector rotation into AI infrastructure names.",
                        "ref_url": [
                            "https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2025-financial",
                            "https://www.cnbc.com/2025/06/05/broadcom-avgo-earnings-report-q2-2025.html",
                            "https://www.investing.com/news/earnings/broadcom-sees-jump-in-ai-chip-revenue-amid-solid-guidance-as-q2-results-beat-4225477",
                        ],
                    },
                    {
                        "ticker": "ASML",
                        "name": "ASML Holding N.V.",
                        "reason": "Q2 2025: reported total net sales of €7.7 billion (at the upper end of guidance) and provided explicit guidance for Q3 and FY2025 indicating continued demand for lithography systems from advanced foundries. Catalyst: strong orders/shipments and conservative but solid guidance imply continued capital spending by leading customers (TSMC/other foundries). Technical/momentum: share strength in the semicap equipment cohort as investors position for another cycle of capex — ASML is a primary beneficiary.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/asml-holding-nv-asml-q2-070318442.html?fr=sycsrp_catchall",
                            "https://www.marketscreener.com/quote/stock/ASML-HOLDING-N-V-12002973/news/ASML-Holding-N-V-Provides-Earnings-Guidance-for-the-Third-Quarter-and-Full-Year-2025-50519630/",
                        ],
                    },
                    {
                        "ticker": "LRCX",
                        "name": "Lam Research Corporation",
                        "reason": "Q2 CY2025 results: revenue of ~$5.17 billion (reported July 30, 2025) and an earnings beat with EPS and revenue well ahead of prior-year levels; company raised/confirmed near-term outlook reflecting strong wafer-fab equipment demand. Catalyst: Lam is a bellwether for the semiconductor equipment cycle — outsized order flow and better-than-expected guidance indicate continued capex momentum. Technical/momentum: post-earnings breakout and leadership within semiconductor equipment names.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/lam-research-nasdaq-lrcx-reports-213228617.html?fr=sycsrp_catchall",
                            "https://investor.lamresearch.com/news-releases",
                        ],
                    },
                    {
                        "ticker": "AMAT",
                        "name": "Applied Materials, Inc.",
                        "reason": "Q2 2025 results: reported record EPS and ~7% year-over-year revenue growth (company press release), with management commentary pointing to broad demand across logic, memory and advanced packaging. Technical catalyst: noted all-time/high breakout patterns in technical scans after the earnings release (several market-data providers flagged ATH breakout). Sector rotation into semiconductor equipment names and the company's broad product footprint make AMAT a momentum candidate.",
                        "ref_url": [
                            "https://www.globenewswire.com/news-release/2025/05/15/3082633/0/en/Applied-Materials-Announces-Second-Quarter-2025-Results.html",
                            "https://in.tradingview.com/symbols/NASDAQ-AMAT/",
                        ],
                    },
                ],
                momo_score=[],
            )
            graph = build_momo_graph(llm_client)
        elif agent_name == "fund":
            state_schema = FundState(
                asof=datetime.utcnow().isoformat(),
                universe=["AAPL", "MSFT", "GOOGL", "NVDA"],
                new_candidates=[
                    {
                        "ticker": "AVGO",
                        "name": "Broadcom Inc.",
                        "reason": "Q2 FY2025 results: reported an earnings beat with revenue/earnings expansion driven by AI-related semiconductor and networking products (company reported AI revenue growth and management pointed to robust AI demand). Management gave strong near-term guidance and commentary about large customer engagements (press coverage cites reports of material new orders/ties to major AI customers). Technical/momentum: shares recently broke out of a trading range into new highs following the results and guidance, reflecting sector rotation into AI infrastructure names.",
                        "ref_url": [
                            "https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2025-financial",
                            "https://www.cnbc.com/2025/06/05/broadcom-avgo-earnings-report-q2-2025.html",
                            "https://www.investing.com/news/earnings/broadcom-sees-jump-in-ai-chip-revenue-amid-solid-guidance-as-q2-results-beat-4225477",
                        ],
                    },
                    {
                        "ticker": "ASML",
                        "name": "ASML Holding N.V.",
                        "reason": "Q2 2025: reported total net sales of €7.7 billion (at the upper end of guidance) and provided explicit guidance for Q3 and FY2025 indicating continued demand for lithography systems from advanced foundries. Catalyst: strong orders/shipments and conservative but solid guidance imply continued capital spending by leading customers (TSMC/other foundries). Technical/momentum: share strength in the semicap equipment cohort as investors position for another cycle of capex — ASML is a primary beneficiary.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/asml-holding-nv-asml-q2-070318442.html?fr=sycsrp_catchall",
                            "https://www.marketscreener.com/quote/stock/ASML-HOLDING-N-V-12002973/news/ASML-Holding-N-V-Provides-Earnings-Guidance-for-the-Third-Quarter-and-Full-Year-2025-50519630/",
                        ],
                    },
                    {
                        "ticker": "LRCX",
                        "name": "Lam Research Corporation",
                        "reason": "Q2 CY2025 results: revenue of ~$5.17 billion (reported July 30, 2025) and an earnings beat with EPS and revenue well ahead of prior-year levels; company raised/confirmed near-term outlook reflecting strong wafer-fab equipment demand. Catalyst: Lam is a bellwether for the semiconductor equipment cycle — outsized order flow and better-than-expected guidance indicate continued capex momentum. Technical/momentum: post-earnings breakout and leadership within semiconductor equipment names.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/lam-research-nasdaq-lrcx-reports-213228617.html?fr=sycsrp_catchall",
                            "https://investor.lamresearch.com/news-releases",
                        ],
                    },
                    {
                        "ticker": "AMAT",
                        "name": "Applied Materials, Inc.",
                        "reason": "Q2 2025 results: reported record EPS and ~7% year-over-year revenue growth (company press release), with management commentary pointing to broad demand across logic, memory and advanced packaging. Technical catalyst: noted all-time/high breakout patterns in technical scans after the earnings release (several market-data providers flagged ATH breakout). Sector rotation into semiconductor equipment names and the company's broad product footprint make AMAT a momentum candidate.",
                        "ref_url": [
                            "https://www.globenewswire.com/news-release/2025/05/15/3082633/0/en/Applied-Materials-Announces-Second-Quarter-2025-Results.html",
                            "https://in.tradingview.com/symbols/NASDAQ-AMAT/",
                        ],
                    },
                ],
                fund_score=[],
            )
            graph = build_fund_graph(llm_client)
        elif agent_name == "reviewer":
            state_schema = ReviewerState(
                user_id=1,
                asof=datetime.utcnow().isoformat(),
                review_note=None,
            )
            graph = build_reviewer_graph(llm_client)
        elif agent_name == "risk":
            state_schema = RiskState(
                asof=datetime.utcnow().isoformat(),
                universe=["AAPL", "MSFT", "GOOGL", "NVDA"],
                new_candidates=[
                    {
                        "ticker": "AVGO",
                        "name": "Broadcom Inc.",
                        "reason": "Q2 FY2025 results: reported an earnings beat with revenue/earnings expansion driven by AI-related semiconductor and networking products (company reported AI revenue growth and management pointed to robust AI demand). Management gave strong near-term guidance and commentary about large customer engagements (press coverage cites reports of material new orders/ties to major AI customers). Technical/momentum: shares recently broke out of a trading range into new highs following the results and guidance, reflecting sector rotation into AI infrastructure names.",
                        "ref_url": [
                            "https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2025-financial",
                            "https://www.cnbc.com/2025/06/05/broadcom-avgo-earnings-report-q2-2025.html",
                            "https://www.investing.com/news/earnings/broadcom-sees-jump-in-ai-chip-revenue-amid-solid-guidance-as-q2-results-beat-4225477",
                        ],
                    },
                    {
                        "ticker": "ASML",
                        "name": "ASML Holding N.V.",
                        "reason": "Q2 2025: reported total net sales of €7.7 billion (at the upper end of guidance) and provided explicit guidance for Q3 and FY2025 indicating continued demand for lithography systems from advanced foundries. Catalyst: strong orders/shipments and conservative but solid guidance imply continued capital spending by leading customers (TSMC/other foundries). Technical/momentum: share strength in the semicap equipment cohort as investors position for another cycle of capex — ASML is a primary beneficiary.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/asml-holding-nv-asml-q2-070318442.html?fr=sycsrp_catchall",
                            "https://www.marketscreener.com/quote/stock/ASML-HOLDING-N-V-12002973/news/ASML-Holding-N-V-Provides-Earnings-Guidance-for-the-Third-Quarter-and-Full-Year-2025-50519630/",
                        ],
                    },
                    {
                        "ticker": "LRCX",
                        "name": "Lam Research Corporation",
                        "reason": "Q2 CY2025 results: revenue of ~$5.17 billion (reported July 30, 2025) and an earnings beat with EPS and revenue well ahead of prior-year levels; company raised/confirmed near-term outlook reflecting strong wafer-fab equipment demand. Catalyst: Lam is a bellwether for the semiconductor equipment cycle — outsized order flow and better-than-expected guidance indicate continued capex momentum. Technical/momentum: post-earnings breakout and leadership within semiconductor equipment names.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/lam-research-nasdaq-lrcx-reports-213228617.html?fr=sycsrp_catchall",
                            "https://investor.lamresearch.com/news-releases",
                        ],
                    },
                    {
                        "ticker": "AMAT",
                        "name": "Applied Materials, Inc.",
                        "reason": "Q2 2025 results: reported record EPS and ~7% year-over-year revenue growth (company press release), with management commentary pointing to broad demand across logic, memory and advanced packaging. Technical catalyst: noted all-time/high breakout patterns in technical scans after the earnings release (several market-data providers flagged ATH breakout). Sector rotation into semiconductor equipment names and the company's broad product footprint make AMAT a momentum candidate.",
                        "ref_url": [
                            "https://www.globenewswire.com/news-release/2025/05/15/3082633/0/en/Applied-Materials-Announces-Second-Quarter-2025-Results.html",
                            "https://in.tradingview.com/symbols/NASDAQ-AMAT/",
                        ],
                    },
                ],
                momo_score=[
                    {
                        "ticker": "AAPL",
                        "score": {
                            "MOMO": 53,
                            "features": {
                                "r20": 0.041553,
                                "r60": 0.189199,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 1.022169,
                                "atr_pct_14": 0.016491,
                            },
                            "norm": {"z20": 0.11, "z60": 0.31, "zvol": 0.05},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "MSFT",
                        "score": {
                            "MOMO": 42,
                            "features": {
                                "r20": -0.040609,
                                "r60": 0.045339,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 0.820368,
                                "atr_pct_14": 0.014100,
                            },
                            "norm": {"z20": -0.74, "z60": -0.73, "zvol": -0.62},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "GOOGL",
                        "score": {
                            "MOMO": 70,
                            "features": {
                                "r20": 0.178117,
                                "r60": 0.347761,
                                "ma_cross": "true",
                                "breakout": "true",
                                "vol_surge": 1.402455,
                                "atr_pct_14": 0.025004,
                            },
                            "norm": {"z20": 1.53, "z60": 1.46, "zvol": 1.31},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "NVDA",
                        "score": {
                            "MOMO": 44,
                            "features": {
                                "r20": -0.080166,
                                "r60": 0.154931,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 0.844478,
                                "atr_pct_14": 0.030898,
                            },
                            "norm": {"z20": -1.15, "z60": 0.06, "zvol": -0.54},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "AVGO",
                        "score": {
                            "MOMO": 67,
                            "features": {
                                "r20": 0.124019,
                                "r60": 0.337109,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 1.572888,
                                "atr_pct_14": 0.038488,
                            },
                            "norm": {"z20": 0.97, "z60": 1.39, "zvol": 1.87},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "ASML",
                        "score": {
                            "MOMO": 48,
                            "features": {
                                "r20": 0.104643,
                                "r60": 0.013457,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 1.002385,
                                "atr_pct_14": 0.021440,
                            },
                            "norm": {"z20": 0.77, "z60": -0.97, "zvol": -0.02},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "LRCX",
                        "score": {
                            "MOMO": 46,
                            "features": {
                                "r20": 0.029461,
                                "r60": 0.148443,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 0.688528,
                                "atr_pct_14": 0.029046,
                            },
                            "norm": {"z20": -0.01, "z60": 0.02, "zvol": -1.06},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "AMAT",
                        "score": {
                            "MOMO": 31,
                            "features": {
                                "r20": -0.112960,
                                "r60": -0.065415,
                                "ma_cross": "false",
                                "breakout": "false",
                                "vol_surge": 0.705856,
                                "atr_pct_14": 0.021206,
                            },
                            "norm": {"z20": -1.49, "z60": -1.54, "zvol": -1.0},
                            "data_confidence": "high",
                        },
                    },
                ],
                fund_score=[
                    {
                        "ticker": "AAPL",
                        "FUND": 50,
                        "scores": {"V": 15, "G": 50, "Q": 80, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Valuation is stretched (P/E ~35.9, EV/Sales ~8.8) which limits upside vs peers.",
                            "Very strong profitability and capital returns (ROE elevated, operating margin ~30%).",
                            "Growth has moderated (mid-single-digit revenue deceleration vs prior periods).",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "MSFT",
                        "FUND": 68,
                        "scores": {"V": 15, "G": 95, "Q": 95, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Premium multiple (P/E ~36.6) but supported by robust top-line and EPS growth (revenue growth ~18% and strong earnings expansion).",
                            "High-quality business metrics: strong ROE (~33%), excellent margins (~45%).",
                            "Analyst sentiment and forward estimates remain favorable—growth and quality offset valuation compression risk.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "GOOGL",
                        "FUND": 69,
                        "scores": {"V": 40, "G": 70, "Q": 100, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Very high-quality franchise: strong ROE (~34.8%) and healthy operating margins (~32%).",
                            "Solid earnings and revenue growth (EPS growth ~22%), with constructive analyst revisions.",
                            "Valuation appears reasonable on some metrics (P/B ~7.9) vs growth/quality profile.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "NVDA",
                        "FUND": 69,
                        "scores": {"V": 15, "G": 95, "Q": 100, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Exceptional growth and profitability (revenue growth ~55.6%, operating margin ~60.8%), driving high quality scores.",
                            "Valuation is very rich (P/E ~47.5, EV/Sales ~24.5), increasing sensitivity to execution and macro risks.",
                            "Strong analyst sentiment and recurring earnings beats support the premium multiple.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "AVGO",
                        "FUND": 70,
                        "scores": {"V": 35, "G": 95, "Q": 80, "E": 75},
                        "label": "Strong",
                        "insights": [
                            "Robust growth driven by AI-related chip and networking demand (strong Q2 FY2025 results and bullish guidance).",
                            "High earnings growth and solid margins/ROE support a strong fundamental profile despite a high P/E (~87).",
                            "Mixed valuation signals: elevated P/E but relatively low EV/Sales (~2.9) — market pricing reflects growth and strategic customer wins.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "ASML",
                        "FUND": 73,
                        "scores": {"V": 30, "G": 95, "Q": 100, "E": 75},
                        "label": "Strong",
                        "insights": [
                            "Clear beneficiary of semiconductor capex cycle: strong orders/shipments and guidance (Q2 net sales ~€7.7bn).",
                            "Exceptional quality metrics (high ROE, robust operating margins) and consistent earnings beats.",
                            "Valuation rich on some multiples (P/B and EV/Sales elevated) but justified by durable structural demand from leading foundries.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "LRCX",
                        "FUND": 75,
                        "scores": {"V": 40, "G": 95, "Q": 95, "E": 75},
                        "label": "Strong",
                        "insights": [
                            "Bellwether for the wafer-fab equipment cycle — strong Q2 CY2025 beats and raised/confirmed outlook indicate sustained capex momentum.",
                            "High revenue and earnings growth (double-digit/low double-digit+ growth) with excellent ROE and margins.",
                            "Valuation sits in a moderate range relative to the growth profile (supportive technical momentum post-earnings).",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "AMAT",
                        "FUND": 62,
                        "scores": {"V": 40, "G": 50, "Q": 95, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Record EPS and broad demand across logic, memory and advanced packaging underpin fundamentals (solid margins, ROE ~35.6%).",
                            "Revenue growth is positive but more moderate (~7% YoY), making valuation/growth trade-offs important.",
                            "High-quality operations and cash generation support a favorable risk profile despite a less aggressive growth score.",
                        ],
                        "data_confidence": "high",
                    },
                ],
                risk_note=None,
            )
            graph = build_risk_graph(llm_client)
        elif agent_name == "decider":
            state_schema = DeciderState(
                asof=datetime.utcnow().isoformat(),
                universe=["AAPL", "MSFT", "GOOGL", "NVDA"],
                new_candidates=[
                    {
                        "ticker": "AVGO",
                        "name": "Broadcom Inc.",
                        "reason": "Q2 FY2025 results: reported an earnings beat with revenue/earnings expansion driven by AI-related semiconductor and networking products (company reported AI revenue growth and management pointed to robust AI demand). Management gave strong near-term guidance and commentary about large customer engagements (press coverage cites reports of material new orders/ties to major AI customers). Technical/momentum: shares recently broke out of a trading range into new highs following the results and guidance, reflecting sector rotation into AI infrastructure names.",
                        "ref_url": [
                            "https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2025-financial",
                            "https://www.cnbc.com/2025/06/05/broadcom-avgo-earnings-report-q2-2025.html",
                            "https://www.investing.com/news/earnings/broadcom-sees-jump-in-ai-chip-revenue-amid-solid-guidance-as-q2-results-beat-4225477",
                        ],
                    },
                    {
                        "ticker": "ASML",
                        "name": "ASML Holding N.V.",
                        "reason": "Q2 2025: reported total net sales of €7.7 billion (at the upper end of guidance) and provided explicit guidance for Q3 and FY2025 indicating continued demand for lithography systems from advanced foundries. Catalyst: strong orders/shipments and conservative but solid guidance imply continued capital spending by leading customers (TSMC/other foundries). Technical/momentum: share strength in the semicap equipment cohort as investors position for another cycle of capex — ASML is a primary beneficiary.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/asml-holding-nv-asml-q2-070318442.html?fr=sycsrp_catchall",
                            "https://www.marketscreener.com/quote/stock/ASML-HOLDING-N-V-12002973/news/ASML-Holding-N-V-Provides-Earnings-Guidance-for-the-Third-Quarter-and-Full-Year-2025-50519630/",
                        ],
                    },
                    {
                        "ticker": "LRCX",
                        "name": "Lam Research Corporation",
                        "reason": "Q2 CY2025 results: revenue of ~$5.17 billion (reported July 30, 2025) and an earnings beat with EPS and revenue well ahead of prior-year levels; company raised/confirmed near-term outlook reflecting strong wafer-fab equipment demand. Catalyst: Lam is a bellwether for the semiconductor equipment cycle — outsized order flow and better-than-expected guidance indicate continued capex momentum. Technical/momentum: post-earnings breakout and leadership within semiconductor equipment names.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/lam-research-nasdaq-lrcx-reports-213228617.html?fr=sycsrp_catchall",
                            "https://investor.lamresearch.com/news-releases",
                        ],
                    },
                    {
                        "ticker": "AMAT",
                        "name": "Applied Materials, Inc.",
                        "reason": "Q2 2025 results: reported record EPS and ~7% year-over-year revenue growth (company press release), with management commentary pointing to broad demand across logic, memory and advanced packaging. Technical catalyst: noted all-time/high breakout patterns in technical scans after the earnings release (several market-data providers flagged ATH breakout). Sector rotation into semiconductor equipment names and the company's broad product footprint make AMAT a momentum candidate.",
                        "ref_url": [
                            "https://www.globenewswire.com/news-release/2025/05/15/3082633/0/en/Applied-Materials-Announces-Second-Quarter-2025-Results.html",
                            "https://in.tradingview.com/symbols/NASDAQ-AMAT/",
                        ],
                    },
                ],
                momo_score=[
                    {
                        "ticker": "AAPL",
                        "score": {
                            "MOMO": 53,
                            "features": {
                                "r20": 0.041553,
                                "r60": 0.189199,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 1.022169,
                                "atr_pct_14": 0.016491,
                            },
                            "norm": {"z20": 0.11, "z60": 0.31, "zvol": 0.05},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "MSFT",
                        "score": {
                            "MOMO": 42,
                            "features": {
                                "r20": -0.040609,
                                "r60": 0.045339,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 0.820368,
                                "atr_pct_14": 0.014100,
                            },
                            "norm": {"z20": -0.74, "z60": -0.73, "zvol": -0.62},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "GOOGL",
                        "score": {
                            "MOMO": 70,
                            "features": {
                                "r20": 0.178117,
                                "r60": 0.347761,
                                "ma_cross": "true",
                                "breakout": "true",
                                "vol_surge": 1.402455,
                                "atr_pct_14": 0.025004,
                            },
                            "norm": {"z20": 1.53, "z60": 1.46, "zvol": 1.31},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "NVDA",
                        "score": {
                            "MOMO": 44,
                            "features": {
                                "r20": -0.080166,
                                "r60": 0.154931,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 0.844478,
                                "atr_pct_14": 0.030898,
                            },
                            "norm": {"z20": -1.15, "z60": 0.06, "zvol": -0.54},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "AVGO",
                        "score": {
                            "MOMO": 67,
                            "features": {
                                "r20": 0.124019,
                                "r60": 0.337109,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 1.572888,
                                "atr_pct_14": 0.038488,
                            },
                            "norm": {"z20": 0.97, "z60": 1.39, "zvol": 1.87},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "ASML",
                        "score": {
                            "MOMO": 48,
                            "features": {
                                "r20": 0.104643,
                                "r60": 0.013457,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 1.002385,
                                "atr_pct_14": 0.021440,
                            },
                            "norm": {"z20": 0.77, "z60": -0.97, "zvol": -0.02},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "LRCX",
                        "score": {
                            "MOMO": 46,
                            "features": {
                                "r20": 0.029461,
                                "r60": 0.148443,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 0.688528,
                                "atr_pct_14": 0.029046,
                            },
                            "norm": {"z20": -0.01, "z60": 0.02, "zvol": -1.06},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "AMAT",
                        "score": {
                            "MOMO": 31,
                            "features": {
                                "r20": -0.112960,
                                "r60": -0.065415,
                                "ma_cross": "false",
                                "breakout": "false",
                                "vol_surge": 0.705856,
                                "atr_pct_14": 0.021206,
                            },
                            "norm": {"z20": -1.49, "z60": -1.54, "zvol": -1.0},
                            "data_confidence": "high",
                        },
                    },
                ],
                fund_score=[
                    {
                        "ticker": "AAPL",
                        "FUND": 50,
                        "scores": {"V": 15, "G": 50, "Q": 80, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Valuation is stretched (P/E ~35.9, EV/Sales ~8.8) which limits upside vs peers.",
                            "Very strong profitability and capital returns (ROE elevated, operating margin ~30%).",
                            "Growth has moderated (mid-single-digit revenue deceleration vs prior periods).",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "MSFT",
                        "FUND": 68,
                        "scores": {"V": 15, "G": 95, "Q": 95, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Premium multiple (P/E ~36.6) but supported by robust top-line and EPS growth (revenue growth ~18% and strong earnings expansion).",
                            "High-quality business metrics: strong ROE (~33%), excellent margins (~45%).",
                            "Analyst sentiment and forward estimates remain favorable—growth and quality offset valuation compression risk.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "GOOGL",
                        "FUND": 69,
                        "scores": {"V": 40, "G": 70, "Q": 100, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Very high-quality franchise: strong ROE (~34.8%) and healthy operating margins (~32%).",
                            "Solid earnings and revenue growth (EPS growth ~22%), with constructive analyst revisions.",
                            "Valuation appears reasonable on some metrics (P/B ~7.9) vs growth/quality profile.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "NVDA",
                        "FUND": 69,
                        "scores": {"V": 15, "G": 95, "Q": 100, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Exceptional growth and profitability (revenue growth ~55.6%, operating margin ~60.8%), driving high quality scores.",
                            "Valuation is very rich (P/E ~47.5, EV/Sales ~24.5), increasing sensitivity to execution and macro risks.",
                            "Strong analyst sentiment and recurring earnings beats support the premium multiple.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "AVGO",
                        "FUND": 70,
                        "scores": {"V": 35, "G": 95, "Q": 80, "E": 75},
                        "label": "Strong",
                        "insights": [
                            "Robust growth driven by AI-related chip and networking demand (strong Q2 FY2025 results and bullish guidance).",
                            "High earnings growth and solid margins/ROE support a strong fundamental profile despite a high P/E (~87).",
                            "Mixed valuation signals: elevated P/E but relatively low EV/Sales (~2.9) — market pricing reflects growth and strategic customer wins.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "ASML",
                        "FUND": 73,
                        "scores": {"V": 30, "G": 95, "Q": 100, "E": 75},
                        "label": "Strong",
                        "insights": [
                            "Clear beneficiary of semiconductor capex cycle: strong orders/shipments and guidance (Q2 net sales ~€7.7bn).",
                            "Exceptional quality metrics (high ROE, robust operating margins) and consistent earnings beats.",
                            "Valuation rich on some multiples (P/B and EV/Sales elevated) but justified by durable structural demand from leading foundries.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "LRCX",
                        "FUND": 75,
                        "scores": {"V": 40, "G": 95, "Q": 95, "E": 75},
                        "label": "Strong",
                        "insights": [
                            "Bellwether for the wafer-fab equipment cycle — strong Q2 CY2025 beats and raised/confirmed outlook indicate sustained capex momentum.",
                            "High revenue and earnings growth (double-digit/low double-digit+ growth) with excellent ROE and margins.",
                            "Valuation sits in a moderate range relative to the growth profile (supportive technical momentum post-earnings).",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "AMAT",
                        "FUND": 62,
                        "scores": {"V": 40, "G": 50, "Q": 95, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Record EPS and broad demand across logic, memory and advanced packaging underpin fundamentals (solid margins, ROE ~35.6%).",
                            "Revenue growth is positive but more moderate (~7% YoY), making valuation/growth trade-offs important.",
                            "High-quality operations and cash generation support a favorable risk profile despite a less aggressive growth score.",
                        ],
                        "data_confidence": "high",
                    },
                ],
                review_note={
                    "period": "2025-09-01...2025-09-08",
                    "opinion": "Insufficient historical data for meaningful performance review. Default to balanced approach.",
                    "preference": "balanced",
                    "adjustment": 0.0,
                },
                risk_note={
                    "per_ticker": [
                        {
                            "ticker": "AAPL",
                            "allowed": "true",
                            "max_weight_pct": 9.02,
                            "notes": [
                                "Liquidity: ADV ≈ $12.8B (ample)",
                                "Volatility: ATR% ≈ 1.65% (passes ≤6% filter)",
                                "Beta: 1.109 (normal)",
                            ],
                            "beta": 1.109,
                            "atr_pct": 1.651211990051754,
                        },
                        {
                            "ticker": "MSFT",
                            "allowed": "true",
                            "max_weight_pct": 9.62,
                            "notes": [
                                "Liquidity: ADV ≈ $10.1B (ample)",
                                "Volatility: ATR% ≈ 1.41% (passes ≤6% filter)",
                                "Beta: 1.04 (normal)",
                            ],
                            "beta": 1.04,
                            "atr_pct": 1.4112231869381413,
                        },
                        {
                            "ticker": "GOOGL",
                            "allowed": "true",
                            "max_weight_pct": 9.89,
                            "notes": [
                                "Liquidity: ADV ≈ $9.1B (ample)",
                                "Volatility: ATR% ≈ 2.50% (passes ≤6% filter)",
                                "Sector: Communication Services (helps diversify away from Technology)",
                            ],
                            "beta": 1.011,
                            "atr_pct": 2.5016210089038503,
                        },
                        {
                            "ticker": "NVDA",
                            "allowed": "true",
                            "max_weight_pct": 4.76,
                            "notes": [
                                "Liquidity: ADV ≈ $29.1B (ample)",
                                "Volatility: ATR% ≈ 3.09% (passes ≤6% filter)",
                                "High beta: 2.102 → beta-adjusted cap (reduced exposure)",
                            ],
                            "beta": 2.102,
                            "atr_pct": 3.092351569541264,
                        },
                        {
                            "ticker": "AVGO",
                            "allowed": "true",
                            "max_weight_pct": 8.53,
                            "notes": [
                                "Liquidity: ADV ≈ $7.1B (ample)",
                                "Volatility: ATR% ≈ 3.87% (passes ≤6% filter)",
                                "Earnings: last reported 2025-09-05 (outside 3-day post-earnings restriction)",
                                "Beta: 1.172 (moderate)",
                            ],
                            "beta": 1.172,
                            "atr_pct": 3.8653280552121146,
                        },
                        {
                            "ticker": "ASML",
                            "allowed": "true",
                            "max_weight_pct": 8.01,
                            "notes": [
                                "Liquidity: ADV ≈ $1.40B (ample, NY-listed ADR liquidity acceptable)",
                                "Volatility: ATR% ≈ 2.14% (passes ≤6% filter)",
                                "Beta: 1.249 (moderate)",
                            ],
                            "beta": 1.249,
                            "atr_pct": 2.1448304541773162,
                        },
                        {
                            "ticker": "LRCX",
                            "allowed": "true",
                            "max_weight_pct": 5.65,
                            "notes": [
                                "Liquidity: ADV ≈ $1.14B (ample)",
                                "Volatility: ATR% ≈ 2.91% (passes ≤6% filter)",
                                "High beta: 1.77 → beta-adjusted cap (reduced exposure)",
                            ],
                            "beta": 1.77,
                            "atr_pct": 2.907253527357254,
                        },
                        {
                            "ticker": "AMAT",
                            "allowed": "true",
                            "max_weight_pct": 5.68,
                            "notes": [
                                "Liquidity: ADV ≈ $1.17B (ample)",
                                "Volatility: ATR% ≈ 2.12% (passes ≤6% filter)",
                                "High beta: 1.762 → beta-adjusted cap (reduced exposure)",
                            ],
                            "beta": 1.762,
                            "atr_pct": 2.123962349020731,
                        },
                    ],
                    "portfolio_limits": {
                        "single_stock_cap": 15.0,
                        "sector_caps": [
                            {"sector": "Technology", "cap": 35.0},
                            {"sector": "Communication Services", "cap": 35.0},
                        ],
                        "cash_floor": 5.0,
                    },
                    "portfolio_warnings": [
                        {"type": "sector_concentration", "sector": "Technology", "actual": 56.99, "limit": 35.0}
                    ],
                    "overall_note": "All tickers pass the volatility (ATR% ≤6%) and liquidity (ADV ≥ $5M) filters. High-beta names (NVDA, LRCX, AMAT) receive reduced maximum weights per the beta adjustment—this is reflected in the calculated max_weight_pct values (conservative sizing). Portfolio is materially overweight Technology (~57% vs 35% cap) — recommend trimming Technology exposure or limiting new additions from the sector until sector weight is reduced toward the 35% cap. Cash currently ≈9.45% (meets ≥5% cash floor). Maintain conservative bias: prioritize purchases in non-Technology/Communication Services or reduce position sizes for high-beta semicap names.",
                },
            )
            graph = build_decider_graph(llm_client)
        elif agent_name == "reporter":
            state_schema = ReporterState(
                asof=datetime.utcnow().isoformat(),
                universe=["AAPL", "MSFT", "GOOGL", "NVDA"],
                new_candidates=[
                    {
                        "ticker": "AVGO",
                        "name": "Broadcom Inc.",
                        "reason": "Q2 FY2025 results: reported an earnings beat with revenue/earnings expansion driven by AI-related semiconductor and networking products (company reported AI revenue growth and management pointed to robust AI demand). Management gave strong near-term guidance and commentary about large customer engagements (press coverage cites reports of material new orders/ties to major AI customers). Technical/momentum: shares recently broke out of a trading range into new highs following the results and guidance, reflecting sector rotation into AI infrastructure names.",
                        "ref_url": [
                            "https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2025-financial",
                            "https://www.cnbc.com/2025/06/05/broadcom-avgo-earnings-report-q2-2025.html",
                            "https://www.investing.com/news/earnings/broadcom-sees-jump-in-ai-chip-revenue-amid-solid-guidance-as-q2-results-beat-4225477",
                        ],
                    },
                    {
                        "ticker": "ASML",
                        "name": "ASML Holding N.V.",
                        "reason": "Q2 2025: reported total net sales of €7.7 billion (at the upper end of guidance) and provided explicit guidance for Q3 and FY2025 indicating continued demand for lithography systems from advanced foundries. Catalyst: strong orders/shipments and conservative but solid guidance imply continued capital spending by leading customers (TSMC/other foundries). Technical/momentum: share strength in the semicap equipment cohort as investors position for another cycle of capex — ASML is a primary beneficiary.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/asml-holding-nv-asml-q2-070318442.html?fr=sycsrp_catchall",
                            "https://www.marketscreener.com/quote/stock/ASML-HOLDING-N-V-12002973/news/ASML-Holding-N-V-Provides-Earnings-Guidance-for-the-Third-Quarter-and-Full-Year-2025-50519630/",
                        ],
                    },
                    {
                        "ticker": "LRCX",
                        "name": "Lam Research Corporation",
                        "reason": "Q2 CY2025 results: revenue of ~$5.17 billion (reported July 30, 2025) and an earnings beat with EPS and revenue well ahead of prior-year levels; company raised/confirmed near-term outlook reflecting strong wafer-fab equipment demand. Catalyst: Lam is a bellwether for the semiconductor equipment cycle — outsized order flow and better-than-expected guidance indicate continued capex momentum. Technical/momentum: post-earnings breakout and leadership within semiconductor equipment names.",
                        "ref_url": [
                            "https://finance.yahoo.com/news/lam-research-nasdaq-lrcx-reports-213228617.html?fr=sycsrp_catchall",
                            "https://investor.lamresearch.com/news-releases",
                        ],
                    },
                    {
                        "ticker": "AMAT",
                        "name": "Applied Materials, Inc.",
                        "reason": "Q2 2025 results: reported record EPS and ~7% year-over-year revenue growth (company press release), with management commentary pointing to broad demand across logic, memory and advanced packaging. Technical catalyst: noted all-time/high breakout patterns in technical scans after the earnings release (several market-data providers flagged ATH breakout). Sector rotation into semiconductor equipment names and the company's broad product footprint make AMAT a momentum candidate.",
                        "ref_url": [
                            "https://www.globenewswire.com/news-release/2025/05/15/3082633/0/en/Applied-Materials-Announces-Second-Quarter-2025-Results.html",
                            "https://in.tradingview.com/symbols/NASDAQ-AMAT/",
                        ],
                    },
                ],
                decisions=[
                    {
                        "ticker": "AAPL",
                        "action": "TRIM",
                        "target_weight_pct": 9.02,
                        "current_weight_pct": 22.33,
                        "shares_to_trade": -5.96,
                        "trade_value": -1407.78,
                        "total_score": 51.65,
                        "momo_score": 53,
                        "fund_score": 50,
                        "reason": "Combined score (51.65) implies HOLD by model, but portfolio is materially overweight Technology and AAPL exceeds the Risk Manager max_weight_pct (9.02%). Trim to risk-approved max to reduce sector concentration and restore compliance.",
                        "risk_notes": [
                            "Currently overweight vs per-ticker max (current 22.33% > allowed 9.02%)",
                            "Technology sector concentration is elevated vs 35% cap",
                            "Post-trim will increase cash buffer while keeping ATR and liquidity limits satisfied",
                        ],
                    },
                    {
                        "ticker": "MSFT",
                        "action": "TRIM",
                        "target_weight_pct": 9.62,
                        "current_weight_pct": 18.89,
                        "shares_to_trade": -1.96,
                        "trade_value": -981.60,
                        "total_score": 53.7,
                        "momo_score": 42,
                        "fund_score": 68,
                        "reason": "Model TOTAL (53.7) => HOLD, but MSFT position exceeds the Risk Manager per-ticker cap (9.62%). Trim to the allowed maximum to reduce Technology concentration and align with risk limits.",
                        "risk_notes": [
                            "Current weight (18.89%) > allowed max (9.62%) — trimming required",
                            "Liquidity and ATR pass filters; trimming is for risk/sector compliance",
                        ],
                    },
                    {
                        "ticker": "GOOGL",
                        "action": "TRIM",
                        "target_weight_pct": 9.89,
                        "current_weight_pct": 33.48,
                        "shares_to_trade": -10.57,
                        "trade_value": -2496.70,
                        "total_score": 69.55,
                        "momo_score": 70,
                        "fund_score": 69,
                        "reason": "TOTAL ~69.6 (just below buy threshold). GOOGL is currently the largest single position and exceeds the Risk Manager max (9.89%). Trim to the allowed max to address sector/position concentration while retaining exposure given strong MOMO/FUND signals.",
                        "risk_notes": [
                            "Current weight (33.48%) significantly > allowed max (9.89%) — trim required",
                            "GOOGL is Communication Services (helps diversify away from Tech) but position size still violates per-ticker cap",
                            "Post-trim cash increase helps keep cushion above 5% cash floor",
                        ],
                    },
                    {
                        "ticker": "NVDA",
                        "action": "TRIM",
                        "target_weight_pct": 4.76,
                        "current_weight_pct": 15.85,
                        "shares_to_trade": -6.99,
                        "trade_value": -1172.30,
                        "total_score": 55.25,
                        "momo_score": 44,
                        "fund_score": 69,
                        "reason": "TOTAL (55.25) => HOLD by model. NVDA is high-beta and the Risk Manager enforces a reduced max weight (4.76%). Trim NVDA to its beta-adjusted maximum to reduce single-name and sector risk.",
                        "risk_notes": [
                            "High beta (2.102) → reduced max weight (4.76%); current 15.85% exceeds allowed",
                            "Volatility and liquidity pass filters, but position size must be reduced per risk policy",
                        ],
                    },
                    {
                        "ticker": "AVGO",
                        "action": "NO_ACTION",
                        "target_weight_pct": 0.0,
                        "current_weight_pct": 0.0,
                        "shares_to_trade": 0.0,
                        "trade_value": 0.0,
                        "total_score": 68.35,
                        "momo_score": 67,
                        "fund_score": 70,
                        "reason": "Strong fundamental and momentum signals (TOTAL 68.35) but below the BUY threshold (≥70). In addition, the portfolio is currently overweight Technology; Risk Manager recommends limiting new Technology additions until sector weight is reduced. No purchase at this time.",
                        "risk_notes": [
                            "TOTAL < 70 → per-decision rule: do not BUY candidate",
                            "Portfolio Technology concentration (≈57%) exceeds sector cap (35%); prioritize trimming before new Tech purchases",
                            "AVGO passes liquidity/volatility filters but wait until sector exposure is reduced",
                        ],
                    },
                    {
                        "ticker": "ASML",
                        "action": "NO_ACTION",
                        "target_weight_pct": 0.0,
                        "current_weight_pct": 0.0,
                        "shares_to_trade": 0.0,
                        "trade_value": 0.0,
                        "total_score": 59.25,
                        "momo_score": 48,
                        "fund_score": 73,
                        "reason": "TOTAL (59.25) below the candidate BUY threshold of 70. Given current Technology sector overweight, defer adding ASML despite favorable fundamentals.",
                        "risk_notes": [
                            "Candidate TOTAL < 70 → no BUY",
                            "ASML is Technology sector — new purchases discouraged until sector weight reduced",
                            "ASML passes liquidity/volatility filters but wait for rebalancing",
                        ],
                    },
                    {
                        "ticker": "LRCX",
                        "action": "NO_ACTION",
                        "target_weight_pct": 0.0,
                        "current_weight_pct": 0.0,
                        "shares_to_trade": 0.0,
                        "trade_value": 0.0,
                        "total_score": 59.05,
                        "momo_score": 46,
                        "fund_score": 75,
                        "reason": "TOTAL (59.05) < 70 so not eligible for BUY as a new candidate. Defer adding Lam Research until after rebalancing — Risk Manager prefers reducing Technology concentration first.",
                        "risk_notes": [
                            "TOTAL < 70 → no BUY signal for new candidate",
                            "LRCX is semiconductor equipment (Technology) and the portfolio is currently overweight in Technology",
                        ],
                    },
                    {
                        "ticker": "AMAT",
                        "action": "NO_ACTION",
                        "target_weight_pct": 0.0,
                        "current_weight_pct": 0.0,
                        "shares_to_trade": 0.0,
                        "trade_value": 0.0,
                        "total_score": 44.95,
                        "momo_score": 31,
                        "fund_score": 62,
                        "reason": "TOTAL (44.95) is below both the BUY threshold for candidates and below HOLD for existing positions. No action on this candidate. Given overall sector constraints, avoid adding AMAT.",
                        "risk_notes": [
                            "TOTAL < 70 → no BUY",
                            "Lower momentum score reduces conviction; portfolio rebalancing is higher priority",
                        ],
                    },
                ],
                momo_score=[
                    {
                        "ticker": "AAPL",
                        "score": {
                            "MOMO": 53,
                            "features": {
                                "r20": 0.041553,
                                "r60": 0.189199,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 1.022169,
                                "atr_pct_14": 0.016491,
                            },
                            "norm": {"z20": 0.11, "z60": 0.31, "zvol": 0.05},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "MSFT",
                        "score": {
                            "MOMO": 42,
                            "features": {
                                "r20": -0.040609,
                                "r60": 0.045339,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 0.820368,
                                "atr_pct_14": 0.014100,
                            },
                            "norm": {"z20": -0.74, "z60": -0.73, "zvol": -0.62},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "GOOGL",
                        "score": {
                            "MOMO": 70,
                            "features": {
                                "r20": 0.178117,
                                "r60": 0.347761,
                                "ma_cross": "true",
                                "breakout": "true",
                                "vol_surge": 1.402455,
                                "atr_pct_14": 0.025004,
                            },
                            "norm": {"z20": 1.53, "z60": 1.46, "zvol": 1.31},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "NVDA",
                        "score": {
                            "MOMO": 44,
                            "features": {
                                "r20": -0.080166,
                                "r60": 0.154931,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 0.844478,
                                "atr_pct_14": 0.030898,
                            },
                            "norm": {"z20": -1.15, "z60": 0.06, "zvol": -0.54},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "AVGO",
                        "score": {
                            "MOMO": 67,
                            "features": {
                                "r20": 0.124019,
                                "r60": 0.337109,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 1.572888,
                                "atr_pct_14": 0.038488,
                            },
                            "norm": {"z20": 0.97, "z60": 1.39, "zvol": 1.87},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "ASML",
                        "score": {
                            "MOMO": 48,
                            "features": {
                                "r20": 0.104643,
                                "r60": 0.013457,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 1.002385,
                                "atr_pct_14": 0.021440,
                            },
                            "norm": {"z20": 0.77, "z60": -0.97, "zvol": -0.02},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "LRCX",
                        "score": {
                            "MOMO": 46,
                            "features": {
                                "r20": 0.029461,
                                "r60": 0.148443,
                                "ma_cross": "true",
                                "breakout": "false",
                                "vol_surge": 0.688528,
                                "atr_pct_14": 0.029046,
                            },
                            "norm": {"z20": -0.01, "z60": 0.02, "zvol": -1.06},
                            "data_confidence": "high",
                        },
                    },
                    {
                        "ticker": "AMAT",
                        "score": {
                            "MOMO": 31,
                            "features": {
                                "r20": -0.112960,
                                "r60": -0.065415,
                                "ma_cross": "false",
                                "breakout": "false",
                                "vol_surge": 0.705856,
                                "atr_pct_14": 0.021206,
                            },
                            "norm": {"z20": -1.49, "z60": -1.54, "zvol": -1.0},
                            "data_confidence": "high",
                        },
                    },
                ],
                fund_score=[
                    {
                        "ticker": "AAPL",
                        "FUND": 50,
                        "scores": {"V": 15, "G": 50, "Q": 80, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Valuation is stretched (P/E ~35.9, EV/Sales ~8.8) which limits upside vs peers.",
                            "Very strong profitability and capital returns (ROE elevated, operating margin ~30%).",
                            "Growth has moderated (mid-single-digit revenue deceleration vs prior periods).",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "MSFT",
                        "FUND": 68,
                        "scores": {"V": 15, "G": 95, "Q": 95, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Premium multiple (P/E ~36.6) but supported by robust top-line and EPS growth (revenue growth ~18% and strong earnings expansion).",
                            "High-quality business metrics: strong ROE (~33%), excellent margins (~45%).",
                            "Analyst sentiment and forward estimates remain favorable—growth and quality offset valuation compression risk.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "GOOGL",
                        "FUND": 69,
                        "scores": {"V": 40, "G": 70, "Q": 100, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Very high-quality franchise: strong ROE (~34.8%) and healthy operating margins (~32%).",
                            "Solid earnings and revenue growth (EPS growth ~22%), with constructive analyst revisions.",
                            "Valuation appears reasonable on some metrics (P/B ~7.9) vs growth/quality profile.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "NVDA",
                        "FUND": 69,
                        "scores": {"V": 15, "G": 95, "Q": 100, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Exceptional growth and profitability (revenue growth ~55.6%, operating margin ~60.8%), driving high quality scores.",
                            "Valuation is very rich (P/E ~47.5, EV/Sales ~24.5), increasing sensitivity to execution and macro risks.",
                            "Strong analyst sentiment and recurring earnings beats support the premium multiple.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "AVGO",
                        "FUND": 70,
                        "scores": {"V": 35, "G": 95, "Q": 80, "E": 75},
                        "label": "Strong",
                        "insights": [
                            "Robust growth driven by AI-related chip and networking demand (strong Q2 FY2025 results and bullish guidance).",
                            "High earnings growth and solid margins/ROE support a strong fundamental profile despite a high P/E (~87).",
                            "Mixed valuation signals: elevated P/E but relatively low EV/Sales (~2.9) — market pricing reflects growth and strategic customer wins.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "ASML",
                        "FUND": 73,
                        "scores": {"V": 30, "G": 95, "Q": 100, "E": 75},
                        "label": "Strong",
                        "insights": [
                            "Clear beneficiary of semiconductor capex cycle: strong orders/shipments and guidance (Q2 net sales ~€7.7bn).",
                            "Exceptional quality metrics (high ROE, robust operating margins) and consistent earnings beats.",
                            "Valuation rich on some multiples (P/B and EV/Sales elevated) but justified by durable structural demand from leading foundries.",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "LRCX",
                        "FUND": 75,
                        "scores": {"V": 40, "G": 95, "Q": 95, "E": 75},
                        "label": "Strong",
                        "insights": [
                            "Bellwether for the wafer-fab equipment cycle — strong Q2 CY2025 beats and raised/confirmed outlook indicate sustained capex momentum.",
                            "High revenue and earnings growth (double-digit/low double-digit+ growth) with excellent ROE and margins.",
                            "Valuation sits in a moderate range relative to the growth profile (supportive technical momentum post-earnings).",
                        ],
                        "data_confidence": "high",
                    },
                    {
                        "ticker": "AMAT",
                        "FUND": 62,
                        "scores": {"V": 40, "G": 50, "Q": 95, "E": 75},
                        "label": "Neutral",
                        "insights": [
                            "Record EPS and broad demand across logic, memory and advanced packaging underpin fundamentals (solid margins, ROE ~35.6%).",
                            "Revenue growth is positive but more moderate (~7% YoY), making valuation/growth trade-offs important.",
                            "High-quality operations and cash generation support a favorable risk profile despite a less aggressive growth score.",
                        ],
                        "data_confidence": "high",
                    },
                ],
                review_note={
                    "period": "2025-09-01...2025-09-08",
                    "opinion": "Insufficient historical data for meaningful performance review. Default to balanced approach.",
                    "preference": "balanced",
                    "adjustment": 0.0,
                },
                risk_note={
                    "per_ticker": [
                        {
                            "ticker": "AAPL",
                            "allowed": "true",
                            "max_weight_pct": 9.02,
                            "notes": [
                                "Liquidity: ADV ≈ $12.8B (ample)",
                                "Volatility: ATR% ≈ 1.65% (passes ≤6% filter)",
                                "Beta: 1.109 (normal)",
                            ],
                            "beta": 1.109,
                            "atr_pct": 1.651211990051754,
                        },
                        {
                            "ticker": "MSFT",
                            "allowed": "true",
                            "max_weight_pct": 9.62,
                            "notes": [
                                "Liquidity: ADV ≈ $10.1B (ample)",
                                "Volatility: ATR% ≈ 1.41% (passes ≤6% filter)",
                                "Beta: 1.04 (normal)",
                            ],
                            "beta": 1.04,
                            "atr_pct": 1.4112231869381413,
                        },
                        {
                            "ticker": "GOOGL",
                            "allowed": "true",
                            "max_weight_pct": 9.89,
                            "notes": [
                                "Liquidity: ADV ≈ $9.1B (ample)",
                                "Volatility: ATR% ≈ 2.50% (passes ≤6% filter)",
                                "Sector: Communication Services (helps diversify away from Technology)",
                            ],
                            "beta": 1.011,
                            "atr_pct": 2.5016210089038503,
                        },
                        {
                            "ticker": "NVDA",
                            "allowed": "true",
                            "max_weight_pct": 4.76,
                            "notes": [
                                "Liquidity: ADV ≈ $29.1B (ample)",
                                "Volatility: ATR% ≈ 3.09% (passes ≤6% filter)",
                                "High beta: 2.102 → beta-adjusted cap (reduced exposure)",
                            ],
                            "beta": 2.102,
                            "atr_pct": 3.092351569541264,
                        },
                        {
                            "ticker": "AVGO",
                            "allowed": "true",
                            "max_weight_pct": 8.53,
                            "notes": [
                                "Liquidity: ADV ≈ $7.1B (ample)",
                                "Volatility: ATR% ≈ 3.87% (passes ≤6% filter)",
                                "Earnings: last reported 2025-09-05 (outside 3-day post-earnings restriction)",
                                "Beta: 1.172 (moderate)",
                            ],
                            "beta": 1.172,
                            "atr_pct": 3.8653280552121146,
                        },
                        {
                            "ticker": "ASML",
                            "allowed": "true",
                            "max_weight_pct": 8.01,
                            "notes": [
                                "Liquidity: ADV ≈ $1.40B (ample, NY-listed ADR liquidity acceptable)",
                                "Volatility: ATR% ≈ 2.14% (passes ≤6% filter)",
                                "Beta: 1.249 (moderate)",
                            ],
                            "beta": 1.249,
                            "atr_pct": 2.1448304541773162,
                        },
                        {
                            "ticker": "LRCX",
                            "allowed": "true",
                            "max_weight_pct": 5.65,
                            "notes": [
                                "Liquidity: ADV ≈ $1.14B (ample)",
                                "Volatility: ATR% ≈ 2.91% (passes ≤6% filter)",
                                "High beta: 1.77 → beta-adjusted cap (reduced exposure)",
                            ],
                            "beta": 1.77,
                            "atr_pct": 2.907253527357254,
                        },
                        {
                            "ticker": "AMAT",
                            "allowed": "true",
                            "max_weight_pct": 5.68,
                            "notes": [
                                "Liquidity: ADV ≈ $1.17B (ample)",
                                "Volatility: ATR% ≈ 2.12% (passes ≤6% filter)",
                                "High beta: 1.762 → beta-adjusted cap (reduced exposure)",
                            ],
                            "beta": 1.762,
                            "atr_pct": 2.123962349020731,
                        },
                    ],
                    "portfolio_limits": {
                        "single_stock_cap": 15.0,
                        "sector_caps": [
                            {"sector": "Technology", "cap": 35.0},
                            {"sector": "Communication Services", "cap": 35.0},
                        ],
                        "cash_floor": 5.0,
                    },
                    "portfolio_warnings": [
                        {"type": "sector_concentration", "sector": "Technology", "actual": 56.99, "limit": 35.0}
                    ],
                    "overall_note": "All tickers pass the volatility (ATR% ≤6%) and liquidity (ADV ≥ $5M) filters. High-beta names (NVDA, LRCX, AMAT) receive reduced maximum weights per the beta adjustment—this is reflected in the calculated max_weight_pct values (conservative sizing). Portfolio is materially overweight Technology (~57% vs 35% cap) — recommend trimming Technology exposure or limiting new additions from the sector until sector weight is reduced toward the 35% cap. Cash currently ≈9.45% (meets ≥5% cash floor). Maintain conservative bias: prioritize purchases in non-Technology/Communication Services or reduce position sizes for high-beta semicap names.",
                },
                final_portfolio={
                    "id": 1,
                    "user_id": 1,
                    "base_currency": "USD",
                    "cash": 7058.38,
                    "updated_at": "2025-09-09T15:21:14Z",
                    "positions": [
                        {
                            "id": 1,
                            "portfolio_id": 1,
                            "ticker": "AAPL",
                            "total_shares": 4.04,
                            "avg_buy_price": 150.00,
                            "updated_at": "2025-09-09T15:21:14Z",
                            "current_price": 236.25999450683594,
                            "current_market_value": 954.4903778076172,
                            "unrealized_pnl": 348.4903778076172,
                            "unrealized_pnl_pct": 57.49,
                        },
                        {
                            "id": 24,
                            "portfolio_id": 1,
                            "ticker": "MSFT",
                            "total_shares": 2.04,
                            "avg_buy_price": 422.37,
                            "updated_at": "2025-09-09T15:21:14Z",
                            "current_price": 499.69500732421875,
                            "current_market_value": 1019.3778149414063,
                            "unrealized_pnl": 157.74301494140625,
                            "unrealized_pnl_pct": 18.31,
                        },
                        {
                            "id": 25,
                            "portfolio_id": 1,
                            "ticker": "GOOGL",
                            "total_shares": 4.43,
                            "avg_buy_price": 172.00,
                            "updated_at": "2025-09-09T15:21:14Z",
                            "current_price": 236.17999267578125,
                            "current_market_value": 1046.27736755,
                            "unrealized_pnl": 284.31736755,
                            "unrealized_pnl_pct": 37.33,
                        },
                        {
                            "id": 26,
                            "portfolio_id": 1,
                            "ticker": "NVDA",
                            "total_shares": 3.01,
                            "avg_buy_price": 136.50,
                            "updated_at": "2025-09-09T15:21:14Z",
                            "current_price": 167.63499450683594,
                            "current_market_value": 504.5813334655762,
                            "unrealized_pnl": 93.7163334655762,
                            "unrealized_pnl_pct": 22.80,
                        },
                    ],
                    "total_stock_value": 3524.7268937645997,
                    "total_value": 10583.1068937646,
                    "total_unrealized_pnl": 884.2670937645997,
                    "total_unrealized_pnl_pct": 33.49,
                },
            )
            graph = build_reporter_graph(llm_client)
    except Exception as e:
        print(f"❌ Graph 빌드 에러: {e}")
        return

    try:
        result = graph.invoke(
            state_schema,
            config={
                "run_name": f"{agent_name}_agent",
                "tags": [agent_name, "individual_test"],
                "metadata": {"agent": agent_name, "test_type": "individual"},
            },
        )
    except Exception as e:
        print(f"❌ Graph 실행 에러: {e}")
        return

    print(f"🔍 {agent_name} 결과: {result}")


def test_pipeline(llm_client):
    """전체 파이프라인 테스트

    Args:
        llm_client: LLMClient
    """

    # 테스트 입력 데이터
    portfolio: PortfolioOut = asyncio.run(PortfolioRepo().get_current_portfolio(user_id=1))
    initial_state: ParentState = ParentState(
        messages=[],
        portfolio=portfolio.model_dump(),
        universe=[pos.ticker for pos in portfolio.positions],
        asof=datetime.utcnow().isoformat(),
        language="ko",
    )

    print("🚀 Multi-Agent Pipeline 테스트 시작...")
    print(f"- Initial portfolio: {initial_state['portfolio']}")
    print(f"- Universe: {initial_state['universe']}")
    print(f"- Timestamp: {initial_state['asof']}")
    print("\n" + "-" * 50)

    try:
        print(f"🤖 LLM Client: {llm_client}")

        # 그래프 빌드
        graph = build_root_graph(llm_client)
        print("✅ 그래프 빌드 성공")

        # 파이프라인 실행
        print("\n🔄 파이프라인 실행 중...")
        result = graph.invoke(initial_state)
        print("\n✅ 파이프라인 실행 완료!")
        print("\n📋 실행 결과:")

        # 결과 출력
        if "crawl_snapshot_id" in result:
            print(f"  📥 Crawler: {result['crawl_snapshot_id']}")

        if "new_candidates" in result:
            print(f"  🔍 New candidates: {len(result.get('new_candidates', []))} found")

        if "momo_signal" in result:
            print(f"  📈 Momentum signals: {len(result.get('momo_signal', {}))} tickers")

        if "fund_signal" in result:
            print(f"  💰 Fund signals: {len(result.get('fund_signal', {}))} tickers")

        if "reviewer_notes" in result:
            reviewer = result.get("reviewer_notes", {})
            print(
                f"  🔍 Reviewer: {reviewer.get('preference', 'N/A')} preference, \
                 {reviewer.get('adjustment', 0)} adjustment"
            )

        if "risk_limits" in result:
            risk = result.get("risk_limits", {})
            print(f"  ⚠️  Risk: {len(risk.get('per_ticker', {}))} ticker assessments")

        if "decisions" in result:
            decisions = result.get("decisions", [])
            print(f"  🎯 Decisions: {len(decisions)} actions")
            for decision in decisions[:3]:  # Show first 3
                print(
                    f"    - {decision.get('ticker', 'N/A')}: {decision.get('action', 'N/A')} \
                     (score: {decision.get('total_score', 'N/A')})"
                )

        if "report_md" in result:
            report_length = len(result.get("report_md", ""))
            print(f"  📊 Report: {report_length} characters generated")

        print(f"\n📋 전체 결과 키: {list(result.keys())}")

        # 리포트 미리보기
        if result.get("report_md"):
            print("\n📄 리포트:")
            print("-" * 50)
            print(result["report_md"])
            print("-" * 50)

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    import asyncio

    # 먼저 .env 파일을 로드
    load_dotenv()

    # LangSmith 트레이싱 활성화
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "porta-pipeline"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

    # API KEYS 확인
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # 데이터베이스 초기화
    from db import init_database

    print("🔧 데이터베이스 초기화 중...")
    asyncio.run(init_database())
    print("✅ 데이터베이스 초기화 완료")

    # .env 로드 후에 LLM 클라이언트 임포트
    from graph.llm_clients.openai_client import get_openai_client

    llm_client_mini = get_openai_client(model_name="gpt-5-mini")
    llm_client_high = get_openai_client(model_name="gpt-5-nano")
    # llm_client = mock_llm

    for agent_name in [
        # "crawler",
        # "momo",
        # "fund",
        # "reviewer",
        # "risk",
    ]:
        test_individual_agent(llm_client_mini, agent_name=agent_name)
    for agent_name in [
        # "decider",
        # "reporter",
    ]:
        test_individual_agent(llm_client_mini, agent_name=agent_name)

    test_pipeline(llm_client_mini)
