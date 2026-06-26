"""
Rule-based natural-language fallback.

This module lets MediGuardian keep working with ZERO LLM calls when the
Gemini API is unavailable (missing key or free-tier rate limit / 429).
It performs lightweight intent detection and parameter extraction, then
calls the same service layer the AI tools use, so behavior stays
consistent with the agent path.

It is intentionally deterministic and free — no external API required.
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.agents.collaboration import (
    analytics_consults_medication_for_log,
    collaboration_step,
    medication_registers_with_reminders,
    reminder_consults_medication,
)
from app.services.adherence_service import (
    AdherenceService,
    CaregiverService,
    PreferenceService,
)
from app.services.medication_service import MedicationService

_medications = MedicationService()
_caregivers = CaregiverService()
_preferences = PreferenceService()

_DOSAGE_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|iu|units?|tablets?|pills?|caps?|capsules?|drops?|puffs?))",
    re.IGNORECASE,
)
_TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", re.IGNORECASE)
_TIME_24_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")

_TIME_WORDS = {
    "morning": "08:00",
    "noon": "12:00",
    "midday": "12:00",
    "afternoon": "14:00",
    "evening": "18:00",
    "night": "21:00",
    "bedtime": "22:00",
}

_FILLER_WORDS = {
    "register", "add", "create", "new", "medication", "medicine", "med", "drug",
    "please", "my", "a", "an", "the", "take", "taking", "of", "dose", "daily",
    "every", "day", "morning", "evening", "night", "noon", "at", "for", "to",
    "i", "need", "want", "with",
}


def _parse_time(text: str) -> str:
    match = _TIME_RE.search(text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        meridiem = match.group(3).lower()
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    match = _TIME_24_RE.search(text)
    if match:
        return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"

    for word, value in _TIME_WORDS.items():
        if word in text.lower():
            return value
    return "08:00"


def _parse_medication(text: str) -> tuple[str, str, str]:
    dosage = ""
    dosage_match = _DOSAGE_RE.search(text)
    if dosage_match:
        dosage = dosage_match.group(1).replace(" ", "")

    time_of_day = _parse_time(text)

    working = text
    if dosage_match:
        working = working[: dosage_match.start()]
    working = re.sub(r"[^a-zA-Z\s\-]", " ", working)

    words = [
        w for w in working.split()
        if w.lower() not in _FILLER_WORDS and len(w) >= 1
    ]
    name = " ".join(words).strip().title() or "Medication"
    return name, dosage or "As prescribed", time_of_day


def _format_medications(meds: list) -> str:
    if not meds:
        return "You don't have any medications registered yet. Try: \"Register aspirin 100mg at 8am\"."
    lines = [f"• {m.name} ({m.dosage})" for m in meds]
    return "Here are your active medications:\n" + "\n".join(lines)


def handle(db: Session, user_id: int, message: str) -> dict | None:
    """Return a response dict if an intent is matched, else None."""
    text = message.lower().strip()

    def result(
        response: str,
        agent: str,
        tool: str,
        args: dict | None = None,
        collaboration: list[dict] | None = None,
    ) -> dict:
        return {
            "response": response,
            "agent": agent,
            "traces": [{
                "agent": agent,
                "tool": tool,
                "args": args or {},
                "collaboration": collaboration or [],
            }],
            "offline": True,
        }

    # List medications
    if re.search(r"\b(list|show|what|which|view)\b.*\b(medications?|medicines?|meds?|drugs?|pills?)\b", text) \
            or text in {"medications", "my medications", "meds", "my meds", "medicines", "my medicines"}:
        meds = _medications.list_for_user(db, user_id)
        return result(_format_medications(meds), "MedicationAgent", "list_medications")

    # Adherence report
    if re.search(r"\b(adherence|report|how am i doing|compliance|stats|statistics)\b", text):
        report = _adherence.report(db, user_id)
        collab = [
            collaboration_step(
                "AnalyticsAgent",
                "MedicationAgent",
                "list_medications",
                "Cross-check medication list when computing adherence",
                "Medication inventory loaded for report context",
            )
        ]
        response = (
            f"Adherence report: {report['adherence_rate']}% "
            f"({report['taken']} taken, {report['missed']} missed, "
            f"{report['skipped']} skipped out of {report['total_doses']} doses)."
        )
        return result(response, "AnalyticsAgent", "get_adherence_report", report, collab)

    # Next dose / today's reminders
    if re.search(r"\b(next dose|today|upcoming|schedule|when.*(dose|medicine|medication|take))\b", text):
        meds, today, collab = reminder_consults_medication(db, user_id, generate=True)
        pending = [r for r in today if r["status"] == "pending"]
        if pending:
            nxt = pending[0]
            response = (
                f"Your next dose is {nxt['medication']} ({nxt['dosage']}) "
                f"at {nxt['time']}. You have {len(pending)} dose(s) scheduled today."
            )
        elif today:
            response = "All of today's doses are already handled. Nice work!"
        elif meds:
            response = "No doses are scheduled for today based on your current schedules."
        else:
            response = "You don't have any medications registered yet. Add one to get reminders."
        return result(
            response,
            "ReminderAgent",
            "generate_reminder_schedules",
            collaboration=collab,
        )

    # Generate reminders
    if re.search(r"\b(remind|reminder|generate.*schedule|set up.*schedule)\b", text):
        meds, _, collab = reminder_consults_medication(db, user_id, generate=True)
        response = (
            f"Generated reminders for {len(meds)} medication(s) after "
            f"MedicationAgent confirmed the active list."
        )
        return result(
            response,
            "ReminderAgent",
            "generate_reminder_schedules",
            collaboration=collab,
        )

    # Log a dose
    log_match = re.search(r"\b(took|taken|log|missed|skip|skipped|had)\b", text)
    if log_match:
        if "miss" in text:
            status = "missed"
        elif "skip" in text:
            status = "skipped"
        else:
            status = "taken"
        target, collab = analytics_consults_medication_for_log(db, user_id, message)
        if target is None:
            return result(
                "I couldn't find a medication to log. Register one first, e.g. \"Register aspirin 100mg\".",
                "AnalyticsAgent",
                "log_medication_taken",
                collaboration=collab,
            )
        _adherence.log_dose(db, user_id, target.id, status=status)
        if status == "missed":
            collab.append(
                collaboration_step(
                    "AnalyticsAgent",
                    "CaregiverAgent",
                    "check_miss_threshold",
                    "Consult caregiver rules after missed dose",
                    "Caregiver alert threshold evaluated",
                )
            )
        return result(
            f"Logged {target.name} as {status}.",
            "AnalyticsAgent",
            "log_medication_taken",
            {"medication_id": target.id, "status": status},
            collab,
        )

    # Add caregiver
    caregiver_match = re.search(r"\b(add|register)\b.*\bcaregiver\b", text)
    if caregiver_match:
        name_match = re.search(r"caregiver\s+(?:named\s+|called\s+)?([a-zA-Z][a-zA-Z\s]+)", message, re.IGNORECASE)
        name = name_match.group(1).strip().title() if name_match else "Caregiver"
        caregiver = _caregivers.add(db, user_id, name=name)
        return result(
            f"Added caregiver {caregiver.name}. They'll be alerted after repeated missed doses.",
            "CaregiverAgent",
            "add_caregiver",
            {"name": name},
        )

    # List caregivers
    if re.search(r"\b(list|show|who).*caregiver", text) or text == "caregivers":
        cgs = _caregivers.list_for_user(db, user_id)
        if not cgs:
            response = "You have no caregivers registered yet."
        else:
            response = "Your caregivers:\n" + "\n".join(
                f"• {c.name}" + (f" ({c.email})" if c.email else "") for c in cgs
            )
        return result(response, "CaregiverAgent", "list_caregivers")

    # Register / add medication (checked after caregiver to avoid clashes)
    if re.search(r"\b(register|add|create|start|new)\b", text) or _DOSAGE_RE.search(message):
        name, dosage, time_of_day = _parse_medication(message)
        medication, collab = medication_registers_with_reminders(
            db, user_id, name, dosage, time_of_day
        )
        return result(
            f"Registered {medication.name} ({medication.dosage}) at {time_of_day}. "
            f"Reminders have been scheduled.",
            "MedicationAgent",
            "register_medication",
            {"name": name, "dosage": dosage, "time_of_day": time_of_day},
            collab,
        )

    # Greeting / help
    if re.search(r"\b(hi|hello|hey|help|what can you|how do)\b", text):
        response = (
            "Hi! I'm MediGuardian. I can help you:\n"
            "• Register medications (\"Register aspirin 100mg at 8am\")\n"
            "• List your medications (\"What medications am I taking?\")\n"
            "• Log doses (\"I took my aspirin\")\n"
            "• Check adherence (\"How is my adherence?\")\n"
            "• Find your next dose (\"When is my next dose?\")\n"
            "• Manage caregivers (\"Add caregiver Jane\")"
        )
        return result(response, "Coordinator", "help")

    return None
