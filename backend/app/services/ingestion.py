"""Ingestion + refresh pipeline.

run_refresh(db, sims):
  1. Fetch via factory providers
  2. Upsert teams (48) + players + matches + match_results + odds_snapshots
  3. Fit Dixon-Coles ratings on historical results
  4. Price all 8 fixtures (match ModelSnapshot per fixture)
  5. Price outright (one ModelSnapshot with all rows)
  6. Run tournament simulation (one TournamentSnapshot)
  7. Refresh team_news
"""
from __future__ import annotations
from datetime import datetime, timezone

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
from app.models.ratings import fit_ratings
from app.providers.factory import get_football_provider, get_news_provider, get_odds_provider
from app.seed import seed_data
from app.services.news import refresh_news
from app.services.pricing import price_match, price_outright
from app.services.tournament_service import run_tournament


def _upsert_team(db: Session, t_dict: dict, ratings=None) -> None:
    """Insert or update a Team row from seed_data TEAMS entry."""
    existing = db.get(Team, t_dict["code"])
    if existing is None:
        row = Team(
            code=t_dict["code"],
            name=seed_data.NAMES.get(t_dict["code"], t_dict["code"]),
            group=t_dict["group"],
            colors=seed_data.COLORS.get(t_dict["code"], ["#888888", "#FFFFFF"]),
            elo=1500.0,
            attack=0.0,
            defense=0.0,
            str_rating=float(t_dict.get("str", 55)),
            form=t_dict.get("form", ""),
        )
        db.add(row)
    else:
        existing.name = seed_data.NAMES.get(t_dict["code"], t_dict["code"])
        existing.group = t_dict["group"]
        existing.colors = seed_data.COLORS.get(t_dict["code"], ["#888888", "#FFFFFF"])
        existing.str_rating = float(t_dict.get("str", 55))
        existing.form = t_dict.get("form", "")

    # If ratings are provided, update attack/defense/str_rating
    if ratings and t_dict["code"] in ratings.teams:
        tr = ratings.teams[t_dict["code"]]
        row_ref = db.get(Team, t_dict["code"]) or existing
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


def _persist_odds(db: Session, lines) -> dict[str, dict]:
    """Persist OddsSnapshot rows and return grouped by market_key."""
    now = datetime.now(timezone.utc)
    grouped: dict[str, dict] = {}
    for line in lines:
        db.add(OddsSnapshot(
            market_key=line.market_key,
            book=line.book,
            selection=line.selection,
            dec=line.dec,
            captured_at=line.captured_at,
        ))
        grouped.setdefault(line.market_key, {})[line.selection] = line.dec
    return grouped


def run_refresh(db: Session, sims: int = 50000) -> None:
    """Full refresh pipeline: fetch → upsert → fit → price → simulate → persist snapshots."""
    now = datetime.now(timezone.utc)

    # --- 1. Fetch from providers ---
    fp = get_football_provider()
    op = get_odds_provider()
    np_ = get_news_provider()

    fixtures = fp.fetch_fixtures()
    results = fp.fetch_results()
    squads = fp.fetch_squads()
    odds_lines = op.fetch_odds()
    news_items = np_.fetch_news()

    # --- 2. Upsert teams (basic info first, ratings updated after fitting) ---
    for t in seed_data.TEAMS:
        _upsert_team(db, t)
    db.flush()

    # --- 3. Upsert players ---
    _upsert_players(db, squads)
    db.flush()

    # --- 4. Upsert matches ---
    _upsert_matches(db, fixtures)
    db.flush()

    # --- 5. Persist match results ---
    raw_results = _persist_results(db, results)
    db.flush()

    # --- 6. Persist odds snapshots + build grouped lookup ---
    odds_grouped = _persist_odds(db, odds_lines)
    db.flush()

    # --- 7. Fit ratings on historical results ---
    codes = [t["code"] for t in seed_data.TEAMS]
    ratings = fit_ratings(raw_results, codes)

    # --- 8. Update team ratings in DB ---
    for t in seed_data.TEAMS:
        code = t["code"]
        if code in ratings.teams:
            tr = ratings.teams[code]
            row = db.get(Team, code)
            if row:
                row.attack = tr.attack
                row.defense = tr.defense
                row.elo = tr.elo
                row.str_rating = tr.str_rating
    db.flush()

    # --- 9. Price each match fixture ---
    for fixture in fixtures:
        market_key = f"h2h:{fixture.id}"
        match_odds = odds_grouped.get(market_key, {})
        # Fall back to even odds if no market data
        market_odds_input = {
            "home": match_odds.get("home", 2.5),
            "draw": match_odds.get("draw", 3.2),
            "away": match_odds.get("away", 2.9),
        }
        # Only price if both teams are in ratings
        if fixture.home not in ratings.teams or fixture.away not in ratings.teams:
            continue
        snap_payload = price_match(
            fixture.id,
            fixture.home,
            fixture.away,
            ratings,
            market_odds=market_odds_input,
        )
        db.add(ModelSnapshot(
            kind="match",
            ref=fixture.id,
            payload=snap_payload,
            created_at=now,
        ))

    # --- 10. Price outright ---
    outright_odds = odds_grouped.get("outright", {})
    if not outright_odds:
        # Fall back: build from seed_data
        outright_odds = {t["code"]: t["dec"] for t in seed_data.TEAMS}

    # Only price teams that are in ratings
    valid_outright = {c: d for c, d in outright_odds.items() if c in ratings.teams}
    outright_rows = price_outright(ratings, valid_outright)
    db.add(ModelSnapshot(
        kind="outright",
        ref="all",
        payload={"rows": outright_rows},
        created_at=now,
    ))

    # --- 11. Run tournament simulation ---
    group_of = {t["code"]: t["group"] for t in seed_data.TEAMS}
    sim_result = run_tournament(ratings, group_of, sims=sims)
    db.add(TournamentSnapshot(
        payload={
            "team_probs": sim_result.team_probs,
            "group_winner": sim_result.group_winner,
            "champion": sim_result.champion,
        },
        created_at=now,
    ))

    # --- 12. Refresh team news ---
    # Clear old seed news before re-inserting
    db.query(TeamNews).filter(TeamNews.source == "seed").delete()
    db.flush()
    refresh_news(db, news_items)

    db.commit()
