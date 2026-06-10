"""App-wide configuration.

Values are loaded from environment variables first; a .env file is used as a
fallback for local development. In production no .env file is present — all
configuration must be supplied as environment variables by the host (Azure
Container Apps / Terraform).
"""

from pydantic import model_validator
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

    # SQLite database path — override to point at a mounted volume in production
    db_path: str = "data/tafelvoetbal.db"

    @model_validator(mode="after")
    def _check_secrets(self) -> "Settings":
        """Reject insecure defaults when running in production mode."""
        if not self.debug and self.session_secret == "change-me":
            raise ValueError(
                "SESSION_SECRET must be set to a secure value when DEBUG=false."
            )
        return self

    @property
    def authority(self) -> str:
        """Entra ID authority URL for this tenant."""
        return f"https://login.microsoftonline.com/{self.tenant_id}"

    @property
    def scopes(self) -> list[str]:
        """OIDC scopes requested at login (sign-in + basic profile)."""
        return ["User.Read"]


settings = Settings()
