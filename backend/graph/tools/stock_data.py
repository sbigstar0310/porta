# tools/stock_data.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from langchain_core.tools import tool
from clients.stock_client import StockClient


@tool
def get_stock_data(tickers: List[str], period: str = "6mo") -> Dict[str, Any]:
    """
    주식 데이터를 가져오는 도구

    Args:
        tickers: 주식 티커 리스트 (예: ["AAPL", "MSFT"])
        period: 데이터 기간 ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y",
                "ytd", "max")

    Returns:
        Dict containing stock data for all tickers
    """
    try:
        # init StockClient
        stock_client = StockClient()

        # Get stock data
        stock_data = stock_client.get_stock_data(tickers, period)

        return {
            "status": "success",
            "stock_history": stock_data.get("stock_history", {}),
            "stock_info": stock_data.get("stock_info", {}),
            "stock_calendar": stock_data.get("stock_calendar", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@tool
def calculate_momentum_scores(tickers: List[str], period: str = "6mo") -> Dict[str, Any]:
    """
    주식 데이터를 가져와서 모멘텀 지표와 정규화된 스코어를 한번에 계산하는 도구

    Args:
        tickers: 주식 티커 리스트 (예: ["AAPL", "MSFT"])
        period: 데이터 기간 ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y",
                "ytd", "max")

    Returns:
        Dict containing normalized momentum scores and features for all tickers
    """
    try:
        # init StockClient
        stock_client = StockClient()

        # 1단계: 모든 티커의 주식 데이터 수집
        all_features = {}
        valid_tickers = []
        stock_data = stock_client.get_stock_data(tickers, period)
        stock_history = stock_data.get("stock_history", {})

        for ticker in tickers:
            try:
                hist = stock_history.get(ticker, {})

                if hist.empty:
                    continue

                # DataFrame 준비
                df = pd.DataFrame(
                    {"close": hist["Close"].values, "volume": hist["Volume"].values},
                    index=hist.index,
                )

                df = df.sort_index()

                if len(df) < 70:  # 최소 70일 데이터 필요
                    continue

                # 모멘텀 지표 계산
                features = {}

                # 1. 20일/60일 수익률
                if len(df) >= 20:
                    features["r20"] = df["close"].iloc[-1] / df["close"].iloc[-21] - 1
                else:
                    features["r20"] = None

                if len(df) >= 60:
                    features["r60"] = df["close"].iloc[-1] / df["close"].iloc[-61] - 1
                else:
                    features["r60"] = None

                # 2. 이동평균선 교차 (20일선이 60일선 위에 있는지)
                if len(df) >= 60:
                    ma20 = df["close"].rolling(20).mean()
                    ma60 = df["close"].rolling(60).mean()
                    features["ma_cross"] = True if ma20.iloc[-1] > ma60.iloc[-1] else False
                else:
                    features["ma_cross"] = None

                # 3. 돌파 여부 (현재가가 20일 최고가 돌파)
                if len(df) >= 20:
                    recent_high = df["close"].rolling(20).max().iloc[-21:-1].max()
                    current_price = df["close"].iloc[-1]
                    features["breakout"] = current_price > recent_high
                else:
                    features["breakout"] = None

                # 4. 거래량 급증 비율 (최근 5일 평균 vs 20일 평균)
                if len(df) >= 20:
                    recent_vol = df["volume"].tail(5).mean()
                    avg_vol = df["volume"].tail(20).mean()
                    features["vol_surge"] = recent_vol / avg_vol if avg_vol > 0 else None
                else:
                    features["vol_surge"] = None

                # 5. 14일 변동성 (ATR %)
                if len(df) >= 14:
                    high_low = hist["High"] - hist["Low"]
                    high_close = (hist["High"] - hist["Close"].shift()).abs()
                    low_close = (hist["Low"] - hist["Close"].shift()).abs()
                    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

                    atr = tr.rolling(window=14).mean().iloc[-1]
                    last_close = hist["Close"].iloc[-1]
                    features["atr_pct_14"] = float(atr / last_close)
                else:
                    features["atr_pct_14"] = None

                # 6. 기본 정보
                features["current_price"] = df["close"].iloc[-1]
                features["data_confidence"] = "high" if len(df) >= 100 else "medium" if len(df) >= 60 else "low"

                # 유효한 데이터로 저장
                all_features[ticker] = features
                valid_tickers.append(ticker)

            except Exception as e:
                print(f"Error fetching stock data for {ticker}: {e}")
                # 개별 ticker 실패시 스킵
                continue

        # 2단계: 유니버스 내에서 정규화 및 스코어 계산
        if len(valid_tickers) < 1:
            return {
                "status": "error",
                "error": "No valid tickers found",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 정규화할 지표들
        feature_mapping = {"z20": "r20", "z60": "r60", "zvol": "vol_surge"}
        metrics_to_normalize = ["z20", "z60", "zvol"]

        # 각 지표별 universe 통계 계산
        universe_stats = {}
        for metric in metrics_to_normalize:
            values = []
            for ticker in valid_tickers:
                # 매핑된 feature 이름 사용
                feature_name = feature_mapping.get(metric, metric)
                val = all_features[ticker].get(feature_name)
                if val is not None and not np.isnan(val):
                    values.append(val)

            if len(values) >= 2:
                universe_stats[metric] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                }
            else:
                print(f"Not enough data for {metric} of {ticker}")

        # 각 ticker별로 정규화 점수 계산
        normalized_results = []
        for ticker in valid_tickers:
            features = all_features[ticker]
            normalized = {}

            # z-score 계산
            for metric in metrics_to_normalize:
                if metric in universe_stats:
                    # 매핑된 feature 이름 사용
                    feature_name = feature_mapping.get(metric, metric)
                    ticker_val = features.get(feature_name)

                    if ticker_val is not None and not np.isnan(ticker_val):
                        stats = universe_stats[metric]
                        if stats["std"] > 0:
                            z_score = (ticker_val - stats["mean"]) / stats["std"]
                            normalized[metric] = round(z_score, 2)

            # 종합 MOMO 스코어 계산 (agent-pipeline.md 공식 반영)
            score_components = {}

            # trend 계산 (r20, r60 z-scores)
            if "z20" in normalized and "z60" in normalized:
                trend = 0.4 * normalized["z20"] + 0.6 * normalized["z60"]
                score_components["trend"] = trend

            # vol_conf 계산 (vol_surge)
            if "zvol" in normalized and features.get("vol_surge"):
                vol_conf = 0.7 * normalized["zvol"] + 0.3 * np.log(max(features["vol_surge"], 0.1))
                score_components["vol_conf"] = vol_conf

            # pattern 계산 (ma_cross, breakout)
            ma_val = 1.0 if features.get("ma_cross", False) else 0.0
            breakout_val = 1.0 if features.get("breakout", False) else 0.0
            pattern = 0.5 * ma_val + 0.5 * breakout_val
            score_components["pattern"] = pattern

            # vol_penalty 계산
            vol_penalty = features.get("atr_pct_14", 0) / 0.05
            score_components["vol_penalty"] = vol_penalty

            # 최종 s 계산
            trend_score = score_components.get("trend", 0)
            vol_conf_score = score_components.get("vol_conf", 0)
            pattern_score = score_components.get("pattern", 0)
            penalty = score_components.get("vol_penalty", 0)

            s = 0.5 * trend_score + 0.3 * vol_conf_score + 0.3 * pattern_score - 0.2 * penalty

            # sigmoid 적용하여 0-100 스케일로 변환
            sigmoid_val = 1 / (1 + np.exp(-0.7 * s))
            momo_score = int(100 * sigmoid_val)

            normalized_results.append(
                {
                    "ticker": ticker,
                    "score": {
                        "MOMO": min(max(momo_score, 0), 100),
                        "features": {
                            "r20": features.get("r20"),
                            "r60": features.get("r60"),
                            "ma_cross": features.get("ma_cross"),  # boolean 유지
                            "breakout": features.get("breakout"),  # boolean 유지
                            "vol_surge": features.get("vol_surge"),
                            "atr_pct_14": features.get("atr_pct_14"),
                        },
                        "norm": normalized,
                        "data_confidence": features.get("data_confidence", "low"),
                    },
                }
            )

        return {
            "version": "1.0",
            "asof": datetime.utcnow().isoformat(),
            "momo_score": [
                {
                    "ticker": result["ticker"],
                    "score": {
                        "MOMO": result["score"]["MOMO"],
                        "features": {
                            "r20": result["score"]["features"]["r20"],
                            "r60": result["score"]["features"]["r60"],
                            "ma_cross": result["score"]["features"]["ma_cross"],  # boolean 유지
                            "breakout": result["score"]["features"]["breakout"],  # boolean 유지
                            "vol_surge": result["score"]["features"]["vol_surge"],
                            "atr_pct_14": result["score"]["features"]["atr_pct_14"],
                        },
                        "norm": result["score"]["norm"],
                        "data_confidence": result["score"]["data_confidence"],
                    },
                }
                for result in normalized_results
            ],
        }

    except Exception as e:
        print(f"Error calculating momentum scores: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@tool
def calculate_fund_scores(tickers: List[str], period: str = "6mo") -> Dict[str, Any]:
    """
    주식 데이터를 가져와서 펀더멘털 분석 지표와 FUND 스코어를 계산하는 도구.
    - V(Valuation), G(Growth), Q(Quality), E(Earnings)을 기반으로 주식의 fundamental 지표를 평가.

    Args:
        tickers: 주식 티커 리스트 (예: ["AAPL", "MSFT"])
        period: 데이터 기간 ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y",
                "ytd", "max")

    Returns:
        Dict containing fundamental scores for all tickers based on VGQE model
        V(Valuation), G(Growth), Q(Quality), E(Earnings)
    """
    try:
        # init StockClient
        stock_client = StockClient()

        # Get stock data
        stock_data = stock_client.get_stock_data(tickers, period)
        stock_info = stock_data["stock_info"]

        fund_results = []
        valid_tickers = []

        for ticker in tickers:
            try:
                info = stock_info[ticker]

                # 기본 정보 수집
                if not info or len(info) < 5:
                    continue

                # 필수 데이터 확인
                current_price = info.get("currentPrice") or info.get("regularMarketPrice")
                if not current_price:
                    continue

                valid_tickers.append(ticker)

                # 1. Valuation (V) - 30% 가중치
                v_weight = 0.3
                v_score = 50  # 기본 점수
                v_factors = []

                # P/E ratio (주가순이익비율)
                pe_ratio = info.get("trailingPE") or info.get("forwardPE")
                if pe_ratio:
                    if pe_ratio < 15:
                        v_score += 20
                        v_factors.append(f"낮은 PER ({pe_ratio:.1f}) (밸류에이션 매력)")
                    elif pe_ratio > 30:
                        v_score -= 15
                        v_factors.append(f"높은 PER ({pe_ratio:.1f}) (밸류에이션 부담)")

                # P/B ratio (주가순자산비율)
                pb_ratio = info.get("priceToBook")
                if pb_ratio:
                    if pb_ratio < 1.5:
                        v_score += 15
                        v_factors.append(f"낮은 PBR ({pb_ratio:.1f})")
                    elif pb_ratio > 4:
                        v_score -= 10
                        v_factors.append(f"높은 PBR ({pb_ratio:.1f})")

                # EV/Sales (기업가치/매출 비율)
                ev_sales = info.get("enterpriseToRevenue")
                if ev_sales:
                    if ev_sales < 3:
                        v_score += 10
                        v_factors.append(f"낮은 EV/Sales ({ev_sales:.1f})")
                    elif ev_sales > 8:
                        v_score -= 10
                        v_factors.append(f"높은 EV/Sales ({ev_sales:.1f})")

                v_score = max(0, min(100, v_score))

                # 2. Growth (G) - 30% 가중치
                g_weight = 0.3
                g_score = 50
                g_factors = []

                # Revenue growth (매출 성장률)
                revenue_growth = info.get("revenueGrowth")
                if revenue_growth:
                    if revenue_growth > 0.15:  # 15% 이상
                        g_score += 25
                        g_factors.append(f"강한 매출 성장 ({revenue_growth:.1%})")
                    elif revenue_growth < 0:
                        g_score -= 20
                        g_factors.append(f"매출 감소 ({revenue_growth:.1%})")

                # Earnings growth (이익 성장률)
                earnings_growth = info.get("earningsGrowth")
                if earnings_growth:
                    if earnings_growth > 0.20:  # 20% 이상
                        g_score += 20
                        g_factors.append(f"높은 이익 성장 ({earnings_growth:.1%})")
                    elif earnings_growth < 0:
                        g_score -= 15
                        g_factors.append(f"이익 감소 ({earnings_growth:.1%})")

                g_score = max(0, min(100, g_score))

                # 3. Quality (Q) - 25% 가중치
                q_weight = 0.25
                q_score = 50
                q_factors = []

                # ROE (자기자본이익률)
                roe = info.get("returnOnEquity")
                if roe:
                    if roe > 0.20:  # 20% 이상
                        q_score += 25
                        q_factors.append(f"높은 ROE ({roe:.1%})")
                    elif roe < 0.10:  # 10% 미만
                        q_score -= 15
                        q_factors.append(f"낮은 ROE ({roe:.1%})")

                # Operating margin (영업이익률)
                operating_margin = info.get("operatingMargins")
                if operating_margin:
                    if operating_margin > 0.20:  # 20% 이상
                        q_score += 20
                        q_factors.append(f"우수한 영업이익률 ({operating_margin:.1%})")
                    elif operating_margin < 0.05:  # 5% 미만
                        q_score -= 20
                        q_factors.append(f"낮은 영업이익률 ({operating_margin:.1%})")

                # Debt to equity (부채비율)
                debt_to_equity = info.get("debtToEquity")
                if debt_to_equity:
                    if debt_to_equity < 30:  # 30% 미만
                        q_score += 10
                        q_factors.append(f"낮은 부채비율 ({debt_to_equity:.1%})")
                    elif debt_to_equity > 80:  # 80% 이상
                        q_score -= 15
                        q_factors.append(f"높은 부채비율 ({debt_to_equity:.1%})")

                q_score = max(0, min(100, q_score))

                # 4. Earnings (E) - 15% 가중치
                e_weight = 0.15
                e_score = 50
                e_factors = []

                # EPS 관련 (주당순이익)
                eps = info.get("trailingEps") or info.get("forwardEps")
                if eps and eps > 0:
                    e_score += 10
                    e_factors.append(f"양의 EPS ({eps:.1f})")
                elif eps and eps < 0:
                    e_score -= 20
                    e_factors.append(f"음의 EPS ({eps:.1f})")

                # Analyst recommendations
                recommendation = info.get("recommendationMean")
                if recommendation:
                    if recommendation <= 2.0:  # Strong Buy/Buy
                        e_score += 15
                        e_factors.append("애널리스트 강력 추천")
                    elif recommendation >= 4.0:  # Hold/Sell
                        e_score -= 10
                        e_factors.append("애널리스트 보수적 전망")

                e_score = max(0, min(100, e_score))

                # 최종 FUND 점수 계산 (VGQE 가중 평균)
                fund_score = int(v_weight * v_score + g_weight * g_score + q_weight * q_score + e_weight * e_score)

                # 라벨 결정
                if fund_score >= 70:
                    label = "Strong"
                elif fund_score >= 50:
                    label = "Neutral"
                else:
                    label = "Weak"

                # insights 생성
                insights = []
                insights.extend(v_factors[:3])  # 최대 3개
                insights.extend(g_factors[:3])  # 최대 3개
                insights.extend(q_factors[:3])  # 최대 3개
                insights.extend(e_factors[:3])  # 최대 3개

                if not insights:
                    insights = ["데이터 제한으로 상세 분석 어려움"]

                # 데이터 신뢰도
                data_confidence = "high"
                missing_count = 0
                key_metrics = [pe_ratio, pb_ratio, revenue_growth, roe, operating_margin]
                for metric in key_metrics:
                    if metric is None:
                        missing_count += 1

                if missing_count >= 3:
                    data_confidence = "low"
                elif missing_count >= 1:
                    data_confidence = "medium"

                fund_results.append(
                    {
                        "ticker": ticker,
                        "FUND": fund_score,
                        "scores": {"V": v_score, "G": g_score, "Q": q_score, "E": e_score},
                        "label": label,
                        "insights": insights,
                        "data_confidence": data_confidence,
                    }
                )

            except Exception as e:
                print(f"Error calculating fund scores for {ticker}: {e}")
                continue

        if not fund_results:
            return {
                "status": "error",
                "error": "No valid fundamental data found for any ticker",
                "timestamp": datetime.utcnow().isoformat(),
            }
        return {"version": "1.0", "asof": datetime.utcnow().isoformat(), "status": "success", "scores": fund_results}

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@tool
def get_benchmark_data(benchmark_ticker: str = "SPY", period: str = "6mo") -> Dict[str, Any]:
    """
    벤치마크 지표(기본 SPY) 데이터를 가져오는 도구

    Args:
        benchmark_ticker: 벤치마크 티커 (기본 SPY)
        period: 데이터 기간 ("1mo", "3mo", "6mo", "1y")

    Returns:
        Dict containing benchmark performance data
    """
    try:
        import yfinance as yf

        # 직접 yfinance 호출 (info, calendar 제외)
        stock = yf.Ticker(benchmark_ticker)
        stock_history = stock.history(period=period)

        if stock_history.empty:
            return {
                "status": "error",
                "error": f"No data found for {benchmark_ticker}",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 기본 통계 계산
        df = stock_history.sort_index()
        current_price = df["Close"].iloc[-1]
        start_price = df["Close"].iloc[0]
        total_return = (current_price / start_price) - 1

        # 최근 7일, 20일, 60일 수익률
        returns_7d = (current_price / df["Close"].iloc[-8]) - 1 if len(df) >= 8 else None
        returns_20d = (current_price / df["Close"].iloc[-21]) - 1 if len(df) >= 21 else None
        returns_60d = (current_price / df["Close"].iloc[-61]) - 1 if len(df) >= 61 else None

        # 변동성 계산
        daily_returns = df["Close"].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)  # 연환산

        # 최근 성과 추세
        recent_trend = "rising" if returns_7d and returns_7d > 0 else "falling"

        return {
            "status": "success",
            "benchmark": benchmark_ticker,
            "current_price": round(current_price, 2),
            "total_return": round(total_return, 4),
            "returns": {
                "7d": round(returns_7d, 4) if returns_7d else None,
                "20d": round(returns_20d, 4) if returns_20d else None,
                "60d": round(returns_60d, 4) if returns_60d else None,
            },
            "volatility": round(volatility, 4),
            "recent_trend": recent_trend,
            "data_points": len(df),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@tool
def calculate_max_weight_pct(tickers: List[str], base_weight: float = 10, period: str = "3mo") -> Dict[str, Any]:
    """
    주식 티커 리스트를 가져와서 최대 가중치 퍼센트를 계산하는 도구
    - beta, atr_pct 지표를 가져와서 최대 가중치 퍼센트를 계산
    - max_weight_pct = base_weight × min(1, 1/max(1, beta, atr_pct/4%))
    - period: 데이터 기간 ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y",
                "ytd", "max")


    Args:
        tickers: 주식 티커 리스트 (예: ["AAPL", "MSFT"])
        base_weight: 기본 가중치

    Returns:
        Dict containing max weight percentage for all tickers
    """
    # init StockClient
    stock_client = StockClient()

    results = {}
    stock_data = stock_client.get_stock_data(tickers, period)
    stock_info = stock_data["stock_info"]
    try:
        for ticker in tickers:
            # Beta 가져오기 (없으면 1.0)
            beta = stock_info[ticker].get("beta", 1.0) or 1.0

            # ATR% 계산
            atr_pct = stock_client.get_atr_pct(ticker, period)

            # 수식 적용
            denominator = max(1, beta, atr_pct / 0.04)
            max_weight_pct = base_weight * min(1, 1 / denominator)

            results[ticker] = {
                "beta": beta,
                "atr_pct": atr_pct,
                "max_weight_pct": max_weight_pct,
            }

        return {
            "status": "success",
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
