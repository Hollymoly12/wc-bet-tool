"""Derive the real WC2026 team universe from h2h OddsLines.

derive_universe(odds_lines) clusters matchups into groups and returns
structured metadata when exactly 12 groups of 4 are found.

Group letters (A–L) are assigned by sorting clusters by their minimum team
code (lexicographic), giving a deterministic assignment regardless of which
cluster the API returns first.
"""
from __future__ import annotations

import logging

from app.providers.base import OddsLine
from app.seed import seed_data

logger = logging.getLogger(__name__)

_NEUTRAL_STR = 60.0


# ---------------------------------------------------------------------------
# Union-Find for connected components
# ---------------------------------------------------------------------------

class _UF:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def _ensure(self, x: str) -> None:
        if x not in self._parent:
            self._parent[x] = x

    def find(self, x: str) -> str:
        self._ensure(x)
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        self._ensure(a)
        self._ensure(b)
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[rb] = ra

    def components(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for node in self._parent:
            root = self.find(node)
            out.setdefault(root, set()).add(node)
        return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def derive_universe(odds_lines: list[OddsLine]) -> dict | None:
    """Derive the real WC2026 team universe from h2h OddsLines.

    Parses market_keys of the form ``h2h:{HOME}_{AWAY}`` and builds an
    adjacency graph.  If exactly 12 connected components of size 4 are found
    the universe is returned; otherwise returns None (seed path applies).

    Args:
        odds_lines: All OddsLine objects fetched by the odds provider.

    Returns:
        dict with keys ``teams`` (list of team dicts) and ``group_of``
        (code → letter mapping), or None if the structure doesn't match the
        12 × 4 WC2026 format.
    """
    uf = _UF()

    for line in odds_lines:
        key = line.market_key
        if not key.startswith("h2h:"):
            continue
        # market_key format: "h2h:{HOME}_{AWAY}"
        body = key[4:]  # strip "h2h:"
        parts = body.split("_", 1)
        if len(parts) != 2:
            continue
        home_code, away_code = parts
        if home_code and away_code:
            uf.union(home_code, away_code)

    components = uf.components()
    clusters = [members for members in components.values() if len(members) == 4]

    if len(clusters) != 12:
        logger.debug(
            "derive_universe: found %d clusters of size 4 (need 12) — using seed",
            len(clusters),
        )
        return None

    # Verify total team count is exactly 48
    all_codes: set[str] = set()
    for c in clusters:
        all_codes.update(c)
    if len(all_codes) != 48:
        logger.debug(
            "derive_universe: %d unique teams (need 48) — using seed", len(all_codes)
        )
        return None

    # Assign group letters A–L by sorting clusters by their lexicographic
    # minimum code, giving deterministic letter assignment.
    sorted_clusters = sorted(clusters, key=lambda c: min(c))
    letter_for_cluster = {
        i: chr(ord("A") + i) for i in range(12)
    }

    teams: list[dict] = []
    group_of: dict[str, str] = {}

    for idx, cluster in enumerate(sorted_clusters):
        letter = letter_for_cluster[idx]
        for code in sorted(cluster):
            name = seed_data.NAMES.get(code, code)
            colors = seed_data.COLORS.get(code, ["#888888", "#FFFFFF"])
            teams.append({
                "code": code,
                "name": name,
                "group": letter,
                "colors": colors,
                "str0": _NEUTRAL_STR,
            })
            group_of[code] = letter

    logger.info(
        "derive_universe: real mode — 48 teams across 12 groups resolved"
    )
    return {"teams": teams, "group_of": group_of}
