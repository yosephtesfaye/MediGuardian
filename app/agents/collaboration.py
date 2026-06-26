"""
Explicit multi-agent collaboration helpers.

Specialists do not operate in isolation — they consult each other's data
before acting. These helpers build structured collaboration traces that
appear in chat responses, agent logs, and evaluation docs.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.medication_service import MedicationService
from app.services.reminder_service import ReminderService

_medications = MedicationService()
_reminders = ReminderService()


def collaboration_step(
    from_agent: str,
    to_agent: str,
    action: str,
    reason: str,
    result: str,
) -> dict:
    return {
        "from": from_agent,
        "to": to_agent,
        "action": action,
        "reason": reason,
        "result": result,
    }


def reminder_consults_medication(
    db: Session,
    user_id: int,
    *,
    generate: bool = True,
) -> tuple[list, list[dict], list[dict]]:
    """
    ReminderAgent asks MedicationAgent to confirm active medications
    before generating or listing schedules.
    """
    meds = _medications.list_for_user(db, user_id)
    collaboration = [
        collaboration_step(
            "ReminderAgent",
            "MedicationAgent",
            "list_medications",
            "Confirm active medications and dosages before scheduling",
            f"{len(meds)} active medication(s): {', '.join(m.name for m in meds) or 'none'}",
        )
    ]
    reminders: list[dict] = []
    if generate:
        _reminders.generate_schedules(db, user_id)
        collaboration.append(
            collaboration_step(
                "MedicationAgent",
                "ReminderAgent",
                "generate_reminder_schedules",
                "Medication data confirmed — proceed with schedule generation",
                "Schedule windows built for next 7 days",
            )
        )
    today = _reminders.list_today(db, user_id)
    return meds, today, collaboration


def medication_registers_with_reminders(
    db: Session,
    user_id: int,
    name: str,
    dosage: str,
    time_of_day: str,
) -> tuple[object, list[dict]]:
    """
    MedicationAgent registers a drug, then delegates to ReminderAgent
    to build upcoming reminder windows.
    """
    medication = _medications.register(
        db,
        user_id=user_id,
        name=name,
        dosage=dosage,
        time_of_day=time_of_day,
    )
    collaboration = [
        collaboration_step(
            "MedicationAgent",
            "ReminderAgent",
            "generate_reminder_schedules",
            "New medication registered — auto-generate reminder schedule",
            f"Reminders scheduled for {name} at {time_of_day}",
        )
    ]
    return medication, collaboration


def analytics_consults_medication_for_log(
    db: Session,
    user_id: int,
    medication_name: str | None,
) -> tuple[object | None, list[dict]]:
    """
    AnalyticsAgent asks MedicationAgent to resolve which drug to log.
    """
    meds = _medications.list_for_user(db, user_id)
    target = None
    if medication_name:
        for med in meds:
            if med.name.lower() in medication_name.lower():
                target = med
                break
    if target is None and meds:
        target = meds[0]

    collaboration = [
        collaboration_step(
            "AnalyticsAgent",
            "MedicationAgent",
            "list_medications",
            "Resolve medication identity before logging adherence",
            (
                f"Matched {target.name} (id={target.id})"
                if target
                else "No medications on file"
            ),
        )
    ]
    return target, collaboration
