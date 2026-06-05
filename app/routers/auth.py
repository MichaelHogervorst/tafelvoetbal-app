"""Authentication routes: login, callback, logout (Entra ID via MSAL)."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.auth import build_auth_code_flow, build_msal_app
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login(request: Request) -> RedirectResponse:
    """Start the sign-in flow by redirecting the user to Microsoft."""
    flow = build_auth_code_flow()
    # The flow contains state + PKCE values we must remember for the callback.
    request.session["auth_flow"] = flow
    return RedirectResponse(flow["auth_uri"])


@router.get("/callback")
def callback(request: Request) -> RedirectResponse:
    """Handle the redirect back from Microsoft and complete sign-in."""
    flow = request.session.get("auth_flow")
    if not flow:
        # No flow in session (e.g. user navigated here directly) — restart login.
        return RedirectResponse(request.url_for("login"))

    result = build_msal_app().acquire_token_by_auth_code_flow(
        flow, dict(request.query_params)
    )

    if "error" in result:
        request.session.pop("auth_flow", None)
        return RedirectResponse(request.url_for("login"))

    claims = result.get("id_token_claims", {})
    request.session.pop("auth_flow", None)
    request.session["user"] = {
        "name": claims.get("name"),
        "email": claims.get("preferred_username"),
        "oid": claims.get("oid"),
    }
    return RedirectResponse(request.url_for("home"))


@router.get("/logout")
def logout(request: Request) -> RedirectResponse:
    """Clear the local session and sign out of Entra ID."""
    request.session.clear()
    home_url = str(request.url_for("home"))
    logout_url = (
        f"{settings.authority}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={home_url}"
    )
    return RedirectResponse(logout_url)
