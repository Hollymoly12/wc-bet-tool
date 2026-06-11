"""Unit tests for WikiResultsProvider.

All tests monkeypatch ``WikiResultsProvider._get`` to return synthetic wikitext
— no network calls are made.  The conftest ``_hermetic_seed_mode`` fixture also
sets ``WIKI_RESULTS_ENABLED=0`` so even if ingestion is exercised, no real
Wikipedia fetch can occur.
"""
from __future__ import annotations

from app.providers.wiki_results import (
    WikiResultsProvider,
    _extract_football_boxes,
    _parse_box,
)

# ---------------------------------------------------------------------------
# Synthetic wikitext fixtures
# ---------------------------------------------------------------------------

# A minimal qualification page with:
#   1. A real result between two WC 2026 teams (ARG vs BRA) — should parse
#   2. A result where one team is not in our 48 (BOL = Bolivia) — should skip
#   3. A future/unplayed match (no score) — should skip
#   4. Correct nesting: {{Start date|...}} and {{fb|...}} inside {{Football box}}
_SAMPLE_WIKITEXT = """\
Some intro text.

=== Group A ===

{{Football box
|id         = ARG v BRA
|date       = {{Start date|2023|9|7|df=y}}
|team1      = {{fb-rt|ARG}}
|score      = 1–0
|team2      = {{fb|BRA}}
|goals1     = {{goal|15|Messi}}
|goals2     =
|stadium    = Estadio Monumental
|city       = Buenos Aires
|attendance = 83000
|referee    = Howard Webb
}}

{{Football box
|id         = COL v BOL
|date       = {{Start date|2023|10|12|df=y}}
|team1      = {{fb-rt|COL}}
|score      = 2–1
|team2      = {{fb|BOL}}
|stadium    = Estadio Metropolitano
|city       = Barranquilla
}}

{{Football box
|id         = URU v VEN
|date       = {{Start date|2026|9|5|df=y}}
|team1      = {{fb-rt|URU}}
|score      = TBD
|team2      = {{fb|VEN}}
|stadium    = Estadio Centenario
|city       = Montevideo
}}

{{Football box
|id         = COL v ARG
|date       = {{Start date|2024|6|11|df=y}}
|team1      = {{fb-rt|COL}}
|score      = 1–2
|team2      = {{fb|ARG}}
|stadium    = Estadio Metropolitano
|city       = Barranquilla
}}
"""

# A page with nested templates to specifically exercise the brace matcher.
# {{Start date}} is nested inside {{Football box}}, which itself contains
# further fb templates — exactly the pattern that breaks naive regex.
_NESTED_WIKITEXT = """\
{{Football box
|date       = {{Start date|2024|3|26|df=y}}
|team1      = {{fbw-rt|ESP}}
|score      = 3–3
|team2      = {{fbw|BRA}}
|goals1     = {{goal|5|Morata}}{{goal|33|Yamal}}{{goal|87|Williams}}
|goals2     = {{goal|12|Vinicius}}{{goal|45|Rodrygo}}{{goal|90|Paqueta}}
|stadium    = Estadio Santiago Bernabéu
}}
"""


def _make_fake_get(wikitext: str):
    """Return a fake _get that returns the right MediaWiki JSON structure."""
    def _fake(self, url: str) -> dict:  # noqa: ARG001
        return {"parse": {"wikitext": wikitext}}
    return _fake


# ---------------------------------------------------------------------------
# Brace-matcher unit tests
# ---------------------------------------------------------------------------

class TestExtractFootballBoxes:
    def test_extracts_all_boxes(self):
        boxes = _extract_football_boxes(_SAMPLE_WIKITEXT)
        # 4 {{Football box}} blocks in the sample
        assert len(boxes) == 4

    def test_box_starts_and_ends_correctly(self):
        boxes = _extract_football_boxes(_SAMPLE_WIKITEXT)
        for box in boxes:
            assert box.startswith("{{Football box")
            assert box.endswith("}}")

    def test_nested_templates_handled(self):
        """The brace matcher must not stop at the }} closing {{Start date}}."""
        boxes = _extract_football_boxes(_NESTED_WIKITEXT)
        assert len(boxes) == 1
        box = boxes[0]
        # Must include the nested {{Start date}} — not truncated
        assert "Start date" in box
        assert "fbw-rt" in box or "fbw" in box

    def test_no_boxes_returns_empty(self):
        assert _extract_football_boxes("No football boxes here.") == []


# ---------------------------------------------------------------------------
# Box parser unit tests
# ---------------------------------------------------------------------------

class TestParseBox:
    def test_valid_result_parsed(self):
        box = """\
{{Football box
|date       = {{Start date|2023|9|7|df=y}}
|team1      = {{fb-rt|ARG}}
|score      = 1–0
|team2      = {{fb|BRA}}
}}"""
        dto = _parse_box(box)
        assert dto is not None
        assert dto.home == "ARG"
        assert dto.away == "BRA"
        assert dto.home_goals == 1
        assert dto.away_goals == 0
        assert dto.days_ago >= 0
        assert dto.competition == "WC2026 Qualifying"

    def test_non_wc_team_skipped(self):
        """Bolivia (BOL) is not in our 48 → box must return None."""
        box = """\
{{Football box
|date       = {{Start date|2023|10|12|df=y}}
|team1      = {{fb-rt|COL}}
|score      = 2–1
|team2      = {{fb|BOL}}
}}"""
        assert _parse_box(box) is None

    def test_no_score_box_skipped(self):
        """A future/unplayed match has no numeric score → None."""
        box = """\
{{Football box
|date       = {{Start date|2026|9|5|df=y}}
|team1      = {{fb-rt|URU}}
|score      = TBD
|team2      = {{fb|VEN}}
}}"""
        assert _parse_box(box) is None

    def test_hyphen_score_separator(self):
        """Accept plain hyphen ``-`` as well as en-dash ``–``."""
        box = """\
{{Football box
|date       = {{Start date|2024|1|15|df=y}}
|team1      = {{fb-rt|ESP}}
|score      = 2-1
|team2      = {{fb|FRA}}
}}"""
        dto = _parse_box(box)
        assert dto is not None
        assert dto.home_goals == 2
        assert dto.away_goals == 1

    def test_days_ago_non_negative(self):
        """days_ago must be >= 0 for a past match."""
        box = """\
{{Football box
|date       = {{Start date|2024|3|26|df=y}}
|team1      = {{fbw-rt|ESP}}
|score      = 3–3
|team2      = {{fbw|BRA}}
}}"""
        dto = _parse_box(box)
        assert dto is not None
        assert dto.days_ago >= 0

    def test_draw_parsed(self):
        box = """\
{{Football box
|date       = {{Start date|2023|6|20|df=y}}
|team1      = {{fb-rt|COL}}
|score      = 0–0
|team2      = {{fb|URU}}
}}"""
        dto = _parse_box(box)
        assert dto is not None
        assert dto.home_goals == 0
        assert dto.away_goals == 0


# ---------------------------------------------------------------------------
# WikiResultsProvider integration-style tests (monkeypatched)
# ---------------------------------------------------------------------------

class TestWikiResultsProvider:
    def test_fetch_results_correct_count(self, monkeypatch):
        """Sample wikitext has 4 boxes: 2 with both teams valid, 1 non-WC team, 1 future.
        Expect exactly 2 results (ARG v BRA and COL v ARG)."""
        monkeypatch.setattr(WikiResultsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        provider = WikiResultsProvider()
        # Override _PAGES to only query once (avoids multiple fake calls)
        monkeypatch.setattr(
            "app.providers.wiki_results._PAGES",
            ["2026 FIFA World Cup qualification (CONMEBOL)"],
        )
        results = provider.fetch_results()
        assert len(results) == 2

    def test_codes_are_valid(self, monkeypatch):
        """All returned team codes must be in our 48-team set."""
        from app.seed.seed_data import NAMES
        monkeypatch.setattr(WikiResultsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        monkeypatch.setattr(
            "app.providers.wiki_results._PAGES",
            ["2026 FIFA World Cup qualification (CONMEBOL)"],
        )
        results = WikiResultsProvider().fetch_results()
        valid = set(NAMES.keys())
        for r in results:
            assert r.home in valid, f"home code {r.home!r} not in valid set"
            assert r.away in valid, f"away code {r.away!r} not in valid set"

    def test_days_ago_non_negative(self, monkeypatch):
        """Every result's days_ago must be >= 0 (past match)."""
        monkeypatch.setattr(WikiResultsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        monkeypatch.setattr(
            "app.providers.wiki_results._PAGES",
            ["2026 FIFA World Cup qualification (CONMEBOL)"],
        )
        results = WikiResultsProvider().fetch_results()
        for r in results:
            assert r.days_ago >= 0, f"days_ago={r.days_ago} should be >= 0"

    def test_dedup_across_pages(self, monkeypatch):
        """If the same match appears on two pages, it should only appear once."""
        # Use the same wikitext for both pages
        call_count = 0

        def _fake_get(self, url: str) -> dict:  # noqa: ARG001
            nonlocal call_count
            call_count += 1
            return {"parse": {"wikitext": _SAMPLE_WIKITEXT}}

        monkeypatch.setattr(WikiResultsProvider, "_get", _fake_get)
        monkeypatch.setattr(
            "app.providers.wiki_results._PAGES",
            [
                "2026 FIFA World Cup qualification (CONMEBOL)",
                "2026 FIFA World Cup qualification (UEFA)",
            ],
        )
        results = WikiResultsProvider().fetch_results()
        # 2 valid matches per page, but duplicates deduped → still 2
        assert len(results) == 2
        assert call_count == 2  # both pages were fetched

    def test_returns_empty_on_total_failure(self, monkeypatch):
        """If every page fetch fails, return [] (never raise)."""
        def _fail(self, url: str):
            raise RuntimeError("network error")

        monkeypatch.setattr(WikiResultsProvider, "_get", _fail)
        monkeypatch.setattr(
            "app.providers.wiki_results._PAGES",
            ["2026 FIFA World Cup qualification (CONMEBOL)"],
        )
        results = WikiResultsProvider().fetch_results()
        assert results == []

    def test_partial_page_failure_continues(self, monkeypatch):
        """If one page fails and another succeeds, return the successful page's results."""
        pages = [
            "2026 FIFA World Cup qualification (CONMEBOL)",
            "2026 FIFA World Cup qualification (UEFA)",
        ]
        monkeypatch.setattr("app.providers.wiki_results._PAGES", pages)

        call_count = 0

        def _sometimes_fail(self, url: str) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("first page failed")
            return {"parse": {"wikitext": _SAMPLE_WIKITEXT}}

        monkeypatch.setattr(WikiResultsProvider, "_get", _sometimes_fail)
        results = WikiResultsProvider().fetch_results()
        # First page failed, second page gave 2 valid results
        assert len(results) == 2

    def test_nested_templates_parsed(self, monkeypatch):
        """Deeply nested {{Start date}} and {{fbw}} templates must be handled correctly."""
        monkeypatch.setattr(WikiResultsProvider, "_get", _make_fake_get(_NESTED_WIKITEXT))
        monkeypatch.setattr(
            "app.providers.wiki_results._PAGES",
            ["2026 FIFA World Cup qualification (UEFA)"],
        )
        results = WikiResultsProvider().fetch_results()
        assert len(results) == 1
        r = results[0]
        assert r.home == "ESP"
        assert r.away == "BRA"
        assert r.home_goals == 3
        assert r.away_goals == 3

    def test_competition_label(self, monkeypatch):
        """ResultDTOs must carry the WC2026 Qualifying competition label."""
        monkeypatch.setattr(WikiResultsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        monkeypatch.setattr(
            "app.providers.wiki_results._PAGES",
            ["2026 FIFA World Cup qualification (CONMEBOL)"],
        )
        results = WikiResultsProvider().fetch_results()
        for r in results:
            assert r.competition == "WC2026 Qualifying"
