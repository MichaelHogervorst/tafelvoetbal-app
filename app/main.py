from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, health, pages

app = FastAPI(title="Tafelvoetbal")

# Signed session cookie. Long-lived (~14 days) so users stay logged in.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    max_age=14 * 24 * 60 * 60,  # 14 days, in seconds
    same_site="lax",
    https_only=not settings.debug,  # only require HTTPS in production
)

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(health.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
