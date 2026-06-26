from sqlalchemy.orm import Session

from app.exceptions.errors import NotFoundError
from app.models.entities import Medication
from app.repositories.medication_repository import MedicationRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.user_repository import UserRepository
from app.services.reminder_service import ReminderService


class MedicationService:

    def __init__(self) -> None:
        self.reminders = ReminderService()

    def register(
        self,
        db: Session,
        user_id: int,
        name: str,
        dosage: str,
        instructions: str | None = None,
        time_of_day: str = "08:00",
        days_of_week: str = "mon,tue,wed,thu,fri,sat,sun",
    ) -> Medication:
        users = UserRepository(db)
        meds = MedicationRepository(db)
        memory = MemoryRepository(db)

        users.get_or_create(user_id)
        medication = meds.create(
            user_id, name, dosage, instructions, time_of_day, days_of_week
        )
        self.reminders.generate_schedules(db, user_id)
        memory.log_agent(
            "MedicationAgent",
            "register_medication",
            f"Registered {name}",
            user_id,
            trace=f"Plan: validate → create medication → generate reminders",
        )
        return medication

    def update(
        self,
        db: Session,
        user_id: int,
        medication_id: int,
        **fields,
    ) -> Medication:
        meds = MedicationRepository(db)
        memory = MemoryRepository(db)
        medication = meds.get(user_id, medication_id)
        if medication is None:
            raise NotFoundError("Medication", medication_id)
        updated = meds.update(medication, **fields)
        memory.log_agent(
            "MedicationAgent",
            "update_medication",
            f"Updated {medication_id}",
            user_id,
        )
        return updated

    def delete(self, db: Session, user_id: int, medication_id: int) -> None:
        meds = MedicationRepository(db)
        memory = MemoryRepository(db)
        medication = meds.get(user_id, medication_id)
        if medication is None:
            raise NotFoundError("Medication", medication_id)
        meds.delete(medication)
        memory.log_agent(
            "MedicationAgent",
            "delete_medication",
            f"Deleted {medication_id}",
            user_id,
        )

    def list_for_user(self, db: Session, user_id: int) -> list[Medication]:
        return MedicationRepository(db).list_active(user_id)

    def get(self, db: Session, user_id: int, medication_id: int) -> Medication:
        medication = MedicationRepository(db).get(user_id, medication_id)
        if medication is None:
            raise NotFoundError("Medication", medication_id)
        return medication
