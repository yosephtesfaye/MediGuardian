from pydantic import BaseModel, Field


class PrescriptionMedication(BaseModel):
    name: str = ""
    dosage: str = ""
    instructions: str = ""
    time_of_day: str = ""


class OCRResponse(BaseModel):
    medications: list[PrescriptionMedication] = Field(default_factory=list)
    patient_name: str | None = None
    doctor_name: str | None = None
    confidence: str = "low"
    registered_ids: list[int] = Field(default_factory=list)
