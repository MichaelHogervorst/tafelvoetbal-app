from fastapi import FastAPI

from app.database import init_db
from app.routers import health, pages

app = FastAPI(title="Tafelvoetbal")

app.include_router(pages.router)
app.include_router(health.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
