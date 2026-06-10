"""The Odds API adapter — real OddsProvider for live WC 2026 fixtures.

Uses the /v4/sports/soccer_fifa_world_cup/odds endpoint.
Adapters are pure/stateless: no DB writes, no rate-limit state here.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.providers.base import OddsLine
from app.providers.teamnames import fixture_id, to_code

logger = logging.getLogger(__name__)

_SPORT = "soccer_fifa_world_cup"
_SPORT_WINNER = "soccer_fifa_world_cup_winner"
_TIMEOUT = 15.0


class TheOddsApiAdapter:
    """Fetches h2h odds from The Odds API and returns OddsLine DTOs."""

    def __init__(self) -> None:
        s = get_settings()
        self._base = s.odds_api_base.rstrip("/")
        self._key = s.odds_api_key

    # ------------------------------------------------------------------
    # Internal HTTP helper (easy to monkeypatch in tests)
    # ------------------------------------------------------------------
    def _get(self, url: str, params: dict) -> list:
        """GET url, return parsed JSON (expected to be a list)."""
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def fetch_odds(self) -> list[OddsLine]:
        """Fetch h2h odds for the World Cup and return as OddsLine list."""
        url = f"{self._base}/sports/{_SPORT}/odds"
        params = {
            "apiKey": self._key,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal",
        }

        try:
            events = self._get(url, params)
        except Exception as exc:
            logger.error("TheOddsApiAdapter fetch failed: %s", exc)
            return []

        now = datetime.now(timezone.utc)
        lines: list[OddsLine] = []

        for event in events:
            home_name = event.get("home_team", "")
            away_name = event.get("away_team", "")

            home_code = to_code(home_name)
            away_code = to_code(away_name)

            if home_code is None or away_code is None:
                logger.warning(
                    "TheOddsApiAdapter: skipping event %r — unresolved team(s)",
                    event.get("id", "?"),
                )
                continue

            mkey = f"h2h:{fixture_id(home_code, away_code)}"

            for bm in event.get("bookmakers", []):
                book_title = bm.get("title", "unknown")
                for market in bm.get("markets", []):
                    if market.get("key") != "h2h":
                        continue
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = float(outcome.get("price", 0.0))
                        if name == home_name:
                            selection = "home"
                        elif name == away_name:
                            selection = "away"
                        elif name.lower() == "draw":
                            selection = "draw"
                        else:
                            # Unknown outcome name — skip
                            logger.debug(
                                "TheOddsApiAdapter: unknown outcome name %r", name
                            )
                            continue

                        lines.append(OddsLine(
                            market_key=mkey,
                            book=book_title,
                            selection=selection,
                            dec=price,
                            captured_at=now,
                        ))

        return lines

    def fetch_outrights(self) -> list[OddsLine]:
        """Fetch outright winner odds for the World Cup and return as OddsLine list.

        Uses the soccer_fifa_world_cup_winner sport key with markets=outrights.
        Each outcome name is mapped to a team code via to_code; unresolved names
        (e.g. "No Winner", "Field") are silently skipped.
        """
        url = f"{self._base}/sports/{_SPORT_WINNER}/odds"
        params = {
            "apiKey": self._key,
            "regions": "eu",
            "markets": "outrights",
            "oddsFormat": "decimal",
        }

        try:
            events = self._get(url, params)
        except Exception as exc:
            logger.error("TheOddsApiAdapter.fetch_outrights failed: %s", exc)
            return []

        now = datetime.now(timezone.utc)
        lines: list[OddsLine] = []

        for event in events:
            for bm in event.get("bookmakers", []):
                book_title = bm.get("title", "unknown")
                for market in bm.get("markets", []):
                    if market.get("key") != "outrights":
                        continue
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = float(outcome.get("price", 0.0))
                        code = to_code(name)
                        if code is None:
                            # Skip "No Winner", "Field", or unknown teams
                            logger.debug(
                                "TheOddsApiAdapter.fetch_outrights: skipping %r", name
                            )
                            continue
                        lines.append(OddsLine(
                            market_key="outright",
                            book=book_title,
                            selection=code,
                            dec=price,
                            captured_at=now,
                        ))

        return lines
