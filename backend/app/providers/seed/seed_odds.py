"""Seed odds provider — builds OddsLine DTOs from seed_data."""
from __future__ import annotations
from datetime import datetime, timezone
from app.providers.base import OddsLine
from app.seed import seed_data


class SeedOddsProvider:
    def fetch_odds(self) -> list[OddsLine]:
        now = datetime.now(timezone.utc)
        out: list[OddsLine] = []

        # h2h lines per match
        for m in seed_data.MATCHES:
            for sel, dec in zip(("home", "draw", "away"), m["odds"]):
                out.append(OddsLine(
                    market_key=f"h2h:{m['id']}",
                    book="seed",
                    selection=sel,
                    dec=dec,
                    captured_at=now,
                ))

        # outright lines per team
        for t in seed_data.TEAMS:
            out.append(OddsLine(
                market_key="outright",
                book="seed",
                selection=t["code"],
                dec=t["dec"],
                captured_at=now,
            ))

        return out
