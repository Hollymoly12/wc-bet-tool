"""InjuriesNewsProvider — fetches injury/suspension news from API-Football.

Uses the /injuries endpoint filtered by league=1&season=2026.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.providers.base import NewsItem
from app.providers.teamnames import to_code

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0
_LEAGUE = 1
_SEASON = 2026

# Keywords that indicate a suspension rather than an injury
_SUSPENSION_KEYWORDS = {"suspension", "suspended", "ban", "banned", "yellow card", "red card"}


def _is_suspension(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _SUSPENSION_KEYWORDS)


class InjuriesNewsProvider:
    """Fetches injury/suspension news from API-Football."""

    def __init__(self) -> None:
        s = get_settings()
        self._base = s.api_football_base.rstrip("/")
        self._key = s.api_football_key

    # ------------------------------------------------------------------
    # Internal HTTP helper (monkeypatchable in tests)
    # ------------------------------------------------------------------
    def _get(self, url: str, params: dict) -> dict:
        headers = {"x-apisports-key": self._key}
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def fetch_news(self) -> list[NewsItem]:
        """Fetch injury/suspension items and return as NewsItem list."""
        url = f"{self._base}/injuries"
        params = {"league": _LEAGUE, "season": _SEASON}

        try:
            data = self._get(url, params)
        except Exception as exc:
            logger.error("InjuriesNewsProvider.fetch_news failed: %s", exc)
            return []

        now = datetime.now(timezone.utc)
        out: list[NewsItem] = []

        for item in data.get("response", []):
            team_info = item.get("team", {})
            team_name = team_info.get("name", "")
            code = to_code(team_name)
            if code is None:
                logger.warning(
                    "InjuriesNewsProvider: skipping injury — unresolved team %r",
                    team_name,
                )
                continue

            player_info = item.get("player", {})
            player_name = player_info.get("name", "Unknown player")

            fixture_info = item.get("fixture", {})
            # reason / type from the injury fields
            reason = item.get("reason") or item.get("type") or "Unknown reason"

            tag = "susp" if _is_suspension(reason) else "injury"
            text = f"{player_name}: {reason}"

            out.append(NewsItem(
                code=code,
                tag=tag,
                text=text,
                source="API-Football",
                url="",
                published_at=now,
            ))

        return out
