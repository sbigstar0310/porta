from fastapi import APIRouter, HTTPException, Query, Depends
from clients import StockClient, get_stock_client
from data.schemas import StockSearchOut
import logging
from typing import List

router = APIRouter(prefix="/stock", tags=["stock"])

logger = logging.getLogger(__name__)


@router.get("/search")
def search_stock(
    query: str = Query(..., min_length=1, description="검색할 티커 또는 회사명 (예: 'AAPL', 'Apple', 'M')"),
    stock_client: StockClient = Depends(get_stock_client),
) -> List[StockSearchOut]:
    """
    종목 검색 API

    Args:
        query: 검색할 티커의 일부 또는 회사명의 일부
        stock_client: 의존성 주입된 StockClient

    Returns:
        List[StockSearchOut]: 후보 종목 목록 (ticker, company_name 포함)

    Examples:
        - /stock/search?query=M -> [{"ticker": "MSFT", "company_name": "Microsoft Corporation"}, ...]
        - /stock/search?query=Micro -> [{"ticker": "MSFT", "company_name": "Microsoft Corporation"}]
        - /stock/search?query=AAPL -> [{"ticker": "AAPL", "company_name": "Apple Inc."}]
    """
    try:
        return stock_client.search_stock(query)
    except Exception as e:
        if "requests.exceptions.RequestException" in str(type(e)):
            logger.error(f"종목 검색 중 네트워크 오류: {e}")
            raise HTTPException(status_code=503, detail="외부 서비스 연결 오류")
        else:
            logger.error(f"종목 검색 중 오류: {e}")
            raise HTTPException(status_code=500, detail="종목 검색 중 오류가 발생했습니다")
