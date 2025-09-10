# llm_clients/mock_client.py
"""
테스트용 Mock LLM 클라이언트
"""


class MockMessage:
    def __init__(self, content: str):
        self.content = content

    @classmethod
    def get_content(cls, agent_name: str) -> str:
        """
        Get content for the given agent name

        Args:
          agent_name: str

        Returns:
          str
        """
        if agent_name == "crawler":
            return """
          {
            "new_candidates": [
              {
                "ticker": "NVDA",
                "name": "NVIDIA Corp",
                "reason": "Strong AI datacenter growth momentum"
              }
            ]
          }
          """
        elif agent_name == "momo":
            return """
            {
              "version": "1.0",
              "asof": "UTC ISO8601",
              "scores": {
                "AAPL": {
                  "MOMO": 63,
                  "features": {
                    "r20": 0.062,
                    "r60": 0.118,
                    "ma_cross": 1,
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
                  "data_confidence": "medium"
                }
            }
            """
        elif agent_name == "fund":
            return """
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
            """
        elif agent_name == "reviewer":
            return """
          {
            "period": "2025-08-31...2025-09-06",
            "opinion": "Recent momentum signals have been performing well in this market environment",
            "preference": "momentum",
            "adjustment": 0.02
          }
          """
        elif agent_name == "risk":
            return """{
            "per_ticker": {
              "AAPL": {
                "allowed": true,
                "max_weight_pct": 8.5,
                "notes": ["liquidity ok", "vol normal"],
                "beta": 1.2,
                "atr_pct": 3.2
              },
              "MSFT": {
                "allowed": true,
                "max_weight_pct": 10.0,
                "notes": ["stable stock"],
                "beta": 0.9,
                "atr_pct": 2.8
              },
              "NVDA": {
                "allowed": true,
                "max_weight_pct": 5.0,
                "notes": ["high volatility"],
                "beta": 1.8,
                "atr_pct": 6.5
              }
            },
            "portfolio_limits": {
              "single_stock_cap": 15,
              "sector_caps": {"Tech": 35},
              "cash_floor": 5
            },
            "portfolio_warnings": []
          }
          """
        elif agent_name == "decider":
            return """
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
            """
        elif agent_name == "reporter":
            return """
            # Portfolio Analysis Report
            *Generated: 2025-01-20T10:30:00Z*

            ## TL;DR
            - Added NVDA position (5%) based on strong momentum signals
            - Increased AAPL allocation to 8.5% on combined strength  
            - Maintained MSFT position with solid fundamentals
            - Current strategy slightly favors momentum (adjustment: +0.02)
            - No significant risk warnings

            ## Portfolio Changes
            | Action | Ticker | Target Weight | Current Weight | Rationale |
            |--------|--------|---------------|----------------|-----------|
            | BUY | NVDA | 5.0% | 0.0% | High momentum score, AI growth |
            | BUY | AAPL | 8.5% | 6.0% | Strong combined signals |
            | HOLD | MSFT | 10.0% | 10.0% | Maintain solid position |

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
            """
        else:
            raise ValueError(f"Invalid agent name: {agent_name}")


class MockLLM:
    """테스트용 Mock LLM"""

    def get_content(self, agent_name: str) -> str:
        """MockMessage의 get_content 메서드를 MockLLM으로 이동"""
        return MockMessage.get_content(agent_name)

    def invoke(self, prompt: str) -> MockMessage:
        """프롬프트에 따라 적절한 mock 응답 반환"""

        # crawler
        if "financial data crawler" in prompt.lower():
            return MockMessage(content=self.get_content("crawler"))

        # momo
        elif "momentum analyzer" in prompt.lower():
            return MockMessage(content=self.get_content("momo"))

        # fund
        elif "fundamental analysis" in prompt.lower():
            return MockMessage(content=self.get_content("fund"))

        # reviewer
        elif "portfolio performance reviewer" in prompt.lower():
            return MockMessage(content=self.get_content("reviewer"))

        # risk
        elif "risk management specialist" in prompt.lower():
            return MockMessage(content=self.get_content("risk"))

        # decider
        elif "portfolio decision maker" in prompt.lower():
            return MockMessage(content=self.get_content("decider"))

        # reporter
        elif "financial report writer" in prompt.lower():
            return MockMessage(content=self.get_content("reporter"))

        else:
            return MockMessage(content='{"error": "Unknown prompt type"}')


# Mock client instance
mock_llm = MockLLM()
