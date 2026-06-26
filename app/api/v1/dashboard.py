from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_dashboard_service, get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get(
    "/{user_id}",
    summary="Get dashboard summary",
    description="Returns medications, today's reminders, adherence stats, heatmap, and caregivers.",
)
def get_dashboard(
    user_id: int,
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    return service.get_summary(db, user_id)
