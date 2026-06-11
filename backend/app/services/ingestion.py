"""Ingestion + refresh pipeline.

run_refresh(db, sims):
  1. Fetch via factory providers
  2. Derive universe (real mode if 12×4 groups from h2h odds, else seed mode)
  3. Upsert teams (48) + players + matches + match_results + odds_snapshots
  4. Fit Dixon-Coles ratings on historical results
  5. Compute blended market-anchored str_rating per team
  6. Overwrite ratings.teams[c].str_rating + Team.str_rating with blended values
  7. Run tournament simulation (now with anchored strengths)
  8. Price all fixtures (match ModelSnapshot per fixture) using str_by_code
  9. Price outright from sim champion probs
 10. Run tournament simulation (one TournamentSnapshot)
 11. Refresh team_news
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from statistics import mean

from sqlalchemy.orm import Session

from app.db.models import (
    Match,
    MatchResult,
    ModelSnapshot,
    OddsSnapshot,
    Player,
    Team,
    TeamNews,
    TournamentSnapshot,
)
from app.models.ratings import RatingsModel, TeamRatings, fit_ratings
from app.config import get_settings
from app.providers.factory import get_football_provider, get_news_provider, get_odds_provider
from app.providers.wiki_results import WikiResultsProvider
from app.providers.wiki_squads import WikiSquadsProvider
from app.seed import seed_data
from app.services.market_anchor import blended_strength
from app.services.news import refresh_news
from app.services.pricing import price_match, price_outright
from app.services.team_universe import derive_universe
from app.services.tournament_service import run_tournament

logger = logging.getLogger(__name__)

# Neutral TeamRatings for teams with no historical data
_NEUTRAL_RATINGS = TeamRatings(attack=0.0, defense=0.0, elo=1500.0, str_rating=55.0)


# ---------------------------------------------------------------------------
# Internal upsert helpers
# ---------------------------------------------------------------------------

def _upsert_team(db: Session, code: str, name: str, group: str,
                 colors: list, str_rating: float, ratings=None) -> None:
    """Insert or update a Team row."""
    existing = db.get(Team, code)
    if existing is None:
        row = Team(
            code=code,
            name=name,
            group=group,
            colors=colors,
            elo=1500.0,
            attack=0.0,
            defense=0.0,
            str_rating=str_rating,
            form="",
        )
        db.add(row)
    else:
        existing.name = name
        existing.group = group
        existing.colors = colors
        existing.str_rating = str_rating

    # If ratings are available for this team, apply them
    if ratings and code in ratings.teams:
        tr = ratings.teams[code]
        row_ref = db.get(Team, code) or existing
        if row_ref:
            row_ref.attack = tr.attack
            row_ref.defense = tr.defense
            row_ref.elo = tr.elo
            row_ref.str_rating = tr.str_rating


def _upsert_players(db: Session, squads: dict[str, list]) -> None:
    """Insert players from squads dict. Clears existing players for each team first."""
    for code, squad_data in squads.items():
        # squad_data = [formation, [[no, name, pos, club, tier?], ...]]
        if not isinstance(squad_data, (list, tuple)) or len(squad_data) < 2:
            continue
        players_list = squad_data[1]
        # Delete existing players for this team to allow re-seeding
        db.query(Player).filter_by(code=code).delete()
        for idx, entry in enumerate(players_list):
            if not entry:
                continue
            no = entry[0] if len(entry) > 0 else 0
            name = entry[1] if len(entry) > 1 else ""
            pos = entry[2] if len(entry) > 2 else "MID"
            club = entry[3] if len(entry) > 3 else ""
            tier = float(entry[4]) if len(entry) > 4 else 1.0
            starter = idx < 11  # first 11 = projected starters
            db.add(Player(
                code=code,
                number=int(no),
                name=str(name),
                pos=str(pos),
                club=str(club),
                tier=tier,
                starter=starter,
                rates={},
            ))


def _upsert_matches(db: Session, fixtures) -> None:
    """Insert or update Match rows from FixtureDTO list."""
    for f in fixtures:
        existing = db.get(Match, f.id)
        if existing is None:
            db.add(Match(
                id=f.id,
                home=f.home,
                away=f.away,
                group=f.group,
                stage=f.stage,
                kickoff=f.kickoff,
                venue=f.venue,
            ))
        else:
            existing.home = f.home
            existing.away = f.away
            existing.group = f.group
            existing.stage = f.stage
            existing.kickoff = f.kickoff
            existing.venue = f.venue


def _persist_results(db: Session, results) -> list[dict]:
    """Persist MatchResult rows and return as dicts for ratings fitting."""
    now = datetime.now(timezone.utc)
    raw_rows = []
    for r in results:
        db.add(MatchResult(
            date=now,
            home=r.home,
            away=r.away,
            home_goals=r.home_goals,
            away_goals=r.away_goals,
            competition=r.competition,
            weight=1.0,
        ))
        raw_rows.append({
            "home": r.home,
            "away": r.away,
            "home_goals": r.home_goals,
            "away_goals": r.away_goals,
            "days_ago": r.days_ago,
        })
    return raw_rows


def _persist_odds(db: Session, lines) -> tuple[dict[str, dict], dict[str, "datetime | None"]]:
    """Persist OddsSnapshot rows and return (grouped, kickoff_by_market).

    grouped: for h2h markets maps selection → avg_dec across books;
             for outright markets maps team_code → avg_dec across books.
    kickoff_by_market: maps market_key → first non-None commence_time seen.
    """
    from datetime import datetime as _datetime
    # First, group all decimals per (market_key, selection) across books
    accumulator: dict[str, dict[str, list[float]]] = {}
    kickoff_by_market: dict[str, "_datetime | None"] = {}
    for line in lines:
        db.add(OddsSnapshot(
            market_key=line.market_key,
            book=line.book,
            selection=line.selection,
            dec=line.dec,
            captured_at=line.captured_at,
        ))
        accumulator.setdefault(line.market_key, {}).setdefault(line.selection, []).append(line.dec)
        # Capture first non-None commence_time per market_key
        ct = getattr(line, "commence_time", None)
        if ct is not None and kickoff_by_market.get(line.market_key) is None:
            kickoff_by_market[line.market_key] = ct

    # Average across books
    grouped: dict[str, dict] = {}
    for mkey, sel_lists in accumulator.items():
        grouped[mkey] = {sel: mean(decs) for sel, decs in sel_lists.items()}

    return grouped, kickoff_by_market


def _ensure_all_in_ratings(ratings: RatingsModel, codes: list[str]) -> RatingsModel:
    """Ensure every code in `codes` is present in ratings.teams.

    Teams absent from historical data get neutral TeamRatings (attack=0,
    defense=0, elo=1500, str_rating=55). This prevents KeyErrors during
    pricing when real mode has teams with zero calibration matches.
    """
    for code in codes:
        if code not in ratings.teams:
            logger.info(
                "ingestion: team %s has no historical results — assigning neutral ratings",
                code,
            )
            ratings.teams[code] = TeamRatings(
                attack=0.0, defense=0.0, elo=1500.0, str_rating=55.0
            )
    return ratings


# ---------------------------------------------------------------------------
# Squad resolver (Wikipedia > seed fallback)
# ---------------------------------------------------------------------------

def _resolve_squads() -> dict[str, list]:
    """Return a merged squads dict.

    If ``wiki_squads_enabled`` is True, attempts to fetch live squads from
    Wikipedia.  Any teams Wikipedia returns override the corresponding seed
    entry; teams Wikipedia missed keep their seed squad.  Falls back to seed
    entirely on failure or if the provider returns an empty dict.
    """
    base: dict[str, list] = dict(seed_data.SQUADS)  # seed as base

    if not get_settings().wiki_squads_enabled:
        return base

    try:
        wiki = WikiSquadsProvider().fetch_squads()
    except Exception as exc:
        logger.warning("_resolve_squads: WikiSquadsProvider raised %s — using seed", exc)
        return base

    if not wiki:
        logger.info("_resolve_squads: Wikipedia returned empty dict — using seed")
        return base

    # Merge: wiki overrides seed per team
    merged = {**base, **wiki}
    logger.info(
        "_resolve_squads: merged %d wiki teams over %d seed teams → %d total",
        len(wiki),
        len(base),
        len(merged),
    )
    return merged


# ---------------------------------------------------------------------------
# Main refresh entrypoint
# ---------------------------------------------------------------------------

def run_refresh(db: Session, sims: int = 50000) -> None:
    """Full refresh pipeline: fetch → upsert → fit → anchor → price → simulate → persist."""
    now = datetime.now(timezone.utc)

    # --- 1. Fetch from providers ---
    fp = get_football_provider()
    op = get_odds_provider()
    np_ = get_news_provider()

    fixtures = fp.fetch_fixtures()
    results = list(fp.fetch_results())
    squads = _resolve_squads()

    # Augment calibration results with recent WC2026 qualification matches
    # (Wikipedia, free, no API key needed).  Gate on setting so hermetic tests
    # never touch the network (WIKI_RESULTS_ENABLED=0 in conftest).
    if get_settings().wiki_results_enabled:
        try:
            wiki_results = WikiResultsProvider().fetch_results()
            results = results + wiki_results
            logger.info(
                "ingestion: merged %d wiki qualification results (%d total)",
                len(wiki_results),
                len(results),
            )
        except Exception as exc:
            logger.warning(
                "ingestion: WikiResultsProvider failed — continuing without: %s", exc
            )
    odds_lines = op.fetch_odds()
    news_items = np_.fetch_news()

    # Fetch outright lines if the provider supports it
    fetch_outrights_fn = getattr(op, "fetch_outrights", None)
    outright_lines = fetch_outrights_fn() if callable(fetch_outrights_fn) else []

    # Combine all lines for persistence
    all_lines = odds_lines + outright_lines

    # --- 2. Determine real vs seed mode ---
    universe = derive_universe(odds_lines)
    real_mode = universe is not None

    if real_mode:
        logger.info("ingestion: REAL mode — %d teams from live odds", len(universe["teams"]))
        universe_teams = universe["teams"]
        group_of = universe["group_of"]
        universe_codes = [t["code"] for t in universe_teams]
    else:
        logger.info("ingestion: SEED mode — using seed_data.TEAMS")
        universe_teams = None
        group_of = {t["code"]: t["group"] for t in seed_data.TEAMS}
        universe_codes = [t["code"] for t in seed_data.TEAMS]

    # --- 3. Upsert teams ---
    if real_mode:
        for t in universe_teams:
            _upsert_team(
                db,
                code=t["code"],
                name=t["name"],
                group=t["group"],
                colors=t["colors"],
                str_rating=t["str0"],
            )
    else:
        for t in seed_data.TEAMS:
            _upsert_team(
                db,
                code=t["code"],
                name=seed_data.NAMES.get(t["code"], t["code"]),
                group=t["group"],
                colors=seed_data.COLORS.get(t["code"], ["#888888", "#FFFFFF"]),
                str_rating=float(t.get("str", 55)),
            )
    db.flush()

    # --- 4. Upsert players (seed squads in both modes for now) ---
    _upsert_players(db, squads)
    db.flush()

    # --- 5. Upsert matches ---
    _upsert_matches(db, fixtures)
    db.flush()

    # --- 6. Persist match results ---
    raw_results = _persist_results(db, results)
    db.flush()

    # --- 7. Persist odds snapshots + build grouped lookup ---
    odds_grouped, kickoff_by_market = _persist_odds(db, all_lines)
    db.flush()

    # --- 8. Fit ratings on historical results ---
    ratings = fit_ratings(raw_results, universe_codes)

    # Ensure teams with no history get neutral ratings (no crash in real mode)
    ratings = _ensure_all_in_ratings(ratings, universe_codes)

    # --- 9. Build outright dec_by_code (needed for market anchor) ---
    outright_odds_grouped = odds_grouped.get("outright", {})
    if real_mode:
        seed_dec_by_code = {t["code"]: t["dec"] for t in seed_data.TEAMS}
        dec_by_code: dict[str, float] = {}
        for code in universe_codes:
            if code in outright_odds_grouped:
                dec_by_code[code] = outright_odds_grouped[code]
            elif code in seed_dec_by_code:
                dec_by_code[code] = seed_dec_by_code[code]
            else:
                dec_by_code[code] = 201.0  # generic long shot fallback
    else:
        # Seed mode: use seed outright odds if no real data
        if outright_odds_grouped:
            dec_by_code = {c: d for c, d in outright_odds_grouped.items()
                          if c in ratings.teams}
        else:
            dec_by_code = {t["code"]: t["dec"] for t in seed_data.TEAMS}

    valid_dec = {c: d for c, d in dec_by_code.items() if c in ratings.teams}

    # --- 10. Compute blended market-anchored strengths ---
    # model_net: Dixon-Coles overall strength = attack + defense (higher defense
    # = better defence here, so strength is the sum, not the difference).
    model_net = {
        c: ratings.teams[c].attack + ratings.teams[c].defense
        for c in universe_codes
        if c in ratings.teams
    }

    # n_matches: count how many raw_results rows involve each code
    n_matches: dict[str, int] = {c: 0 for c in universe_codes}
    for row in raw_results:
        if row["home"] in n_matches:
            n_matches[row["home"]] += 1
        if row["away"] in n_matches:
            n_matches[row["away"]] += 1

    # Use valid_dec as market anchor; for codes not in valid_dec, use a neutral long-shot
    market_dec_for_blend: dict[str, float] = {}
    for c in universe_codes:
        if c in valid_dec:
            market_dec_for_blend[c] = valid_dec[c]
        elif c in dec_by_code:
            market_dec_for_blend[c] = dec_by_code[c]
        else:
            market_dec_for_blend[c] = 201.0

    str_by_code = blended_strength(model_net, market_dec_for_blend, n_matches, universe_codes)

    # --- 11. Overwrite ratings.teams[c].str_rating with blended strength ---
    for c in universe_codes:
        if c in ratings.teams:
            ratings.teams[c].str_rating = str_by_code[c]

    # --- 12. Update team ratings in DB (str_rating now anchored) ---
    for code in universe_codes:
        if code in ratings.teams:
            tr = ratings.teams[code]
            row = db.get(Team, code)
            if row:
                row.attack = tr.attack
                row.defense = tr.defense
                row.elo = tr.elo
                row.str_rating = str_by_code.get(code, tr.str_rating)
    db.flush()

    # --- 13. Run tournament simulation with anchored strengths ---
    sim_result = run_tournament(ratings, group_of, sims=sims)

    # --- 14. Price each match fixture using anchored str_by_code ---
    if real_mode:
        # In real mode: iterate h2h market keys present in odds_grouped
        h2h_keys = [k for k in odds_grouped if k.startswith("h2h:")]
        for mkey in h2h_keys:
            # market_key format: "h2h:{HOME}_{AWAY}"
            body = mkey[4:]
            parts = body.split("_", 1)
            if len(parts) != 2:
                continue
            home_code, away_code = parts
            if home_code not in str_by_code or away_code not in str_by_code:
                continue
            match_odds_raw = odds_grouped.get(mkey, {})
            market_odds_input = {
                "home": match_odds_raw.get("home", 2.5),
                "draw": match_odds_raw.get("draw", 3.2),
                "away": match_odds_raw.get("away", 2.9),
            }
            match_id = body  # "{HOME}_{AWAY}"
            # Determine stage: group if both teams are in the same group
            match_stage = (
                "group"
                if group_of.get(home_code) == group_of.get(away_code)
                   and group_of.get(home_code) is not None
                else "knockout"
            )
            snap_payload = price_match(
                match_id,
                home_code,
                away_code,
                ratings,
                market_odds=market_odds_input,
                str_by_code=str_by_code,
                stage=match_stage,
            )
            # Attach kickoff from commence_time if available
            ko = kickoff_by_market.get(mkey)
            snap_payload["kickoff"] = ko.isoformat() if ko else None
            db.add(ModelSnapshot(
                kind="match",
                ref=match_id,
                payload=snap_payload,
                created_at=now,
            ))
    else:
        # Seed mode: use seed fixture IDs (m1..m8)
        for fixture in fixtures:
            market_key = f"h2h:{fixture.id}"
            match_odds = odds_grouped.get(market_key, {})
            market_odds_input = {
                "home": match_odds.get("home", 2.5),
                "draw": match_odds.get("draw", 3.2),
                "away": match_odds.get("away", 2.9),
            }
            if fixture.home not in str_by_code or fixture.away not in str_by_code:
                continue
            # Determine stage: group if both teams are in the same group
            match_stage = (
                "group"
                if group_of.get(fixture.home) == group_of.get(fixture.away)
                   and group_of.get(fixture.home) is not None
                else "knockout"
            )
            snap_payload = price_match(
                fixture.id,
                fixture.home,
                fixture.away,
                ratings,
                market_odds=market_odds_input,
                str_by_code=str_by_code,
                stage=match_stage,
            )
            # Seed mode has no real commence_time; kickoff is None
            snap_payload["kickoff"] = None
            db.add(ModelSnapshot(
                kind="match",
                ref=fixture.id,
                payload=snap_payload,
                created_at=now,
            ))

    # --- 15. Price outright from sim champion probs ---
    valid_outright = {c: d for c, d in valid_dec.items() if c in ratings.teams}
    outright_rows = price_outright(sim_result.champion, valid_outright, str_by_code)
    db.add(ModelSnapshot(
        kind="outright",
        ref="all",
        payload={"rows": outright_rows},
        created_at=now,
    ))

    # --- 16. Persist tournament snapshot ---
    db.add(TournamentSnapshot(
        payload={
            "team_probs": sim_result.team_probs,
            "group_winner": sim_result.group_winner,
            "champion": sim_result.champion,
        },
        created_at=now,
    ))

    # --- 17. Refresh team news ---
    db.query(TeamNews).filter(TeamNews.source == "seed").delete()
    db.flush()
    refresh_news(db, news_items)

    db.commit()
