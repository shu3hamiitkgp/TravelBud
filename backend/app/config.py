from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://travelbud:travelbud@localhost:5432/travelbud"

    jwt_secret: str = "dev-secret-do-not-use-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    cookie_secure: bool = False  # set True behind HTTPS

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    google_maps_api_key: str = ""

    pricing_provider: str = "mock"  # "mock" | "amadeus"
    amadeus_client_id: str = ""
    amadeus_client_secret: str = ""

    storage_backend: str = "local"  # "local" | "s3"
    local_storage_dir: str = "data/itineraries"
    s3_bucket: str = ""
    aws_region: str = "us-east-1"

    seed_admin_email: str = "admin@travelbud.dev"
    seed_admin_password: str = "admin12345"

    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
