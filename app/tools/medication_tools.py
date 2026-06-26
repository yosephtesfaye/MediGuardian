from google.adk.tools.tool_context import ToolContext

from app.database.session import SessionLocal
from app.services.adherence_service import (
    AdherenceService,
    CaregiverService,
    PreferenceService,
)
from app.services.dashboard_service import MemoryService
from app.services.medication_service import MedicationService
from app.services.reminder_service import ReminderService
from app.tools.safety import is_unsafe_medical_advice, safety_response, classify_safety_violation

_medication_service = MedicationService()
_reminder_service = ReminderService()
_adherence_service = AdherenceService()
_caregiver_service = CaregiverService()
_preference_service = PreferenceService()
_memory_service = MemoryService()


def _user_id(tool_context: ToolContext) -> int:
    raw = tool_context.user_id
    if raw and str(raw).isdigit():
        return int(raw)
    return 1


def register_medication(
    name: str,
    dosage: str,
    instructions: str = "",
    time_of_day: str = "08:00",
    tool_context: ToolContext = None,
) -> dict:
    """Register a new medication for the user."""
    db = SessionLocal()
    try:
        medication = _medication_service.register(
            db,
            user_id=_user_id(tool_context),
            name=name,
            dosage=dosage,
            instructions=instructions or None,
            time_of_day=time_of_day,
        )
        return {
            "id": medication.id,
            "name": medication.name,
            "dosage": medication.dosage,
            "message": f"Registered {medication.name}.",
        }
    finally:
        db.close()


def update_medication(
    medication_id: int,
    name: str = "",
    dosage: str = "",
    instructions: str = "",
    active: bool | None = None,
    time_of_day: str = "",
    tool_context: ToolContext = None,
) -> dict:
    """Update an existing medication."""
    db = SessionLocal()
    try:
        fields = {
            "name": name or None,
            "dosage": dosage or None,
            "instructions": instructions or None,
            "active": active,
            "time_of_day": time_of_day or None,
        }
        medication = _medication_service.update(
            db,
            user_id=_user_id(tool_context),
            medication_id=medication_id,
            **fields,
        )
        if medication is None:
            return {"error": "Medication not found."}
        return {"id": medication.id, "message": f"Updated {medication.name}."}
    finally:
        db.close()


def delete_medication(
    medication_id: int,
    tool_context: ToolContext = None,
) -> dict:
    """Delete a medication."""
    db = SessionLocal()
    try:
        deleted = _medication_service.delete(
            db,
            user_id=_user_id(tool_context),
            medication_id=medication_id,
        )
        if not deleted:
            return {"error": "Medication not found."}
        return {"message": "Medication deleted."}
    finally:
        db.close()


def list_medications(tool_context: ToolContext = None) -> dict:
    """List active medications for the user."""
    db = SessionLocal()
    try:
        medications = _medication_service.list_for_user(
            db,
            user_id=_user_id(tool_context),
        )
        return {
            "medications": [
                {
                    "id": med.id,
                    "name": med.name,
                    "dosage": med.dosage,
                    "instructions": med.instructions,
                }
                for med in medications
            ]
        }
    finally:
        db.close()


def generate_reminder_schedules(
    days: int = 7,
    tool_context: ToolContext = None,
) -> dict:
    """Generate reminder schedules for upcoming days."""
    db = SessionLocal()
    try:
        reminders = _reminder_service.generate_schedules(
            db,
            user_id=_user_id(tool_context),
            days=days,
        )
        return {"count": len(reminders), "message": "Reminder schedules generated."}
    finally:
        db.close()


def log_medication_taken(
    medication_id: int,
    status: str = "taken",
    notes: str = "",
    tool_context: ToolContext = None,
) -> dict:
    """Log medication adherence (taken, missed, or skipped)."""
    db = SessionLocal()
    try:
        log = _adherence_service.log_dose(
            db,
            user_id=_user_id(tool_context),
            medication_id=medication_id,
            status=status,
            notes=notes or None,
        )
        return {"id": log.id, "status": log.status, "message": "Adherence logged."}
    finally:
        db.close()


def get_adherence_report(tool_context: ToolContext = None) -> dict:
    """Generate an adherence report for the user."""
    db = SessionLocal()
    try:
        return _adherence_service.report(db, user_id=_user_id(tool_context))
    finally:
        db.close()


def add_caregiver(
    name: str,
    email: str = "",
    phone: str = "",
    notify_on_miss_count: int = 3,
    tool_context: ToolContext = None,
) -> dict:
    """Register a caregiver for notifications."""
    db = SessionLocal()
    try:
        caregiver = _caregiver_service.add(
            db,
            user_id=_user_id(tool_context),
            name=name,
            email=email or None,
            phone=phone or None,
            notify_on_miss_count=notify_on_miss_count,
        )
        return {"id": caregiver.id, "message": f"Caregiver {caregiver.name} added."}
    finally:
        db.close()


def list_caregivers(tool_context: ToolContext = None) -> dict:
    """List caregivers for the user."""
    db = SessionLocal()
    try:
        caregivers = _caregiver_service.list_for_user(
            db,
            user_id=_user_id(tool_context),
        )
        return {
            "caregivers": [
                {
                    "id": caregiver.id,
                    "name": caregiver.name,
                    "email": caregiver.email,
                    "phone": caregiver.phone,
                }
                for caregiver in caregivers
            ]
        }
    finally:
        db.close()


def update_user_preferences(
    reminder_channel: str = "",
    timezone: str = "",
    notification_enabled: bool | None = None,
    tool_context: ToolContext = None,
) -> dict:
    """Update user notification preferences."""
    db = SessionLocal()
    try:
        preference = _preference_service.update(
            db,
            user_id=_user_id(tool_context),
            reminder_channel=reminder_channel or None,
            timezone=timezone or None,
            notification_enabled=notification_enabled,
        )
        return {
            "reminder_channel": preference.reminder_channel,
            "timezone": preference.timezone,
            "notification_enabled": preference.notification_enabled,
        }
    finally:
        db.close()


def get_conversation_history(
    limit: int = 10,
    tool_context: ToolContext = None,
) -> dict:
    """Retrieve recent conversation history for context."""
    db = SessionLocal()
    try:
        session_id = getattr(tool_context, "session_id", "default") or "default"
        history = _memory_service.get_history(
            db,
            user_id=_user_id(tool_context),
            session_id=session_id,
            limit=limit,
        )
        return {
            "messages": [
                {"role": item.role, "content": item.content}
                for item in reversed(history)
            ]
        }
    finally:
        db.close()


def check_medical_safety(message: str) -> dict:
    """Check whether a message requests unsafe medical advice."""
    category = classify_safety_violation(message)
    if category:
        return {"safe": False, "category": category, "response": safety_response(category)}
    return {"safe": True, "response": "Message appears safe."}
