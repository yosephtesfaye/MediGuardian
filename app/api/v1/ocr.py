from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_db, get_medication_service, get_ocr_service
from app.schemas.ocr import OCRResponse, PrescriptionMedication
from app.services.medication_service import MedicationService
from app.services.ocr_service import OCRService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/ocr", tags=["OCR"])


@router.post(
    "/prescription",
    response_model=OCRResponse,
    summary="Extract medications from prescription image",
    description="Upload a prescription photo. Gemini Vision extracts medication details.",
)
async def extract_prescription(
    file: UploadFile = File(..., description="Prescription image (JPEG/PNG)"),
    user_id: int = 1,
    auto_register: bool = False,
    db: Session = Depends(get_db),
    ocr: OCRService = Depends(get_ocr_service),
    meds: MedicationService = Depends(get_medication_service),
) -> OCRResponse:
    result = await ocr.extract_from_image(file)
    registered = []

    if auto_register and result.get("medications"):
        for item in result["medications"]:
            medication = meds.register(
                db,
                user_id=user_id,
                name=item.get("name", "Unknown"),
                dosage=item.get("dosage", "As prescribed"),
                instructions=item.get("instructions"),
                time_of_day=item.get("time_of_day") or "08:00",
            )
            registered.append(medication.id)

    return OCRResponse(
        medications=[
            PrescriptionMedication(**m) for m in result.get("medications", [])
        ],
        patient_name=result.get("patient_name"),
        doctor_name=result.get("doctor_name"),
        confidence=result.get("confidence", "low"),
        registered_ids=registered,
    )
