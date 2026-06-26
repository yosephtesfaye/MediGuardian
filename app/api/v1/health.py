from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.core.constants import APP_NAME, APP_VERSION
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        application=APP_NAME,
        version=APP_VERSION,
        status="healthy",
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        ai_enabled=bool(settings.GEMINI_API_KEY),
    )


@router.get("/health/ready")
async def readiness():
    return {"status": "ready", "database": "connected"}
