from datetime import datetime

from pydantic import BaseModel, Field


class MedicationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=120)
    instructions: str | None = None
    time_of_day: str = Field(default="08:00", pattern=r"^\d{2}:\d{2}$")
    days_of_week: str = "mon,tue,wed,thu,fri,sat,sun"


class MedicationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    dosage: str | None = Field(default=None, min_length=1, max_length=120)
    instructions: str | None = None
    active: bool | None = None
    time_of_day: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    days_of_week: str | None = None


class MedicationResponse(BaseModel):
    id: int
    user_id: int
    name: str
    dosage: str
    instructions: str | None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaregiverCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str | None = None
    phone: str | None = None
    notify_on_miss_count: int = Field(default=3, ge=1)


class CaregiverResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str | None
    phone: str | None
    notify_on_miss_count: int
    active: bool

    model_config = {"from_attributes": True}


class PreferenceUpdate(BaseModel):
    reminder_channel: str | None = None
    timezone: str | None = None
    notification_enabled: bool | None = None


class PreferenceResponse(BaseModel):
    user_id: int
    reminder_channel: str
    timezone: str
    notification_enabled: bool

    model_config = {"from_attributes": True}


class AdherenceLogCreate(BaseModel):
    medication_id: int
    status: str = Field(default="taken", pattern=r"^(taken|missed|skipped)$")
    notes: str | None = None


class AdherenceLogResponse(BaseModel):
    id: int
    medication_id: int
    user_id: int
    taken_at: datetime
    status: str
    notes: str | None

    model_config = {"from_attributes": True}


class AdherenceReport(BaseModel):
    user_id: int
    total_doses: int
    taken: int
    missed: int
    skipped: int
    adherence_rate: float
