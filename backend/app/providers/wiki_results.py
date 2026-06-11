"""Wikipedia-based recent international results provider for WC 2026.

Scrapes WC 2026 qualification pages (CONMEBOL, UEFA, AFC, CAF, CONCACAF, OFC)
via the MediaWiki action API (no key required).  Returns ResultDTOs for use in
model calibration alongside the existing API-Football 2022-2024 data.

Key design note — brace-matched extraction:
  A naive regex like ``{{Football box.*?}}`` BREAKS because each Football box
  contains *nested* templates (``{{Start date|...}}``, ``{{fb|...}}``, etc.).
  We use a character-level depth scanner instead: find ``{{Football box``, then
  walk forward counting ``{{`` (+1) and ``}}`` (-1) until depth returns to 0.
  This correctly handles arbitrary nesting depth.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import date
from urllib.parse import quote

import httpx

from app.providers.base import ResultDTO
from app.seed import seed_data

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_TIMEOUT = 20.0
_MAX_RETRIES = 3
_RETRY_BACKOFF_S = 8.0
_PAGE_DELAY_S = 1.0  # polite delay between the ~25 sub-page fetches (avoids 429)

_WIKI_API_BASE = "https://en.wikipedia.org/w/api.php"

# Match results live in {{Football box}} templates. CONMEBOL (single round-robin)
# has them on its main page; the other confederations split matches onto per-group
# sub-pages titled "<qual> – <CONF> Group <X>" (en-dash). We enumerate generously
# and skip any page that 404s (fetch_results tolerates per-page failures).
_QUAL = "2026 FIFA World Cup qualification"
_PAGES: list[str] = (
    [f"{_QUAL} (CONMEBOL)"]                                    # single round-robin
    + [f"{_QUAL} – UEFA Group {g}" for g in "ABCDEFGHIJKL"]    # 12 group sub-pages
    + [f"{_QUAL} – CAF Group {g}" for g in "ABCDEFGHI"]        # 9 group sub-pages
    + [f"{_QUAL} – AFC second round", f"{_QUAL} – AFC third round"]  # single pages
    + [f"{_QUAL} – CONCACAF third round"]
)

# ---------------------------------------------------------------------------
# FIFA code aliases — Wikipedia occasionally uses a different 3-letter code
# than our seed.  Map Wikipedia code → our code.  Only entries that differ.
# ---------------------------------------------------------------------------
_CODE_ALIASES: dict[str, str] = {
    # Wikipedia uses "KVX" or "KOS" for Kosovo; not a WC participant → no alias needed
    # Wikipedia uses "EQG" for Equatorial Guinea → not in our 48
    # Wikipedia uses "PHI" for Philippines → not in our 48
    # Wikipedia uses "TPE" for Chinese Taipei → not in our 48
    # CONCACAF: Wikipedia uses "TRI" for Trinidad & Tobago → not in our 48
    # Wikipedia uses "HON" for Honduras → not in our 48
    # CAF: "CGO" = Republic of Congo → not in our 48
    # A handful of UEFA codes differ from FIFA standard:
    "NIR": "NIR",   # Northern Ireland — not in our 48, but identity mapping is harmless
    # South Korea: Wikipedia uses "KOR" (same as ours) ✓
    # Iran: Wikipedia uses "IRN" (same as ours) ✓
    # Ivory Coast: Wikipedia uses "CIV" (same as ours) ✓
    # Türkiye: Wikipedia uses "TUR" (same as ours) ✓
    # DR Congo: Wikipedia uses "COD" (same as ours) ✓
    # Cape Verde: Wikipedia uses "CPV" (same as ours) ✓
    # Bosnia: Wikipedia uses "BIH" (same as ours) ✓
    # Curaçao: Wikipedia uses "CUW" (same as ours) ✓
    # Saudi Arabia: Wikipedia uses "KSA" (same as ours) ✓
}

# Set of valid team codes in our model (computed once at import time)
_VALID_CODES: frozenset[str] = frozenset(seed_data.NAMES)


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _build_url(page_title: str) -> str:
    encoded = quote(page_title.replace(" ", "_"), safe="()")
    return (
        f"{_WIKI_API_BASE}"
        f"?action=parse"
        f"&page={encoded}"
        f"&format=json"
        f"&prop=wikitext"
        f"&formatversion=2"
        f"&redirects=1"
    )


# ---------------------------------------------------------------------------
# Brace-matched extraction of {{Football box … }} blocks
# ---------------------------------------------------------------------------

def _extract_football_boxes(wikitext: str) -> list[str]:
    """Return a list of raw wikitext strings, one per ``{{Football box ...}}`` block.

    Uses a character-level depth scanner to correctly handle nested templates
    such as ``{{Start date|...}}`` and ``{{fb|...}}``.  A naive regex would
    stop at the first ``}}`` (closing a nested template) rather than the outer
    Football box close.
    """
    marker = "{{Football box"
    boxes: list[str] = []
    search_from = 0

    while True:
        start = wikitext.find(marker, search_from)
        if start == -1:
            break

        # Walk forward balancing {{ / }}
        depth = 0
        i = start
        end = -1
        length = len(wikitext)

        while i < length - 1:
            if wikitext[i] == "{" and wikitext[i + 1] == "{":
                depth += 1
                i += 2
            elif wikitext[i] == "}" and wikitext[i + 1] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 2  # include the closing }}
                    break
                i += 2
            else:
                i += 1

        if end == -1:
            # Malformed — skip and keep searching from after the marker
            search_from = start + len(marker)
            continue

        boxes.append(wikitext[start:end])
        search_from = end

    return boxes


# ---------------------------------------------------------------------------
# Field parsers
# ---------------------------------------------------------------------------

# Matches: {{fb|ARG}}, {{fb-rt|COL}}, {{fbw|VEN}}, {{fbw-rt|ESP}}, {{fb-rt|PAR}}
# We just grab the first and second 3-letter code appearing in fb* templates.
_FB_RE = re.compile(r"\{\{fb[a-z-]*\s*\|\s*([A-Z]{3})", re.IGNORECASE)
_SCORE_RE = re.compile(r"\|\s*score\s*=\s*(\d+)\s*[–\-]\s*(\d+)")
_DATE_RE = re.compile(r"\{\{Start date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})")


def _parse_box(box: str) -> ResultDTO | None:
    """Parse a single ``{{Football box ...}}`` block into a ResultDTO.

    Returns None if the box has no valid numeric score (future/void match),
    no recognisable team codes, or both teams are outside our 48-team set.
    """
    # --- Score ---
    score_m = _SCORE_RE.search(box)
    if not score_m:
        return None  # future match or void — no numeric score
    home_goals = int(score_m.group(1))
    away_goals = int(score_m.group(2))

    # --- Teams ---
    fb_matches = _FB_RE.findall(box)
    if len(fb_matches) < 2:
        return None
    raw_home = fb_matches[0].upper()
    raw_away = fb_matches[1].upper()

    # Apply aliases
    home_code = _CODE_ALIASES.get(raw_home, raw_home)
    away_code = _CODE_ALIASES.get(raw_away, raw_away)

    # Skip if neither team is in our 48 (saves filtering later; we need BOTH)
    if home_code not in _VALID_CODES or away_code not in _VALID_CODES:
        return None

    # --- Date ---
    date_m = _DATE_RE.search(box)
    if date_m:
        match_date = date(int(date_m.group(1)), int(date_m.group(2)), int(date_m.group(3)))
        today = date.today()
        days_ago = (today - match_date).days
        if days_ago < 0:
            # Future match — skip
            return None
    else:
        days_ago = 365  # fallback: treat as ~1 year old if date missing

    return ResultDTO(
        home=home_code,
        away=away_code,
        home_goals=home_goals,
        away_goals=away_goals,
        days_ago=float(days_ago),
        competition="WC2026 Qualifying",
    )


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class WikiResultsProvider:
    """Fetches recent WC 2026 qualification results from Wikipedia.

    No API key required.  Returns ResultDTOs to augment the API-Football
    2022-2024 calibration data with fresher 2023-2025 form.
    """

    def _get(self, url: str) -> dict:
        """HTTP GET *url*, return parsed JSON.

        Retries up to ``_MAX_RETRIES`` times on HTTP 429 (Wikipedia rate-limit)
        with exponential-ish backoff.  Separated into its own method so tests
        can monkeypatch it without touching the network.
        """
        headers = {
            "User-Agent": (
                "WCBetTool/1.0 (https://github.com/Hollymoly12/wc-bet-tool)"
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
        raise RuntimeError("wiki_results: exhausted retries")  # pragma: no cover

    def _fetch_page(self, page_title: str) -> list[ResultDTO]:
        """Fetch one qualification page and return parsed results."""
        url = _build_url(page_title)
        data = self._get(url)
        wikitext: str = data["parse"]["wikitext"]
        boxes = _extract_football_boxes(wikitext)

        results: list[ResultDTO] = []
        for box in boxes:
            dto = _parse_box(box)
            if dto is not None:
                results.append(dto)

        logger.info(
            "wiki_results: %s — %d boxes, %d valid results",
            page_title,
            len(boxes),
            len(results),
        )
        return results

    def fetch_results(self) -> list[ResultDTO]:
        """Fetch qualification results from all confederation pages.

        Failures on individual pages are logged and skipped (partial data ok).
        Returns an empty list only if every page fails.
        """
        all_results: list[ResultDTO] = []
        seen: set[tuple[str, str, float]] = set()

        for i, page_title in enumerate(_PAGES):
            if i:
                time.sleep(_PAGE_DELAY_S)  # be polite across ~37 sub-pages
            try:
                page_results = self._fetch_page(page_title)
            except Exception as exc:
                logger.warning(
                    "wiki_results: failed to fetch %r — %s", page_title, exc
                )
                continue

            for dto in page_results:
                key = (dto.home, dto.away, dto.days_ago)
                if key not in seen:
                    seen.add(key)
                    all_results.append(dto)

        logger.info(
            "wiki_results: total %d results across %d pages",
            len(all_results),
            len(_PAGES),
        )
        return all_results
