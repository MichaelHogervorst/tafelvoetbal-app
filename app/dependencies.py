"""Auth dependencies: guards that protect routes."""

from fastapi import Request
from fastapi.responses import RedirectResponse

from app.config import settings

# Fake user injected during local development when AUTH_ENABLED=false.
DEV_USER = {
    "name": "Dev User",
    "email": "dev@localhost",
    "oid": "local-dev",
}


class RedirectToLogin(Exception):
    """Raised when an anonymous user hits a protected route."""


def get_current_user(request: Request) -> dict:
    """Return the signed-in user.

    - If auth is disabled (local dev), returns a fake dev user.
    - Otherwise reads the user from the session, or raises RedirectToLogin.
    """
    if not settings.auth_enabled:
        return DEV_USER

    user = request.session.get("user")
    if not user:
        raise RedirectToLogin()
    return user
