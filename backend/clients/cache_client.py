import os
import redis
import pickle
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CacheClient:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.client = redis.from_url(redis_url)
            # 연결 테스트
            self.client.ping()
            logger.info("✅ Redis cache client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise ValueError(f"Redis connection failed: {e}")

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        try:
            data = self.client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """캐시에 데이터 저장 (기본 5분 TTL)"""
        try:
            serialized = pickle.dumps(value)
            return self.client.setex(key, ttl_seconds, serialized)
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """캐시 키 존재 여부 확인"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {e}")
            return False

    def get_or_set(self, key: str, fetch_func, ttl_seconds: int = 300) -> Any:
        """캐시 조회 또는 새로 생성"""
        cached = self.get(key)
        if cached is not None:
            logger.debug(f"Cache hit: {key}")
            return cached

        logger.debug(f"Cache miss: {key}")
        fresh_data = fetch_func()
        self.set(key, fresh_data, ttl_seconds)
        return fresh_data

    def clear_pattern(self, pattern: str) -> int:
        """패턴에 맞는 모든 키 삭제"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    def get_ttl(self, key: str) -> int:
        """키의 남은 TTL 조회 (초 단위)"""
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.warning(f"Cache TTL error for key {key}: {e}")
            return -1
