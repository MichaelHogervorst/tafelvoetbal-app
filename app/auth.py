"""MSAL confidential client helpers for the Entra ID Authorization Code Flow."""

import msal

from app.config import settings


def build_msal_app(cache: msal.SerializableTokenCache | None = None) -> msal.ConfidentialClientApplication:
    """Create an MSAL confidential client application."""
    return msal.ConfidentialClientApplication(
        client_id=settings.client_id,
        client_credential=settings.client_secret,
        authority=settings.authority,
        token_cache=cache,
    )


def build_auth_code_flow() -> dict:
    """Start an auth code flow and return the flow dict (to be stored in session)."""
    return build_msal_app().initiate_auth_code_flow(
        scopes=settings.scopes,
        redirect_uri=settings.redirect_uri,
    )
