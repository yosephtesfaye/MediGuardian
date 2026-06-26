import os
import time

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agents.coordinator.agent import root_agent
from app.core.config import settings
from app.core.logging import logger
from app.database.session import SessionLocal
from app.repositories.memory_repository import MemoryRepository
from app.services import fallback_nlu
from app.services.dashboard_service import MemoryService
from app.tools.safety import classify_safety_violation, safety_response

_memory_service = MemoryService()

# Maps each tool to the specialist agent it conceptually belongs to, so the
# trace UI can still present MediGuardian's multi-agent architecture even
# though the Coordinator executes the tools directly for reliability.
TOOL_TO_SPECIALIST = {
    "register_medication": "MedicationAgent",
    "update_medication": "MedicationAgent",
    "delete_medication": "MedicationAgent",
    "list_medications": "MedicationAgent",
    "generate_reminder_schedules": "ReminderAgent",
    "log_medication_taken": "AnalyticsAgent",
    "get_adherence_report": "AnalyticsAgent",
    "add_caregiver": "CaregiverAgent",
    "list_caregivers": "CaregiverAgent",
    "update_user_preferences": "MemoryAgent",
    "get_conversation_history": "MemoryAgent",
    "check_medical_safety": "SafetyAgent",
}


# When Gemini returns a quota error, skip live calls for this many seconds
# and answer instantly with the free rule-based engine instead of waiting
# through the client's internal retry/backoff on every message.
_QUOTA_COOLDOWN_SECONDS = 60


class AIRunner:

    _quota_cooldown_until: float = 0.0

    def __init__(self) -> None:
        if settings.GEMINI_API_KEY:
            os.environ.setdefault("GOOGLE_API_KEY", settings.GEMINI_API_KEY)
            os.environ.setdefault("GEMINI_API_KEY", settings.GEMINI_API_KEY)

        self.runner = InMemoryRunner(
            agent=root_agent,
            app_name="MediGuardian",
        )

    async def _ensure_session(self, user_id: str, session_id: str) -> None:
        session_service = self.runner.session_service
        existing = await session_service.get_session(
            app_name=self.runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        if existing is None:
            await session_service.create_session(
                app_name=self.runner.app_name,
                user_id=user_id,
                session_id=session_id,
            )

    async def run(
        self,
        message: str,
        user_id: str = "1",
        session_id: str = "default",
    ) -> dict:
        violation = classify_safety_violation(message)
        if violation:
            response = safety_response(violation)
            self._log_trace(int(user_id), "SafetyAgent", "blocked_request", violation)
            return {"response": response, "agent": "SafetyAgent", "traces": []}

        # Free, deterministic path: no API key, or we recently hit the Gemini
        # quota → use the rule-based engine so the assistant stays fully
        # functional at zero cost without waiting through retry backoff.
        if not settings.GEMINI_API_KEY:
            return self._offline_reply(user_id, session_id, message)

        if time.monotonic() < AIRunner._quota_cooldown_until:
            offline = self._offline_reply(user_id, session_id, message)
            offline["response"] = (
                "[Offline mode — Gemini quota reached] " + offline["response"]
            )
            return offline

        db = SessionLocal()
        try:
            _memory_service.save_message(
                db, int(user_id), session_id, "user", message
            )
            context = _memory_service.get_context(db, int(user_id), message)
        finally:
            db.close()

        enriched = message
        if context:
            enriched = f"[User context]\n{context}\n\n[User message]\n{message}"

        content = types.Content(
            role="user",
            parts=[types.Part(text=enriched)],
        )

        final_text = ""
        active_agent = "Coordinator"
        traces: list[dict] = []

        try:
            await self._ensure_session(user_id, session_id)
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.author and event.author != "user":
                    active_agent = event.author
                if not event.content or not event.content.parts:
                    continue
                if event.author == "user":
                    continue
                for part in event.content.parts:
                    if part.text:
                        final_text = part.text
                    if part.function_call:
                        tool_name = part.function_call.name
                        specialist = TOOL_TO_SPECIALIST.get(tool_name, "Coordinator")
                        active_agent = specialist
                        traces.append({
                            "agent": specialist,
                            "tool": tool_name,
                            "args": dict(part.function_call.args or {}),
                            "collaboration": [],
                        })
            traces = self._enrich_collaboration(traces)
        except Exception as exc:
            logger.exception("AI runner failed: %s", exc)
            err = str(exc)
            is_quota = "RESOURCE_EXHAUSTED" in err or "429" in err
            is_auth = (
                "API key" in err or "PERMISSION_DENIED" in err or "401" in err
            )
            if is_quota or is_auth:
                if is_quota:
                    AIRunner._quota_cooldown_until = (
                        time.monotonic() + _QUOTA_COOLDOWN_SECONDS
                    )
                # Gracefully degrade to the free rule-based engine so the
                # user still gets a useful answer at no cost.
                offline = self._offline_reply(user_id, session_id, message)
                prefix = (
                    "[Offline mode — Gemini quota reached] "
                    if is_quota
                    else "[Offline mode — set GEMINI_API_KEY for full AI] "
                )
                offline["response"] = prefix + offline["response"]
                return offline
            return {
                "response": "I encountered an error. Please try again.",
                "agent": active_agent,
                "traces": traces,
            }

        if not final_text:
            final_text = "I processed your request."

        db = SessionLocal()
        try:
            _memory_service.save_message(
                db, int(user_id), session_id, "assistant", final_text
            )
            self._log_trace(
                int(user_id),
                active_agent,
                "chat_response",
                final_text[:200],
                trace=str(traces) if traces else None,
            )
        finally:
            db.close()

        return {"response": final_text, "agent": active_agent, "traces": traces}

    def _offline_reply(
        self,
        user_id: str,
        session_id: str,
        message: str,
    ) -> dict:
        """Answer using the free rule-based engine (no LLM calls)."""
        db = SessionLocal()
        try:
            _memory_service.save_message(
                db, int(user_id), session_id, "user", message
            )
            result = fallback_nlu.handle(db, int(user_id), message)
            if result is None:
                result = {
                    "response": (
                        "I can help you register medications, list them, log "
                        "doses, check adherence, find your next dose, and manage "
                        "caregivers. Try \"What medications am I taking?\""
                    ),
                    "agent": "Coordinator",
                    "traces": [],
                }
            _memory_service.save_message(
                db, int(user_id), session_id, "assistant", result["response"]
            )
            MemoryRepository(db).log_agent(
                result.get("agent", "Coordinator"),
                "offline_reply",
                result["response"][:200],
                int(user_id),
            )
        finally:
            db.close()
        return result

    @staticmethod
    def _enrich_collaboration(traces: list[dict]) -> list[dict]:
        """Add explicit collaboration steps when multiple agents' tools appear."""
        tools = [t.get("tool") for t in traces]
        if not tools:
            return traces

        for trace in traces:
            tool = trace.get("tool")
            collab: list[dict] = trace.get("collaboration") or []

            if tool == "generate_reminder_schedules" and "list_medications" in tools:
                collab.append({
                    "from": "ReminderAgent",
                    "to": "MedicationAgent",
                    "action": "list_medications",
                    "reason": "Confirm active medications before scheduling",
                    "result": "Medication inventory verified",
                })
            if tool == "register_medication":
                collab.append({
                    "from": "MedicationAgent",
                    "to": "ReminderAgent",
                    "action": "generate_reminder_schedules",
                    "reason": "Auto-schedule reminders for new medication",
                    "result": "Reminder windows created",
                })
            if tool == "log_medication_taken":
                collab.append({
                    "from": "AnalyticsAgent",
                    "to": "MedicationAgent",
                    "action": "list_medications",
                    "reason": "Resolve medication before logging dose",
                    "result": "Medication identity confirmed",
                })
            if collab:
                trace["collaboration"] = collab

        return traces

    def _log_trace(
        self,
        user_id: int,
        agent: str,
        action: str,
        details: str,
        trace: str | None = None,
    ) -> None:
        db = SessionLocal()
        try:
            MemoryRepository(db).log_agent(agent, action, details, user_id, trace)
        finally:
            db.close()
