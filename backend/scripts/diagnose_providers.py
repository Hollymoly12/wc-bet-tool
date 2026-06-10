"""Diagnostic: call each real provider ONCE and report what comes back + how well
team names resolve to our codes. Read-only, no DB writes. ~3 API calls total.

Run: .venv/bin/python scripts/diagnose_providers.py
"""
from __future__ import annotations

import sys

from app.config import get_settings
from app.providers.teamnames import to_code
from app.seed import seed_data


def hr(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main() -> None:
    s = get_settings()
    print(f"Odds key set: {s.has_odds_key} | Football key set: {s.has_football_key}")

    seed_codes = {t["code"] for t in seed_data.TEAMS}
    seed_names = set(seed_data.NAMES.values())

    # ---- The Odds API (1 call, raw) ---------------------------------------
    hr("THE ODDS API — /odds (raw)")
    try:
        from app.providers.the_odds_api import TheOddsApiAdapter
        ad = TheOddsApiAdapter()
        url = f"{ad._base}/sports/soccer_fifa_world_cup/odds"
        events = ad._get(url, {"apiKey": ad._key, "regions": "eu",
                               "markets": "h2h", "oddsFormat": "decimal"})
        print(f"events returned: {len(events)}")
        names = set()
        for e in events:
            names.add(e.get("home_team", ""))
            names.add(e.get("away_team", ""))
        names.discard("")
        resolved = sorted(n for n in names if to_code(n))
        unresolved = sorted(n for n in names if not to_code(n))
        print(f"distinct teams: {len(names)} | resolved: {len(resolved)} | "
              f"unresolved: {len(unresolved)}")
        if unresolved:
            print("UNRESOLVED names (need alias or are non-WC teams):")
            for n in unresolved:
                print("   -", n)
        if events:
            e0 = events[0]
            print("sample event:", e0.get("home_team"), "vs", e0.get("away_team"),
                  "| books:", len(e0.get("bookmakers", [])))
    except Exception as exc:  # noqa: BLE001
        print("ODDS error:", type(exc).__name__, exc)

    # ---- API-Football fixtures (1 call) -----------------------------------
    hr("API-FOOTBALL — /fixtures?league=1&season=2026 (raw)")
    try:
        from app.providers.api_football import ApiFootballAdapter
        af = ApiFootballAdapter()
        # use the adapter's own getter to see the raw 'response' array
        raw = af._get(f"{af._base}/fixtures", {"league": 1, "season": 2026})
        resp = raw.get("response", raw) if isinstance(raw, dict) else raw
        print(f"fixtures returned: {len(resp)}")
        af_names = set()
        for fx in resp[:200]:
            teams = (fx.get("teams") or {})
            af_names.add(((teams.get("home") or {}).get("name")) or "")
            af_names.add(((teams.get("away") or {}).get("name")) or "")
        af_names.discard("")
        af_unres = sorted(n for n in af_names if not to_code(n))
        print(f"distinct teams: {len(af_names)} | unresolved by to_code: {len(af_unres)}")
        if af_unres:
            print("API-Football names not in our map:")
            for n in af_unres:
                print("   -", n)
        if resp:
            fx0 = resp[0]
            print("sample:", fx0.get("teams"), "| date:", (fx0.get("fixture") or {}).get("date"))
    except Exception as exc:  # noqa: BLE001
        print("FIXTURES error:", type(exc).__name__, exc)

    # ---- API-Football injuries (1 call) -----------------------------------
    hr("API-FOOTBALL — /injuries?league=1&season=2026 (raw)")
    try:
        from app.providers.api_football import ApiFootballAdapter
        af = ApiFootballAdapter()
        raw = af._get(f"{af._base}/injuries", {"league": 1, "season": 2026})
        resp = raw.get("response", raw) if isinstance(raw, dict) else raw
        print(f"injury records: {len(resp)}")
        if resp:
            i0 = resp[0]
            print("sample:", (i0.get("team") or {}).get("name"),
                  "-", (i0.get("player") or {}).get("name"),
                  "-", i0.get("reason") or (i0.get("player") or {}).get("reason"))
    except Exception as exc:  # noqa: BLE001
        print("INJURIES error:", type(exc).__name__, exc)

    hr("SEED universe (for comparison)")
    print(f"seed teams: {len(seed_codes)} (illustrative projected WC26 set)")
    print("sample seed names:", sorted(seed_names)[:8])


if __name__ == "__main__":
    sys.exit(main())
