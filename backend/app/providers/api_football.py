"""API-Football adapter — real FootballProvider for WC 2026 fixtures/results/squads.

Uses the v3.football.api-sports.io endpoint (league=1, season=2026).
Adapters are pure/stateless: no DB writes here.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone

import httpx
from dateutil import parser as du_parser

from app.config import get_settings
from app.providers.base import FixtureDTO, ResultDTO
from app.providers.teamnames import fixture_id, to_code
from app.seed import seed_data

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0
_LEAGUE = 1
_SEASON = 2026


class ApiFootballAdapter:
    """Fetches fixtures, results, and squads from API-Football."""

    def __init__(self) -> None:
        s = get_settings()
        self._base = s.api_football_base.rstrip("/")
        self._key = s.api_football_key

    # ------------------------------------------------------------------
    # Internal HTTP helper (easy to monkeypatch in tests)
    # ------------------------------------------------------------------
    def _get(self, url: str, params: dict) -> dict:
        """GET url with API-Football headers, return parsed JSON dict."""
        headers = {"x-apisports-key": self._key}
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def fetch_fixtures(self) -> list[FixtureDTO]:
        """Fetch all WC 2026 fixtures and return as FixtureDTO list."""
        url = f"{self._base}/fixtures"
        params = {"league": _LEAGUE, "season": _SEASON}

        try:
            data = self._get(url, params)
        except Exception as exc:
            logger.error("ApiFootballAdapter.fetch_fixtures failed: %s", exc)
            return []

        out: list[FixtureDTO] = []
        for item in data.get("response", []):
            teams = item.get("teams", {})
            home_name = teams.get("home", {}).get("name", "")
            away_name = teams.get("away", {}).get("name", "")

            home_code = to_code(home_name)
            away_code = to_code(away_name)
            if home_code is None or away_code is None:
                logger.warning(
                    "ApiFootballAdapter: skipping fixture — unresolved team(s) %r vs %r",
                    home_name, away_name,
                )
                continue

            fid = fixture_id(home_code, away_code)

            fixture_info = item.get("fixture", {})
            date_str = fixture_info.get("date", "")
            try:
                kickoff: datetime | None = du_parser.parse(date_str).astimezone(timezone.utc)
            except Exception:
                kickoff = None

            league_info = item.get("league", {})
            # league.round looks like "Group Stage - 1" or "Quarter-finals"
            round_str = league_info.get("round", "")

            venue_info = fixture_info.get("venue", {})
            venue = venue_info.get("name", "") or ""

            out.append(FixtureDTO(
                id=fid,
                home=home_code,
                away=away_code,
                group=round_str,
                stage="group",
                kickoff=kickoff,
                venue=venue,
            ))

        return out

    def fetch_results(self) -> list[ResultDTO]:
        """Fetch finished WC 2026 fixtures and return as ResultDTO list."""
        url = f"{self._base}/fixtures"
        params = {"league": _LEAGUE, "season": _SEASON, "status": "FT"}

        try:
            data = self._get(url, params)
        except Exception as exc:
            logger.error("ApiFootballAdapter.fetch_results failed: %s", exc)
            return []

        now = datetime.now(timezone.utc)
        out: list[ResultDTO] = []
        for item in data.get("response", []):
            teams = item.get("teams", {})
            home_name = teams.get("home", {}).get("name", "")
            away_name = teams.get("away", {}).get("name", "")

            home_code = to_code(home_name)
            away_code = to_code(away_name)
            if home_code is None or away_code is None:
                logger.warning(
                    "ApiFootballAdapter: skipping result — unresolved team(s) %r vs %r",
                    home_name, away_name,
                )
                continue

            goals = item.get("goals", {})
            home_goals = int(goals.get("home") or 0)
            away_goals = int(goals.get("away") or 0)

            fixture_info = item.get("fixture", {})
            date_str = fixture_info.get("date", "")
            try:
                match_dt = du_parser.parse(date_str).astimezone(timezone.utc)
                days_ago = (now - match_dt).total_seconds() / 86400.0
            except Exception:
                days_ago = 0.0

            out.append(ResultDTO(
                home=home_code,
                away=away_code,
                home_goals=home_goals,
                away_goals=away_goals,
                days_ago=days_ago,
                competition="WC2026",
            ))

        return out

    def fetch_squads(self) -> dict[str, list]:
        """Return squads.

        NOTE: Fetching real squads requires per-team numeric IDs which are
        unavailable without a prior fixtures/teams lookup. Returning seed
        squads as a fully populated interim until a team-id mapping is
        implemented (see TODO below).

        TODO: Build a {code: team_id} map from the /teams endpoint filtered
        by league=1&season=2026, then call /players/squads?team={id} for each,
        and merge into the seed_data.SQUADS format.
        """
        return seed_data.SQUADS
