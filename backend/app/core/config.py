# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "BuildFlow"
    app_env: str = "development"
    debug: bool = False
    secret_key: str

    # Database
    database_url: str ="postgresql+asyncpg://postgres:postgres@localhost:5432/buildflow"

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # AI Provider
    ai_provider: str = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    ai_model: str = "gpt-4o"
    ai_max_tokens: int = 4096
    ai_temperature: float = 0.7

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    Import this function and call it — do not instantiate Settings directly.
    """
    return Settings()


settings = get_settings()