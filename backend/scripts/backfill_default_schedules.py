# scripts/backfill_default_schedules.py
"""스케줄이 없는 기존 유저에게 기본 보고서 스케줄(매일 09:00)을 일괄 생성한다 (멱등).

신규 가입은 usecase.user_usecase.register_user 가 기본 스케줄을 자동 생성하지만,
그 훅이 없던 시절에 가입한 유저들은 schedules 행이 없어 보고서를 받지 못한다.
이 스크립트가 그런 유저들을 백필한다.

⚠️  이 스크립트는 기본적으로 base .env(= 프로덕션 Supabase)를 대상으로 하며,
    실행하면 대상 유저들이 다음 스케줄 시각부터 실제로 매일 이메일을 받기 시작한다.
    안전을 위해 기본은 dry-run(쓰기 없음)이고, 실제 INSERT는 --commit 플래그가 있을 때만 수행한다.

사용법:
    cd backend && uv run python scripts/backfill_default_schedules.py            # dry-run (대상만 출력)
    cd backend && uv run python scripts/backfill_default_schedules.py --commit   # 실제 생성

    # dev 등 다른 프로젝트를 대상으로 하려면 오버레이 지정:
    PORTA_ENV_FILE=../.env.dev uv run python scripts/backfill_default_schedules.py --commit
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent

# repo 등 backend 모듈 임포트 경로 보장
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 회원가입 훅과 동일한 기본값
DEFAULT_HOUR = 9
DEFAULT_MINUTE = 0
DEFAULT_TIMEZONE = "Asia/Seoul"


def _load_env() -> None:
    """base .env 로드 후 PORTA_ENV_FILE 오버레이가 있으면 덮어쓴다 (앱과 동일한 규칙)."""
    load_dotenv(ROOT_DIR / ".env")
    overlay = os.getenv("PORTA_ENV_FILE")
    if overlay:
        if not load_dotenv(overlay, override=True):
            sys.exit(f"[중단] PORTA_ENV_FILE 오버레이를 찾을 수 없습니다: {overlay}")


def main() -> None:
    commit = "--commit" in sys.argv[1:]
    _load_env()

    target = os.getenv("SUPABASE_URL", "")
    if not target:
        sys.exit("[중단] SUPABASE_URL 이 설정되지 않았습니다.")

    mode = "COMMIT (실제 생성)" if commit else "DRY-RUN (쓰기 없음)"
    print(f"[env] 대상 SUPABASE_URL: {target}")
    print(f"[mode] {mode}\n")

    from repo import get_db_client

    db = get_db_client()

    # 스케줄 없는 유저 계산: 전체 유저 - 이미 스케줄이 있는 user_id
    users = db.table("users").select("id, email, timezone").execute().data or []
    scheduled_rows = db.table("schedules").select("user_id").execute().data or []
    scheduled_user_ids = {row["user_id"] for row in scheduled_rows}

    targets = [u for u in users if u["id"] not in scheduled_user_ids]

    print(f"전체 유저: {len(users)}명 / 이미 스케줄 있음: {len(scheduled_user_ids)}명 / 백필 대상: {len(targets)}명\n")

    if not targets:
        print("백필할 유저가 없습니다. (모든 유저가 이미 스케줄 보유)")
        return

    created = 0
    for u in targets:
        tz = u.get("timezone") or DEFAULT_TIMEZONE
        label = f"user_id={u['id']} ({u.get('email', '?')}) tz={tz}"
        if not commit:
            print(f"  [dry-run] 생성 예정: {label} → {DEFAULT_HOUR:02d}:{DEFAULT_MINUTE:02d}")
            continue
        try:
            db.table("schedules").insert(
                {
                    "user_id": u["id"],
                    "hour": DEFAULT_HOUR,
                    "minute": DEFAULT_MINUTE,
                    "timezone": tz,
                    "enabled": True,
                }
            ).execute()
            created += 1
            print(f"  [created] {label} → {DEFAULT_HOUR:02d}:{DEFAULT_MINUTE:02d}")
        except Exception as e:
            print(f"  [실패] {label}: {e}")

    if commit:
        print(f"\n완료 — {created}/{len(targets)}명 스케줄 생성.")
    else:
        print(f"\nDRY-RUN 종료 — 실제 생성하려면 --commit 을 붙여 재실행하세요. (대상 {len(targets)}명)")


if __name__ == "__main__":
    main()
