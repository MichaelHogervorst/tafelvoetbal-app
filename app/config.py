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

    # Local development flag (relaxes cookie https_only requirement)
    debug: bool = True

    @property
    def authority(self) -> str:
        """Entra ID authority URL for this tenant."""
        return f"https://login.microsoftonline.com/{self.tenant_id}"

    @property
    def scopes(self) -> list[str]:
        """OIDC scopes requested at login (sign-in + basic profile)."""
        return ["User.Read"]


settings = Settings()
