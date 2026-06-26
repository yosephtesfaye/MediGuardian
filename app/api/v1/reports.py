from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_report_service
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/v1/users/{user_id}/reports", tags=["Reports"])


@router.get("/csv", summary="Export adherence report as CSV")
def export_csv(
    user_id: int,
    db: Session = Depends(get_db),
    service: ReportService = Depends(get_report_service),
) -> Response:
    content = service.export_csv(db, user_id)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=adherence_{user_id}.csv"},
    )


@router.get("/pdf", summary="Export adherence report as PDF")
def export_pdf(
    user_id: int,
    db: Session = Depends(get_db),
    service: ReportService = Depends(get_report_service),
) -> Response:
    content = service.export_pdf(db, user_id)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=adherence_{user_id}.pdf"},
    )
