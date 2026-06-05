from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templates_engine import templates

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"app_name": "Tafelvoetbal"})
