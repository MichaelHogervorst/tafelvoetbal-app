from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.database import get_game_history, get_leaderboard, get_player_detail
from app.dependencies import get_current_user
from app.templates_engine import templates

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request, user: dict = Depends(get_current_user)) -> HTMLResponse:
    players = get_leaderboard()
    return templates.TemplateResponse(
        request, "index.html", {"user": user, "players": players}
    )


@router.get("/games", response_class=HTMLResponse)
def game_history(request: Request, user: dict = Depends(get_current_user)) -> HTMLResponse:
    games = get_game_history()
    return templates.TemplateResponse(
        request, "game_history.html", {"user": user, "games": games}
    )


@router.get("/player/{name}", response_class=HTMLResponse)
def player_detail(name: str, request: Request, user: dict = Depends(get_current_user)) -> HTMLResponse:
    detail = get_player_detail(name)
    if detail is None:
        return HTMLResponse("Player not found", status_code=404)
    return templates.TemplateResponse(
        request, "player_detail.html", {"user": user, **detail}
    )
