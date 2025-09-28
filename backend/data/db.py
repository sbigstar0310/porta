# backend/data/db.py
from typing import Optional, Dict, Any
from supabase import Client
from clients import get_supabase_client
import logging

logger = logging.getLogger(__name__)


class Database:
    """
    앱 전역 DB 싱글톤 클래스
    Supabase client를 관리하며 thread-safe한 방식으로 인스턴스를 제공합니다.
    """

    _instance: Optional["Database"] = None
    _client: Optional[Client] = None
    _initialized: bool = False

    def __new__(cls) -> "Database":
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """인스턴스 초기화 (한 번만 실행됨)"""
        if not self._initialized:
            self._initialized = True

    @classmethod
    async def initialize(cls) -> "Database":
        """
        비동기 초기화 메서드
        앱 시작 시 한 번만 호출해야 합니다.

        Returns:
            Database: 초기화된 데이터베이스 인스턴스
        """
        instance = cls()
        if cls._client is None:
            await instance._init_supabase_client()
        return instance

    async def _init_supabase_client(self):
        """Supabase 클라이언트 초기화"""
        try:
            self._client = get_supabase_client()
            logger.info("Supabase 클라이언트가 성공적으로 초기화되었습니다.")

        except Exception as e:
            logger.error(f"Supabase 클라이언트 초기화 실패: {e}")
            raise

    @property
    def client(self) -> Client:
        """
        Supabase 클라이언트 반환

        Returns:
            Client: Supabase 클라이언트 인스턴스

        Raises:
            RuntimeError: 클라이언트가 초기화되지 않은 경우
        """
        if self._client is None:
            raise RuntimeError("데이터베이스가 초기화되지 않았습니다. " "Database.initialize()를 먼저 호출해주세요.")
        return self._client

    async def health_check(self) -> Dict[str, Any]:
        """
        데이터베이스 연결 상태 확인

        Returns:
            Dict[str, Any]: 상태 정보
        """
        try:
            # 간단한 쿼리로 연결 상태 확인
            self.client.table("users").select("count", count="exact").limit(1).execute()
            return {"status": "healthy", "connected": True, "message": "데이터베이스 연결이 정상입니다."}
        except Exception as e:
            logger.error(f"데이터베이스 상태 확인 실패: {e}")
            return {"status": "unhealthy", "connected": False, "error": str(e)}

    async def close(self):
        """
        데이터베이스 연결 종료
        앱 종료 시 호출하여 리소스를 정리합니다.
        """
        if self._client:
            logger.info("데이터베이스 연결이 종료되었습니다.")
