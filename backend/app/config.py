from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://wc:wc@localhost:5432/wcbet"
    odds_api_key: str = ""
    api_football_key: str = ""
    odds_api_base: str = "https://api.the-odds-api.com/v4"
    api_football_base: str = "https://v3.football.api-sports.io"
    model_sims: int = 50000
    model_decay_halflife_days: int = 300
    wiki_squads_enabled: bool = True
    wiki_results_enabled: bool = True

    @property
    def has_odds_key(self) -> bool:
        return bool(self.odds_api_key.strip())

    @property
    def has_football_key(self) -> bool:
        return bool(self.api_football_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
