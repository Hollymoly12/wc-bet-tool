"""Wikipedia-based squads provider for WC 2026.

Scrapes the official Wikipedia "2026 FIFA World Cup squads" page via the
MediaWiki action API (no key required).  Returns squads in the same format
as seed_data.SQUADS so it can be used as a drop-in replacement.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

from app.providers.teamnames import to_code
from app.seed import seed_data

logger = logging.getLogger(__name__)

_WIKI_API_URL = (
    "https://en.wikipedia.org/w/api.php"
    "?action=parse"
    "&page=2026_FIFA_World_Cup_squads"
    "&format=json"
    "&prop=wikitext"
    "&formatversion=2"
)

_TIMEOUT = 20.0
_MAX_RETRIES = 3
_RETRY_BACKOFF_S = 8.0

# Wikipedia position → our position string
_POS_MAP: dict[str, str] = {
    "GK": "GK",
    "DF": "CB",
    "MF": "CM",
    "FW": "ST",
}

# Non-team section headers to skip
_SKIP_HEADERS = frozenset(
    [
        "Age",
        "Player representation by club",
        "Player representation by league system",
        "Player representation by club confederation",
        "Average age of squads",
        "Coach representation by country",
    ]
)

# Starting XI quota by position (GK, DEF, MID, FWD)
_XI_QUOTA = {"GK": 1, "CB": 4, "CM": 3, "ST": 3}
_XI_TOTAL = 11


def _strip_link(val: str) -> str:
    """Strip a ``[[...]]`` wiki link.  For ``[[A|B]]`` returns ``B``."""
    val = val.strip()
    m = re.search(r"\[\[([^\]]+)\]\]", val)
    if not m:
        return val
    inner = m.group(1)
    if "|" in inner:
        return inner.split("|", 1)[1].strip()
    return inner.strip()


def _parse_player_line(line: str) -> tuple[int, str, str, str] | None:
    """Parse a ``{{nat fs g player|...}}`` line.

    Returns ``(no, pos_mapped, name, club)`` or ``None`` if the line cannot
    be parsed.
    """
    no_m = re.search(r"\bno=(\d+)", line)
    pos_m = re.search(r"\bpos=(GK|DF|MF|FW)", line)
    name_m = re.search(r"\bname=(\[\[[^\]]*\]\])", line)
    club_m = re.search(r"\bclub=(\[\[[^\]]*\]\])", line)

    if not (no_m and pos_m and name_m and club_m):
        return None

    no = int(no_m.group(1))
    wiki_pos = pos_m.group(1)
    pos = _POS_MAP.get(wiki_pos, "ST")
    name = _strip_link(name_m.group(1))
    club = _strip_link(club_m.group(1))

    if not name or not club:
        return None

    return no, pos, name, club


def _build_xi(players: list[list[Any]]) -> list[list[Any]]:
    """Return the squad reordered: first-11 projected XI then the bench.

    XI = 1 GK + 4 CB + 3 CM + 3 ST, filled from the squad in jersey-number
    order.  If a position line is short, bench players of any position backfill
    to reach exactly 11.
    """
    by_pos: dict[str, list[list[Any]]] = {"GK": [], "CB": [], "CM": [], "ST": []}
    for p in players:
        pos = p[2]
        by_pos.setdefault(pos, []).append(p)

    xi: list[list[Any]] = []
    used: set[int] = set()  # indices into `players`

    # Fill by quota in canonical order
    for pos_key in ("GK", "CB", "CM", "ST"):
        quota = _XI_QUOTA[pos_key]
        pool = by_pos.get(pos_key, [])
        for p in pool[:quota]:
            xi.append(p)
            used.add(id(p))

    # If still < 11 (a position was short), backfill from any remaining
    if len(xi) < _XI_TOTAL:
        for p in players:
            if id(p) not in used:
                xi.append(p)
                used.add(id(p))
                if len(xi) == _XI_TOTAL:
                    break

    bench = [p for p in players if id(p) not in used]
    return xi + bench


class WikiSquadsProvider:
    """Fetches real WC 2026 squads from Wikipedia (no API key needed)."""

    def _get(self, url: str) -> dict:
        """HTTP GET *url*, return parsed JSON.  Retries on HTTP 429 (Wikipedia
        rate-limit) with backoff.  Separated for easy monkeypatching."""
        headers = {
            # Wikipedia requires a descriptive User-Agent or it rate-limits hard.
            "User-Agent": (
                "WCBetTool/1.0 (World Cup 2026 betting tool; "
                "https://github.com/Hollymoly12/wc-bet-tool)"
            ),
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        }
        for attempt in range(_MAX_RETRIES):
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 429 and attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_BACKOFF_S * (attempt + 1))
                    continue
                resp.raise_for_status()
                return resp.json()
        raise RuntimeError("wiki_squads: exhausted retries")  # pragma: no cover

    def fetch_squads(self) -> dict[str, list]:
        """Fetch and parse squads.  Returns ``{}`` on any failure (caller uses seed)."""
        try:
            return self._fetch_squads_inner()
        except Exception as exc:
            logger.warning("WikiSquadsProvider.fetch_squads failed: %s", exc)
            return {}

    def _fetch_squads_inner(self) -> dict[str, list]:
        data = self._get(_WIKI_API_URL)
        wikitext: str = data["parse"]["wikitext"]

        # Split by any == header; capture the header in the list
        parts = re.split(r"(==+\s*[^=]+\s*==+)", wikitext)

        result: dict[str, list] = {}
        teams_parsed = 0
        total_players = 0

        i = 0
        while i < len(parts):
            part = parts[i]
            # Is this a level-3 (===) header?
            header_m = re.match(r"^===\s*(.+?)\s*===$", part.strip())
            if header_m:
                header_name = header_m.group(1).strip()
                content = parts[i + 1] if i + 1 < len(parts) else ""
                i += 2

                # Skip non-team sections
                if header_name in _SKIP_HEADERS:
                    continue

                code = to_code(header_name)
                if code is None:
                    logger.debug(
                        "WikiSquadsProvider: skipping unrecognised section %r",
                        header_name,
                    )
                    continue

                # Extract player lines (both nat fs g player and nat fs player)
                raw_players: list[list[Any]] = []
                for line in content.split("\n"):
                    line = line.strip()
                    if not (
                        line.startswith("{{nat fs g player")
                        or line.startswith("{{nat fs player")
                    ):
                        continue
                    parsed = _parse_player_line(line)
                    if parsed is None:
                        continue
                    no, pos, name, club = parsed
                    raw_players.append([no, name, pos, club])

                if len(raw_players) < _XI_TOTAL:
                    logger.debug(
                        "WikiSquadsProvider: %s — only %d players, skipping",
                        code,
                        len(raw_players),
                    )
                    continue

                # Sort by jersey number before building XI
                raw_players.sort(key=lambda p: p[0])

                ordered = _build_xi(raw_players)

                # Formation: reuse seed if available, else default
                seed_squad = seed_data.SQUADS.get(code)
                formation = seed_squad[0] if seed_squad else "4-3-3"

                result[code] = [formation, ordered]
                teams_parsed += 1
                total_players += len(ordered)
            else:
                i += 1

        logger.info(
            "WikiSquadsProvider: parsed %d teams, %d total players",
            teams_parsed,
            total_players,
        )
        return result
