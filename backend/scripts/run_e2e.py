# scripts/run_e2e.py
"""에이전트 파이프라인 E2E 러너 (기본: dev Supabase).

run_graph만 실행한다 — 이메일 발송/보고서 저장/포트폴리오 변경 없음.
보고서 전문은 local_documents/에 저장된다.

사용법:
    cd backend && uv run python scripts/run_e2e.py [--email e2e-test@porta.dev]
"""
import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from dev_env import ROOT_DIR, load_dev_env


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail else ""))
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="e2e-test@porta.dev")
    parser.add_argument("--allow-prod", action="store_true", help="프로덕션 Supabase 대상 실행 허용 (주의)")
    args = parser.parse_args()

    load_dev_env(allow_prod=args.allow_prod)

    from repo import get_db_client, get_portfolio_repo
    from graph.app import run_graph

    rows = get_db_client().table("users").select("id,language").eq("email", args.email).execute().data
    if not rows:
        raise SystemExit(f"유저를 찾을 수 없습니다: {args.email} — 먼저 `uv run python scripts/seed_dev.py`를 실행하세요")
    user_id = rows[0]["id"]
    language = rows[0].get("language") or "ko"

    portfolio = asyncio.run(get_portfolio_repo().get_by_user_id(user_id))
    print(f"\n=== E2E 시작: user_id={user_id}, {len(portfolio.positions)}개 포지션 {[p.ticker for p in portfolio.positions]} ===\n")

    started = datetime.now(timezone.utc)
    result = run_graph(portfolio=portfolio, user_id=user_id, language=language)
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()

    # ---- 결과 요약 ----
    regime = result.get("market_regime", {})
    candidates = result.get("new_candidates", [])
    review_note = result.get("review_note", {})
    decisions = result.get("decisions", [])
    report_md = result.get("report_md") or ""

    print(f"\n=== 파이프라인 완료 ({elapsed:.0f}초) ===")
    print(f"시장 국면: {regime}")
    print(f"신규 후보 {len(candidates)}개: {[c.get('ticker') for c in candidates]}")
    print(f"리뷰어: δ={review_note.get('adjustment')} preference={review_note.get('preference')}")
    print("결정:")
    for d in decisions:
        print(
            f"  - {d['ticker']}: {d['action']} target={d['target_weight_pct']}% conf={d.get('confidence')}"
            f" shares={d['shares_to_trade']} value=${d['trade_value']} notes={d['risk_notes'][:2]}"
        )

    # ---- 핵심 체크 ----
    print("\n=== 검증 체크 ===")
    checks = [
        check("국면 신호 산출", regime.get("regime") in ("risk_on", "neutral", "risk_off"), str(regime.get("regime"))),
        check("신규 후보 발굴", len(candidates) > 0, f"{len(candidates)}개"),
        check("결정 생성", len(decisions) > 0, f"{len(decisions)}건"),
        check("결정에 검증 시세 포함", all(d.get("price", 0) > 0 for d in decisions) if decisions else False),
        check("보고서 생성", len(report_md) > 500, f"{len(report_md)}자"),
        check("보고서: 성적표 섹션", "추천 성적표" in report_md or "Track Record" in report_md),
        check("보고서: 시장 환경 줄", "시장 환경" in report_md or "Market Environment" in report_md),
        check("보고서: 면책 조항", "면책" in report_md or "Disclaimer" in report_md),
    ]

    # ---- 보고서 저장 ----
    out_dir = ROOT_DIR / "local_documents"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"e2e-report-{started.strftime('%Y%m%d-%H%M%S')}.md"
    out_path.write_text(report_md)
    print(f"\n보고서 저장: {out_path}")

    if all(checks):
        print("\n🎉 E2E PASS")
    else:
        raise SystemExit("\n💥 E2E FAIL — 위 체크 항목을 확인하세요")


if __name__ == "__main__":
    main()
