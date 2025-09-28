# app.py
from graph.root_graph import build_root_graph
import os
from graph.schemas import ParentState
from datetime import datetime
from data.schemas import PortfolioOut
from graph.llm_clients.openai_client import get_openai_client
import logging
import time
from langchain_core.runnables.config import RunnableConfig

logger = logging.getLogger(__name__)


def activate_langsmith():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "porta"


def run_graph(portfolio: PortfolioOut, user_id: int, language: str = "ko", debug: bool = True) -> dict:
    """
    Porta Agent Pipeline 실행

    Args:
        portfolio: PortfolioOut
        user_id: int
        language: 언어 설정
        debug: 디버그 모드 (True시 상세 로그 출력)

    Returns:
        dict: 파이프라인 결과
    """

    if debug:
        logger.info("🚀 Porta Agent Pipeline 시작 (디버그 모드)")
        logger.info(f"📊 포트폴리오: {len(portfolio.positions)}개 종목")
        start_time = time.time()

    # activate langsmith
    activate_langsmith()

    # llm client
    light_llm_client = get_openai_client(model_name="gpt-5-mini")
    middle_llm_client = get_openai_client(model_name="gpt-5")
    heavy_llm_client = get_openai_client(model_name="gpt-5")
    base_llm_client = get_openai_client(model_name="gpt-5-nano")

    if debug:
        logger.info("🤖 LLM 클라이언트 초기화 완료")

    # build root graph
    app = build_root_graph(
        light_llm_client=light_llm_client,
        middle_llm_client=middle_llm_client,
        heavy_llm_client=heavy_llm_client,
        base_llm_client=base_llm_client,
    )

    if debug:
        logger.info("📊 그래프 빌드 완료")

    # initial state
    initial_state: ParentState = ParentState(
        messages=[],
        portfolio=portfolio.model_dump(),
        asof=datetime.utcnow().isoformat(),
        universe=[pos.ticker for pos in portfolio.positions],
        user_id=user_id,
        language=language,
    )

    if debug:
        logger.info("🎯 파이프라인 실행 시작")

    # invoke pipeline with user_id in config
    config = RunnableConfig(recursion_limit=30, configurable={"user_id": user_id})
    result = app.invoke(initial_state, config=config)

    if debug:
        end_time = time.time()
        logger.info(f"✅ 파이프라인 실행 완료 (소요시간: {end_time - start_time:.2f}초)")
        logger.info(f"📋 결과 키: {list(result.keys())}")

    return result
