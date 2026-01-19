from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/harpoon"
    polygon_rpc_url: str = "https://polygon-rpc.com"
    subgraph_url: str = "https://api.thegraph.com/subgraphs/name/polymarket/polymarket-matic"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
