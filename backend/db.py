# backend/db.py
import aiosqlite
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./porta.db"
    default_base_currency: str = "USD"


settings = Settings()
engine = create_async_engine(settings.database_url, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session():
    async with async_session() as session:
        yield session


async def init_database():
    """SQL 스크립트로 데이터베이스 초기화"""
    # SQLite 파일 경로 추출
    db_path = settings.database_url.replace("sqlite+aiosqlite:///./", "")

    # schema.sql 읽기
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    # SQLite에 직접 실행
    async with aiosqlite.connect(db_path) as conn:
        await conn.executescript(schema_sql)
        await conn.commit()
