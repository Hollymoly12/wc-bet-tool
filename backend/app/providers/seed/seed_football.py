"""Seed football provider — builds DTOs from seed_data (no API key needed)."""
from __future__ import annotations
from app.providers.base import FixtureDTO, ResultDTO
from app.seed import seed_data


class SeedFootballProvider:
    def fetch_fixtures(self) -> list[FixtureDTO]:
        out = []
        for m in seed_data.MATCHES:
            out.append(FixtureDTO(
                id=m["id"],
                home=m["home"],
                away=m["away"],
                group=m["group"],
                stage="group",
                kickoff=None,
                venue=m["venue"],
            ))
        return out

    def fetch_results(self) -> list[ResultDTO]:
        return [
            ResultDTO(
                home=h["home"],
                away=h["away"],
                home_goals=h["home_goals"],
                away_goals=h["away_goals"],
                days_ago=h["days_ago"],
            )
            for h in seed_data.synth_history()
        ]

    def fetch_squads(self) -> dict[str, list]:
        return seed_data.SQUADS
