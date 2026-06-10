# scripts/seed_dev.py
"""dev Supabase에 E2E용 테스트 유저/포트폴리오를 시딩한다 (멱등 — 재실행 안전).

사용법:
    cd backend && uv run python scripts/seed_dev.py
"""
import uuid

from dev_env import load_dev_env

TEST_EMAIL = "e2e-test@porta.dev"
CASH = "5000.00"
POSITIONS = [
    ("AAPL", "10.00", "180.00"),
    ("MSFT", "5.00", "380.00"),
    ("NVDA", "8.00", "120.00"),
]


def main():
    load_dev_env()
    from repo import get_db_client

    db = get_db_client()

    # 유저 (이메일 기준 멱등)
    rows = db.table("users").select("id").eq("email", TEST_EMAIL).execute().data
    if rows:
        user_id = rows[0]["id"]
        print(f"기존 테스트 유저 사용: user_id={user_id}")
    else:
        created = (
            db.table("users")
            .insert({"email": TEST_EMAIL, "uuid": str(uuid.uuid4()), "email_verified": True, "language": "ko"})
            .execute()
            .data
        )
        user_id = created[0]["id"]
        print(f"테스트 유저 생성: user_id={user_id}")

    # 포트폴리오 (유저당 1개)
    rows = db.table("portfolios").select("id").eq("user_id", user_id).execute().data
    if rows:
        portfolio_id = rows[0]["id"]
    else:
        portfolio_id = db.table("portfolios").insert({"user_id": user_id, "cash": CASH}).execute().data[0]["id"]
        print(f"포트폴리오 생성: portfolio_id={portfolio_id}, cash=${CASH}")

    # 포지션 (티커 기준 멱등)
    for ticker, shares, avg_price in POSITIONS:
        exists = db.table("positions").select("id").eq("portfolio_id", portfolio_id).eq("ticker", ticker).execute().data
        if not exists:
            db.table("positions").insert(
                {"portfolio_id": portfolio_id, "ticker": ticker, "total_shares": shares, "avg_buy_price": avg_price}
            ).execute()
            print(f"포지션 추가: {ticker} {shares}주 @ ${avg_price}")

    print(f"\n시딩 완료 — user_id={user_id} ({TEST_EMAIL})")
    print("E2E 실행: uv run python scripts/run_e2e.py")


if __name__ == "__main__":
    main()
