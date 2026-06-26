"""
Coordinator Agent.

The Coordinator is the single entry point for the AI concierge. It is a
tool-calling Gemini agent that directly orchestrates every capability the
specialist agents represent (medication, reminder, memory, caregiver,
analytics, safety).

NOTE ON ARCHITECTURE
--------------------
The conceptual multi-agent design lives in ``app/agents/specialists.py`` —
each specialist owns a focused slice of tools and its own system prompt.
For runtime reliability we register those same tools directly on the
Coordinator instead of using ADK ``sub_agents`` delegation. ADK 2.3's
dynamic-node scheduler can raise ``RuntimeError: Task cannot await on
itself`` when a delegated sub-agent transfers control back to its parent
within a single turn, which makes live chat flaky. Holding the tools on
the Coordinator keeps the same capabilities with deterministic behavior.
"""

from google.adk.agents import Agent

from app.core.constants import DEFAULT_MODEL
from app.prompts.coordinator import COORDINATOR_PROMPT
from app.tools.medication_tools import (
    add_caregiver,
    check_medical_safety,
    delete_medication,
    generate_reminder_schedules,
    get_adherence_report,
    get_conversation_history,
    list_caregivers,
    list_medications,
    log_medication_taken,
    register_medication,
    update_medication,
    update_user_preferences,
)

root_agent = Agent(
    name="Coordinator",
    model=DEFAULT_MODEL,
    description="Coordinates MediGuardian AI medication management.",
    instruction=COORDINATOR_PROMPT,
    tools=[
        # Medication management
        register_medication,
        update_medication,
        delete_medication,
        list_medications,
        # Reminders
        generate_reminder_schedules,
        # Adherence & analytics
        log_medication_taken,
        get_adherence_report,
        # Caregivers
        add_caregiver,
        list_caregivers,
        # Memory & preferences
        update_user_preferences,
        get_conversation_history,
        # Safety guardrail
        check_medical_safety,
    ],
)
