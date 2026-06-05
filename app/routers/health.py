from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Liveness check: confirms the web server is up and responding."""
    return {"status": "ok"}
