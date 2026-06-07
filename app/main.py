from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import init_db, migrate_db
from app.dependencies import RedirectToLogin
from app.routers import auth, games, health, pages

app = FastAPI(
    title="Tafelvoetbal",
    # Disable API docs in production (when auth is enabled).
    # Locally (AUTH_ENABLED=false) docs remain available at /docs.
    docs_url="/docs" if not settings.auth_enabled else None,
    redoc_url="/redoc" if not settings.auth_enabled else None,
)

# Signed session cookie. Long-lived (~14 days) so users stay logged in.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    max_age=14 * 24 * 60 * 60,  # 14 days, in seconds
    same_site="lax",
    https_only=not settings.debug,  # only require HTTPS in production
)

app.include_router(pages.router)
app.include_router(games.router)
app.include_router(auth.router)
app.include_router(health.router)


@app.exception_handler(RedirectToLogin)
def redirect_to_login(request: Request, exc: RedirectToLogin) -> RedirectResponse:
    """Send anonymous users to the login page when a guarded route is hit."""
    return RedirectResponse(request.url_for("login"))


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    migrate_db()
