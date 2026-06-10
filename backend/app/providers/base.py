"""Provider protocols + transport DTOs (provider-agnostic)."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class OddsLine:
    market_key: str       # e.g. "h2h:m1"
    book: str
    selection: str        # "home"|"draw"|"away"|team code|"Over 2.5"...
    dec: float
    captured_at: datetime
    commence_time: datetime | None = None


@dataclass
class FixtureDTO:
    id: str
    home: str
    away: str
    group: str
    stage: str
    kickoff: datetime | None
    venue: str


@dataclass
class ResultDTO:
    home: str
    away: str
    home_goals: int
    away_goals: int
    days_ago: float
    competition: str = ""


@dataclass
class NewsItem:
    code: str
    tag: str       # injury|susp|lineup|form|intel
    text: str
    source: str
    url: str
    published_at: datetime


class OddsProvider(Protocol):
    def fetch_odds(self) -> list[OddsLine]: ...

class FootballProvider(Protocol):
    def fetch_fixtures(self) -> list[FixtureDTO]: ...
    def fetch_results(self) -> list[ResultDTO]: ...
    def fetch_squads(self) -> dict[str, list]: ...

class NewsProvider(Protocol):
    def fetch_news(self) -> list[NewsItem]: ...
