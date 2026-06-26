from sqlalchemy.orm import Session

from app.models.entities import Medication, Schedule
from app.repositories.base import BaseRepository


class MedicationRepository(BaseRepository):

    def create(
        self,
        user_id: int,
        name: str,
        dosage: str,
        instructions: str | None,
        time_of_day: str,
        days_of_week: str,
    ) -> Medication:
        medication = Medication(
            user_id=user_id,
            name=name,
            dosage=dosage,
            instructions=instructions,
        )
        self.db.add(medication)
        self.db.flush()
        schedule = Schedule(
            medication_id=medication.id,
            time_of_day=time_of_day,
            days_of_week=days_of_week,
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(medication)
        return medication

    def get(self, user_id: int, medication_id: int) -> Medication | None:
        return (
            self.db.query(Medication)
            .filter(
                Medication.id == medication_id,
                Medication.user_id == user_id,
            )
            .first()
        )

    def list_active(self, user_id: int) -> list[Medication]:
        return (
            self.db.query(Medication)
            .filter(Medication.user_id == user_id, Medication.active.is_(True))
            .all()
        )

    def update(self, medication: Medication, **fields) -> Medication:
        schedule_fields = {}
        for key in ("time_of_day", "days_of_week"):
            if key in fields and fields[key] is not None:
                schedule_fields[key] = fields.pop(key)

        for key, value in fields.items():
            if value is not None and hasattr(medication, key):
                setattr(medication, key, value)

        if schedule_fields:
            schedule = (
                self.db.query(Schedule)
                .filter(Schedule.medication_id == medication.id)
                .first()
            )
            if schedule:
                for key, value in schedule_fields.items():
                    setattr(schedule, key, value)

        self.db.commit()
        self.db.refresh(medication)
        return medication

    def delete(self, medication: Medication) -> None:
        self.db.delete(medication)
        self.db.commit()
