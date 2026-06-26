from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_family_service
from app.exceptions.errors import MediGuardianError
from app.services.family_service import FamilyService

router = APIRouter(prefix="/api/v1/family", tags=["Family"])


class FamilyLinkRequest(BaseModel):
    caregiver_user_id: int
    patient_user_id: int
    relationship: str = Field(default="family", max_length=64)


class FamilyLinkResponse(BaseModel):
    id: int
    caregiver_user_id: int
    patient_user_id: int
    relationship: str
    active: bool

    model_config = {"from_attributes": True}


@router.post("/link", response_model=FamilyLinkResponse, summary="Link caregiver to patient")
def link_family(
    payload: FamilyLinkRequest,
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> FamilyLinkResponse:
    try:
        return service.link_patient(
            db,
            caregiver_user_id=payload.caregiver_user_id,
            patient_user_id=payload.patient_user_id,
            relationship=payload.relationship,
        )
    except MediGuardianError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc


@router.get("/{caregiver_user_id}/patients", summary="List patients for a caregiver")
def list_patients(
    caregiver_user_id: int,
    db: Session = Depends(get_db),
    service: FamilyService = Depends(get_family_service),
) -> list[dict]:
    return service.list_patients(db, caregiver_user_id)
