"""App-wide configuration loaded from .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Entra ID (Azure AD)
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8000/auth/callback"

    # Session middleware
    session_secret: str = "change-me"

    # Set to false to skip auth during local development
    auth_enabled: bool = False


settings = Settings()
