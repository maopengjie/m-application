from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vben Data Engine (Python)"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5777",
            "http://127.0.0.1:5777",
        ]
    )
    access_token_secret: str = "access_token_secret"
    refresh_token_secret: str = "refresh_token_secret"
    access_token_expire_seconds: int = 7 * 24 * 60 * 60
    refresh_token_expire_seconds: int = 30 * 24 * 60 * 60
    refresh_cookie_key: str = "jwt"
    
    # Data Layer
    mysql_dsn: str = "sqlite:///./data_engine.db"
    redis_url: str = "redis://127.0.0.1:6379/0"
    elasticsearch_url: str = "http://localhost:9200"
    enable_elasticsearch: bool = False
    debug: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DATA_ENGINE_")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
