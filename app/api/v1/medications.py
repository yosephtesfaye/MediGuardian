from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.dependencies import (
    get_adherence_service,
    get_db,
    get_medication_service,
)
from app.exceptions.errors import MediGuardianError, NotFoundError
from app.schemas.medication import (
    AdherenceLogCreate,
    AdherenceLogResponse,
    AdherenceReport,
    CaregiverCreate,
    CaregiverResponse,
    MedicationCreate,
    MedicationResponse,
    MedicationUpdate,
    PreferenceResponse,
    PreferenceUpdate,
)
from app.services.adherence_service import AdherenceService, CaregiverService, PreferenceService
from app.services.medication_service import MedicationService
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/api/v1", tags=["Medications"])
limiter = Limiter(key_func=get_remote_address)
_reminder_service = ReminderService()
_caregiver_service = CaregiverService()
_preference_service = PreferenceService()


@router.post(
    "/users/{user_id}/medications",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a medication",
    responses={201: {"description": "Medication registered successfully"}},
)
@limiter.limit("30/minute")
def register_medication(
    request: Request,
    user_id: int,
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationResponse:
    return service.register(
        db,
        user_id=user_id,
        name=payload.name,
        dosage=payload.dosage,
        instructions=payload.instructions,
        time_of_day=payload.time_of_day,
        days_of_week=payload.days_of_week,
    )


@router.get(
    "/users/{user_id}/medications",
    response_model=list[MedicationResponse],
    summary="List active medications",
)
def list_medications(
    user_id: int,
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> list[MedicationResponse]:
    return service.list_for_user(db, user_id)


@router.patch(
    "/users/{user_id}/medications/{medication_id}",
    response_model=MedicationResponse,
    summary="Update a medication",
)
def update_medication(
    user_id: int,
    medication_id: int,
    payload: MedicationUpdate,
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> MedicationResponse:
    try:
        return service.update(
            db,
            user_id=user_id,
            medication_id=medication_id,
            **payload.model_dump(exclude_unset=True),
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.delete(
    "/users/{user_id}/medications/{medication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a medication",
)
def delete_medication(
    user_id: int,
    medication_id: int,
    db: Session = Depends(get_db),
    service: MedicationService = Depends(get_medication_service),
) -> None:
    try:
        service.delete(db, user_id, medication_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.post("/users/{user_id}/reminders/generate", status_code=status.HTTP_201_CREATED)
def generate_reminders(user_id: int, db: Session = Depends(get_db)) -> dict:
    reminders = _reminder_service.generate_schedules(db, user_id=user_id)
    return {"count": len(reminders)}


@router.post(
    "/users/{user_id}/adherence",
    response_model=AdherenceLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def log_adherence(
    user_id: int,
    payload: AdherenceLogCreate,
    db: Session = Depends(get_db),
    service: AdherenceService = Depends(get_adherence_service),
) -> AdherenceLogResponse:
    return service.log_dose(
        db,
        user_id=user_id,
        medication_id=payload.medication_id,
        status=payload.status,
        notes=payload.notes,
    )


@router.get("/users/{user_id}/adherence/report", response_model=AdherenceReport)
def adherence_report(
    user_id: int,
    db: Session = Depends(get_db),
    service: AdherenceService = Depends(get_adherence_service),
) -> AdherenceReport:
    return service.report(db, user_id)


@router.post(
    "/users/{user_id}/caregivers",
    response_model=CaregiverResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_caregiver(
    user_id: int,
    payload: CaregiverCreate,
    db: Session = Depends(get_db),
) -> CaregiverResponse:
    return _caregiver_service.add(
        db,
        user_id=user_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        notify_on_miss_count=payload.notify_on_miss_count,
    )


@router.get("/users/{user_id}/caregivers", response_model=list[CaregiverResponse])
def list_caregivers(user_id: int, db: Session = Depends(get_db)) -> list[CaregiverResponse]:
    return _caregiver_service.list_for_user(db, user_id)


@router.get("/users/{user_id}/preferences", response_model=PreferenceResponse)
def get_preferences(user_id: int, db: Session = Depends(get_db)) -> PreferenceResponse:
    return _preference_service.get_or_create(db, user_id)


@router.patch("/users/{user_id}/preferences", response_model=PreferenceResponse)
def update_preferences(
    user_id: int,
    payload: PreferenceUpdate,
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    return _preference_service.update(
        db,
        user_id=user_id,
        **payload.model_dump(exclude_unset=True),
    )
