from google.adk.agents import Agent

from app.core.constants import DEFAULT_MODEL
from app.prompts.coordinator import (
    ANALYTICS_PROMPT,
    CAREGIVER_PROMPT,
    MEDICATION_PROMPT,
    MEMORY_PROMPT,
    REMINDER_PROMPT,
    SAFETY_PROMPT,
)
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

medication_agent = Agent(
    name="MedicationAgent",
    model=DEFAULT_MODEL,
    description="Registers, updates, deletes, and lists medications.",
    instruction=MEDICATION_PROMPT,
    mode="single_turn",
    tools=[
        register_medication,
        update_medication,
        delete_medication,
        list_medications,
    ],
)

reminder_agent = Agent(
    name="ReminderAgent",
    model=DEFAULT_MODEL,
    description="Generates and manages medication reminder schedules.",
    instruction=REMINDER_PROMPT,
    mode="single_turn",
    tools=[generate_reminder_schedules, list_medications],
)

memory_agent = Agent(
    name="MemoryAgent",
    model=DEFAULT_MODEL,
    description="Stores user preferences and conversation memory.",
    instruction=MEMORY_PROMPT,
    mode="single_turn",
    tools=[update_user_preferences, get_conversation_history],
)

caregiver_agent = Agent(
    name="CaregiverAgent",
    model=DEFAULT_MODEL,
    description="Manages caregivers and missed-dose notifications.",
    instruction=CAREGIVER_PROMPT,
    mode="single_turn",
    tools=[add_caregiver, list_caregivers],
)

analytics_agent = Agent(
    name="AnalyticsAgent",
    model=DEFAULT_MODEL,
    description="Tracks adherence and generates reports.",
    instruction=ANALYTICS_PROMPT,
    mode="single_turn",
    tools=[log_medication_taken, get_adherence_report],
)

safety_agent = Agent(
    name="SafetyAgent",
    model=DEFAULT_MODEL,
    description="Rejects unsafe medical advice requests.",
    instruction=SAFETY_PROMPT,
    mode="single_turn",
    tools=[check_medical_safety],
)
