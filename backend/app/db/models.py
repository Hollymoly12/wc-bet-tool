from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"
    code: Mapped[str] = mapped_column(String(4), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    group: Mapped[str] = mapped_column(String(2))
    colors: Mapped[list] = mapped_column(JSON, default=list)
    elo: Mapped[float] = mapped_column(Float, default=1500.0)
    attack: Mapped[float] = mapped_column(Float, default=0.0)
    defense: Mapped[float] = mapped_column(Float, default=0.0)
    str_rating: Mapped[float] = mapped_column(Float, default=55.0)
    form: Mapped[str] = mapped_column(String(8), default="")


class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(4), index=True)
    number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(64))
    pos: Mapped[str] = mapped_column(String(4))
    club: Mapped[str] = mapped_column(String(48), default="")
    tier: Mapped[float] = mapped_column(Float, default=1.0)
    starter: Mapped[bool] = mapped_column(default=False)
    rates: Mapped[dict] = mapped_column(JSON, default=dict)


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    home: Mapped[str] = mapped_column(String(4))
    away: Mapped[str] = mapped_column(String(4))
    group: Mapped[str] = mapped_column(String(2), default="")
    stage: Mapped[str] = mapped_column(String(24), default="group")
    kickoff: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    venue: Mapped[str] = mapped_column(String(96), default="")


class MatchResult(Base):
    __tablename__ = "match_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    home: Mapped[str] = mapped_column(String(4))
    away: Mapped[str] = mapped_column(String(4))
    home_goals: Mapped[int] = mapped_column(Integer)
    away_goals: Mapped[int] = mapped_column(Integer)
    competition: Mapped[str] = mapped_column(String(48), default="")
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_key: Mapped[str] = mapped_column(String(64), index=True)
    book: Mapped[str] = mapped_column(String(48))
    selection: Mapped[str] = mapped_column(String(64))
    dec: Mapped[float] = mapped_column(Float)
    captured_at: Mapped[datetime] = mapped_column(DateTime)


class ModelSnapshot(Base):
    __tablename__ = "model_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(24), index=True)  # outright|match|group|player
    ref: Mapped[str] = mapped_column(String(48), index=True)   # team code or match id
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class TournamentSnapshot(Base):
    __tablename__ = "tournament_snapshot"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class TeamNews(Base):
    __tablename__ = "team_news"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(4), index=True)
    tag: Mapped[str] = mapped_column(String(12))
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(48), default="")
    url: Mapped[str] = mapped_column(String(256), default="")
    published_at: Mapped[datetime] = mapped_column(DateTime)


class Bet(Base):
    __tablename__ = "bets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(96))
    pick: Mapped[str] = mapped_column(String(128))
    team: Mapped[str] = mapped_column(String(4), default="")
    market: Mapped[str] = mapped_column(String(48), default="")
    stake: Mapped[float] = mapped_column(Float)
    dec: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(8), default="open")  # open|won|lost|void
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    placed_at: Mapped[datetime] = mapped_column(DateTime)


class BankrollTxn(Base):
    __tablename__ = "bankroll_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(16))  # deposit|bet|settle
    amount: Mapped[float] = mapped_column(Float)
    bet_id: Mapped[int | None] = mapped_column(ForeignKey("bets.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class ProviderCall(Base):
    __tablename__ = "provider_calls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32))
    endpoint: Mapped[str] = mapped_column(String(96))
    called_at: Mapped[datetime] = mapped_column(DateTime)
