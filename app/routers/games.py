"""Routes for entering and submitting new games."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database import get_player_names, submit_game
from app.dependencies import get_current_user
from app.templates_engine import templates

router = APIRouter(tags=["games"])


@router.get("/new-game", response_class=HTMLResponse)
def new_game(request: Request, user: dict = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "new_game.html", {"user": user, "players": get_player_names()}
    )


@router.post("/submit-score")
def submit_score(
    request: Request,
    user: dict = Depends(get_current_user),
    t1p1: str = Form(...),
    t1p2: str = Form(""),
    t2p1: str = Form(...),
    t2p2: str = Form(""),
    t1_score: int = Form(...),
    t2_score: int = Form(...),
) -> RedirectResponse:
    submit_game(t1p1, t1p2.strip(), t2p1, t2p2.strip(), t1_score=t1_score, t2_score=t2_score)
    return RedirectResponse(request.url_for("home"), status_code=303)
