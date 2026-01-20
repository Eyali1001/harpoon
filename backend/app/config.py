from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/harpoon"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Convert postgresql:// to postgresql+asyncpg:// for async SQLAlchemy
        if self.database_url.startswith("postgresql://"):
            object.__setattr__(self, 'database_url', self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1))
        elif self.database_url.startswith("postgres://"):
            object.__setattr__(self, 'database_url', self.database_url.replace("postgres://", "postgresql+asyncpg://", 1))

    # Goldsky-hosted subgraphs
    orders_subgraph_url: str = "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/prod/gn"
    activity_subgraph_url: str = "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/activity-subgraph/0.0.4/gn"

    # Gamma API for market metadata
    gamma_api_url: str = "https://gamma-api.polymarket.com"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
