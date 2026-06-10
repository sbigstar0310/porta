# scripts/dev_env.py
"""dev 스크립트 공용 환경 로더.

베이스(루트 .env)를 로드한 뒤 PORTA_ENV_FILE(기본: 루트 .env.dev)로 덮어쓴다.
안전장치: 결과 SUPABASE_URL이 프로덕션(.env)과 같으면 중단 — E2E/시딩이
실수로 메인 DB를 건드리는 것을 막는다 (--allow-prod 류 플래그로만 우회).
"""
import os
import sys
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent

# repo/graph 등 backend 모듈 임포트 경로 보장
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def load_dev_env(allow_prod: bool = False) -> None:
    base_env = ROOT_DIR / ".env"
    overlay = Path(os.getenv("PORTA_ENV_FILE", ROOT_DIR / ".env.dev"))

    load_dotenv(base_env)
    if not load_dotenv(overlay, override=True):
        sys.exit(f"[중단] 환경 오버레이 파일을 찾을 수 없습니다: {overlay}")

    prod_url = (dotenv_values(base_env) or {}).get("SUPABASE_URL")
    if not allow_prod and prod_url and os.getenv("SUPABASE_URL") == prod_url:
        sys.exit(
            "[중단] 대상이 프로덕션 Supabase와 동일합니다.\n"
            f"  - {overlay} 의 SUPABASE_URL이 dev 프로젝트를 가리키는지 확인하세요."
        )
    print(f"[env] base={base_env.name} + overlay={overlay.name} → SUPABASE host: {os.getenv('SUPABASE_URL', '')[:35]}...")
