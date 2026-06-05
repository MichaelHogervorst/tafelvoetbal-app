from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.database import get_leaderboard
from app.dependencies import get_current_user
from app.templates_engine import templates

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request, user: dict = Depends(get_current_user)) -> HTMLResponse:
    players = get_leaderboard()
    return templates.TemplateResponse(
        request, "index.html", {"user": user, "players": players}
    )
