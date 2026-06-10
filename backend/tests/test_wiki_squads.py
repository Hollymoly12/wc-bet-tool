"""Unit tests for WikiSquadsProvider.

All tests monkeypatch ``WikiSquadsProvider._get`` to return a small synthetic
wikitext dict — no network calls are made.
"""
from __future__ import annotations

from app.providers.wiki_squads import WikiSquadsProvider

# ---------------------------------------------------------------------------
# Sample wikitext: 2 teams, various edge cases
# ---------------------------------------------------------------------------

_SCOTLAND_PLAYERS = """\
{{nat fs g player|no=1|pos=GK|name=[[Angus Gunn]]|sortname=Gunn, Angus|age={{birth date and age2|2026|6|11|1996|1|22}}|caps=22|goals=0|club=[[Nottingham Forest F.C.|Nottingham Forest]]|clubnat=ENG}}
{{nat fs g player|no=2|pos=DF|name=[[Aaron Hickey]]|sortname=Hickey, Aaron|age={{birth date and age2|2026|6|11|2002|6|10}}|caps=21|goals=0|club=[[Brentford F.C.|Brentford]]|clubnat=ENG}}
{{nat fs g player|no=3|pos=DF|name=[[Andy Robertson]]|sortname=Robertson, Andy|age={{birth date and age2|2026|6|11|1994|3|11}}|caps=94|goals=4|club=[[Liverpool F.C.|Liverpool]]|clubnat=ENG}}
{{nat fs g player|no=4|pos=MF|name=[[Scott McTominay]]|sortname=Mctominay, Scott|age={{birth date and age2|2026|6|11|1996|12|8}}|caps=60|goals=14|club=[[S.S.C. Napoli|Napoli]]|clubnat=ITA}}
{{nat fs g player|no=5|pos=DF|name=[[Grant Hanley]]|sortname=Hanley, Grant|age={{birth date and age2|2026|6|11|1991|11|20}}|caps=57|goals=2|club=[[Norwich City F.C.|Norwich City]]|clubnat=ENG}}
{{nat fs g player|no=6|pos=DF|name=[[Liam Cooper]]|sortname=Cooper, Liam|age={{birth date and age2|2026|6|11|1991|8|30}}|caps=29|goals=1|club=[[Coventry City F.C.|Coventry City]]|clubnat=ENG}}
{{nat fs g player|no=7|pos=FW|name=[[Lawrence Shankland]]|sortname=Shankland, Lawrence|age={{birth date and age2|2026|6|11|1995|10|10}}|caps=30|goals=15|club=[[Heart of Midlothian F.C.|Hearts]]|clubnat=SCO}}
{{nat fs g player|no=8|pos=MF|name=[[John McGinn]]|sortname=Mcginn, John|age={{birth date and age2|2026|6|11|1994|10|18}}|caps=70|goals=8|club=[[Aston Villa F.C.|Aston Villa]]|clubnat=ENG}}
{{nat fs g player|no=9|pos=FW|name=[[Lyndon Dykes]]|sortname=Dykes, Lyndon|age={{birth date and age2|2026|6|11|1995|10|7}}|caps=42|goals=16|club=[[Queens Park Rangers F.C.|Queens Park Rangers]]|clubnat=ENG}}
{{nat fs g player|no=10|pos=MF|name=[[Billy Gilmour]]|sortname=Gilmour, Billy|age={{birth date and age2|2026|6|11|2001|6|11}}|caps=27|goals=2|club=[[S.S.C. Napoli|Napoli]]|clubnat=ITA}}
{{nat fs g player|no=11|pos=FW|name=[[Che Adams]]|sortname=Adams, Che|age={{birth date and age2|2026|6|11|1996|7|13}}|caps=34|goals=8|club=[[AFC Bournemouth|Bournemouth]]|clubnat=ENG}}
{{nat fs g player|no=12|pos=GK|name=[[Craig Gordon]]|sortname=Gordon, Craig|age={{birth date and age2|2026|6|11|1982|12|31}}|caps=70|goals=0|club=[[Heart of Midlothian F.C.|Hearts]]|clubnat=SCO}}
{{nat fs g player|no=13|pos=DF|name=[[Kieran Tierney]]|sortname=Tierney, Kieran|age={{birth date and age2|2026|6|11|1997|6|5}}|caps=60|goals=3|club=[[Arsenal F.C.|Arsenal]]|clubnat=ENG}}
{{nat fs g player|no=14|pos=MF|name=[[Kenny McLean]]|sortname=Mclean, Kenny|age={{birth date and age2|2026|6|11|1992|1|8}}|caps=53|goals=2|club=[[Norwich City F.C.|Norwich City]]|clubnat=ENG}}
"""

# Czech Republic — uses pipe-in-club and pipe-in-name links; also uses nat fs player variant
_CZE_PLAYERS = """\
{{nat fs g player|no=1|pos=GK|name=[[Matěj Kovář]]|sortname=Kovar, Matej|age={{birth date and age2|2026|6|11|2000|5|17}}|caps=20|goals=0|club=[[PSV Eindhoven]]|clubnat=NED}}
{{nat fs g player|no=2|pos=DF|name=[[David Zima]]|sortname=Zima, David|age={{birth date and age2|2026|6|11|2000|11|8}}|caps=25|goals=1|club=[[SK Slavia Prague|Slavia Prague]]|clubnat=CZE}}
{{nat fs g player|no=3|pos=DF|name=[[Tomáš Holeš]]|sortname=Holes, Tomas|age={{birth date and age2|2026|6|11|1993|3|31}}|caps=41|goals=2|club=[[SK Slavia Prague|Slavia Prague]]|clubnat=CZE}}
{{nat fs g player|no=4|pos=DF|name=[[Robin Hranáč]]|sortname=Hranac, Robin|age={{birth date and age2|2026|6|11|2001|4|25}}|caps=15|goals=1|club=[[TSG 1899 Hoffenheim|TSG Hoffenheim]]|clubnat=GER}}
{{nat fs g player|no=5|pos=DF|name=[[Vladimír Coufal]]|sortname=Coufal, Vladimir|age={{birth date and age2|2026|6|11|1992|8|22}}|caps=46|goals=2|club=[[West Ham United F.C.|West Ham]]|clubnat=ENG}}
{{nat fs g player|no=6|pos=DF|name=[[Štěpán Chaloupek]]|sortname=Chaloupek, Stepan|age={{birth date and age2|2026|6|11|1998|2|9}}|caps=5|goals=0|club=[[SK Slavia Prague|Slavia Prague]]|clubnat=CZE}}
{{nat fs g player|no=7|pos=DF|name=[[Ladislav Krejčí (footballer, born 1999)|Ladislav Krejčí]]|sortname=Krejci, Ladislav|age={{birth date and age2|2026|6|11|1999|5|24}}|caps=31|goals=1|club=[[Wolverhampton Wanderers F.C.|Wolverhampton Wanderers]]|clubnat=ENG}}
{{nat fs g player|no=8|pos=MF|name=[[Vladimír Darida]]|sortname=Darida, Vladimir|age={{birth date and age2|2026|6|11|1990|8|8}}|caps=85|goals=10|club=[[FC Hradec Králové|Hradec Králové]]|clubnat=CZE}}
{{nat fs g player|no=9|pos=FW|name=[[Adam Hložek]]|sortname=Hlozek, Adam|age={{birth date and age2|2026|6|11|2002|7|25}}|caps=30|goals=5|club=[[TSG 1899 Hoffenheim|TSG Hoffenheim]]|clubnat=GER}}
{{nat fs g player|no=10|pos=FW|name=[[Patrik Schick]]|sortname=Schick, Patrik|age={{birth date and age2|2026|6|11|1996|1|24}}|caps=55|goals=26|club=[[Bayer 04 Leverkusen|Bayer Leverkusen]]|clubnat=GER}}
{{nat fs g player|no=11|pos=MF|name=[[Tomáš Souček]]|sortname=Soucek, Tomas|age={{birth date and age2|2026|6|11|1995|2|27}}|caps=65|goals=12|club=[[West Ham United F.C.|West Ham]]|clubnat=ENG}}
{{nat fs g player|no=12|pos=GK|name=[[Jiří Pavlenka]]|sortname=Pavlenka, Jiri|age={{birth date and age2|2026|6|11|1992|4|14}}|caps=32|goals=0|club=[[SV Werder Bremen|Werder Bremen]]|clubnat=GER}}
{{nat fs g player|no=13|pos=GK|name=[[Martin Jedlička]]|sortname=Jedlicka, Martin|age={{birth date and age2|2026|6|11|1990|2|1}}|caps=3|goals=0|club=[[Sparta Prague|Sparta Prague]]|clubnat=CZE}}
{{nat fs g player|no=14|pos=MF|name=[[Alex Král]]|sortname=Kral, Alex|age={{birth date and age2|2026|6|11|1998|5|19}}|caps=37|goals=3|club=[[RC Strasbourg Alsace|Strasbourg]]|clubnat=FRA}}
"""

_SAMPLE_WIKITEXT = f"""\
Intro text here.

== Group A ==

=== Scotland ===

Coach: [[Steve Clarke]]

{{{{nat fs g start}}}}
{_SCOTLAND_PLAYERS}{{{{nat fs g end}}}}

=== Czech Republic ===

Coach: [[Miroslav Koubek]]

{{{{nat fs g start}}}}
{_CZE_PLAYERS}{{{{nat fs g end}}}}

== Statistics ==

=== Age ===
Some stats here.

=== Player representation by club ===
More stats.
"""


def _make_fake_get(wikitext: str):
    """Return a fake _get callable that returns the right JSON structure."""
    def _fake_get(self, url: str) -> dict:  # noqa: ARG001
        return {"parse": {"wikitext": wikitext}}
    return _fake_get


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWikiSquadsProvider:
    def test_codes_resolved(self, monkeypatch):
        """Both Scotland (SCO) and Czech Republic (CZE) should be resolved."""
        monkeypatch.setattr(WikiSquadsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        squads = WikiSquadsProvider().fetch_squads()
        assert "SCO" in squads, "Scotland (SCO) should be in squads"
        assert "CZE" in squads, "Czech Republic (CZE) should be in squads"

    def test_formation_present(self, monkeypatch):
        """Each squad should have a non-empty formation string."""
        monkeypatch.setattr(WikiSquadsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        squads = WikiSquadsProvider().fetch_squads()
        for code, squad in squads.items():
            assert isinstance(squad[0], str) and squad[0], f"{code}: formation should be a non-empty str"

    def test_positions_mapped(self, monkeypatch):
        """Wikipedia pos codes must map to our internal strings."""
        monkeypatch.setattr(WikiSquadsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        squads = WikiSquadsProvider().fetch_squads()
        valid = {"GK", "CB", "CM", "ST"}
        for code, (_, players) in squads.items():
            for p in players:
                assert p[2] in valid, f"{code} player {p[1]}: unexpected pos {p[2]!r}"

    def test_first_player_is_gk(self, monkeypatch):
        """First player in the XI must be a GK."""
        monkeypatch.setattr(WikiSquadsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        squads = WikiSquadsProvider().fetch_squads()
        for code, (_, players) in squads.items():
            assert players[0][2] == "GK", f"{code}: first player should be GK, got {players[0][2]}"

    def test_xi_exactly_one_gk(self, monkeypatch):
        """The projected XI (first 11) must contain exactly 1 GK."""
        monkeypatch.setattr(WikiSquadsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        squads = WikiSquadsProvider().fetch_squads()
        for code, (_, players) in squads.items():
            xi = players[:11]
            gks = [p for p in xi if p[2] == "GK"]
            assert len(gks) == 1, f"{code}: XI has {len(gks)} GK(s), expected 1"

    def test_link_stripping(self, monkeypatch):
        """[[A|B]] links should return the display text B, not the full bracket form."""
        monkeypatch.setattr(WikiSquadsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        squads = WikiSquadsProvider().fetch_squads()
        # Slavia Prague clubs should show "Slavia Prague" not "SK Slavia Prague|Slavia Prague"
        cze_players = squads["CZE"][1]
        slavia_players = [p for p in cze_players if "Slavia Prague" in p[3]]
        assert slavia_players, "Expected some Slavia Prague players in CZE squad"
        for p in slavia_players:
            assert "|" not in p[3], f"Club display should not contain '|': {p[3]!r}"
            assert "[[" not in p[3], f"Club should not contain wiki brackets: {p[3]!r}"

    def test_name_pipe_stripping(self, monkeypatch):
        """[[Link text (disambiguation)|Display]] should yield just 'Display'."""
        monkeypatch.setattr(WikiSquadsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        squads = WikiSquadsProvider().fetch_squads()
        # Ladislav Krejčí has name=[[Ladislav Krejčí (footballer, born 1999)|Ladislav Krejčí]]
        cze_players = squads["CZE"][1]
        krejci = [p for p in cze_players if "Krej" in p[1]]
        assert krejci, "Ladislav Krejčí should be in CZE squad"
        assert krejci[0][1] == "Ladislav Krejčí", (
            f"Expected 'Ladislav Krejčí', got {krejci[0][1]!r}"
        )

    def test_non_team_sections_ignored(self, monkeypatch):
        """Statistics/Age sections should not be parsed as teams."""
        monkeypatch.setattr(WikiSquadsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        squads = WikiSquadsProvider().fetch_squads()
        # Only SCO and CZE should be present — no "Age" or "Statistics" entries
        assert set(squads.keys()) == {"SCO", "CZE"}

    def test_returns_empty_on_get_failure(self, monkeypatch):
        """If _get raises, fetch_squads must return {} (caller falls back to seed)."""
        def _fail(self, url: str):
            raise RuntimeError("network error")
        monkeypatch.setattr(WikiSquadsProvider, "_get", _fail)
        squads = WikiSquadsProvider().fetch_squads()
        assert squads == {}

    def test_squad_length(self, monkeypatch):
        """Each squad should have at least 11 players (we seeded 14 each)."""
        monkeypatch.setattr(WikiSquadsProvider, "_get", _make_fake_get(_SAMPLE_WIKITEXT))
        squads = WikiSquadsProvider().fetch_squads()
        for code, (_, players) in squads.items():
            assert len(players) >= 11, f"{code}: expected ≥11 players, got {len(players)}"
