from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import Caregiver, Medication, MedicationLog, Notification
from app.repositories.memory_repository import MemoryRepository
from app.repositories.user_repository import UserRepository


class AdherenceService:

    def log_dose(
        self,
        db: Session,
        user_id: int,
        medication_id: int,
        status: str = "taken",
        notes: str | None = None,
    ) -> MedicationLog:
        log = MedicationLog(
            user_id=user_id,
            medication_id=medication_id,
            status=status,
            notes=notes,
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        if status == "missed":
            self._check_caregiver_alerts(db, user_id, medication_id)
            MemoryRepository(db).log_agent(
                "AnalyticsAgent",
                "consult_caregiver",
                f"Missed dose on medication {medication_id} — CaregiverAgent threshold check",
                user_id,
                trace="Collaboration: AnalyticsAgent → CaregiverAgent",
            )

        MemoryRepository(db).log_agent(
            "AnalyticsAgent",
            "log_adherence",
            f"{status} medication {medication_id}",
            user_id,
        )
        return log

    def _check_caregiver_alerts(
        self,
        db: Session,
        user_id: int,
        medication_id: int,
    ) -> None:
        from datetime import datetime

        caregivers = (
            db.query(Caregiver)
            .filter(Caregiver.user_id == user_id, Caregiver.active.is_(True))
            .all()
        )
        if not caregivers:
            return

        missed_count = (
            db.query(func.count(MedicationLog.id))
            .filter(
                MedicationLog.user_id == user_id,
                MedicationLog.medication_id == medication_id,
                MedicationLog.status == "missed",
            )
            .scalar()
        )

        medication = db.get(Medication, medication_id)
        for caregiver in caregivers:
            if missed_count < caregiver.notify_on_miss_count:
                continue
            message = (
                f"Caregiver alert: {medication.name} missed {missed_count} times."
            )
            db.add(
                Notification(
                    user_id=user_id,
                    caregiver_id=caregiver.id,
                    type="caregiver_alert",
                    message=message,
                    status="sent",
                    sent_at=datetime.utcnow(),
                )
            )
        db.commit()

    def report(self, db: Session, user_id: int) -> dict:
        logs = db.query(MedicationLog).filter(MedicationLog.user_id == user_id).all()
        total = len(logs)
        taken = sum(1 for log in logs if log.status == "taken")
        missed = sum(1 for log in logs if log.status == "missed")
        skipped = sum(1 for log in logs if log.status == "skipped")
        rate = (taken / total * 100) if total else 0.0

        MemoryRepository(db).log_agent(
            "AnalyticsAgent",
            "generate_report",
            f"Adherence rate {rate:.1f}%",
            user_id,
        )
        return {
            "user_id": user_id,
            "total_doses": total,
            "taken": taken,
            "missed": missed,
            "skipped": skipped,
            "adherence_rate": round(rate, 2),
        }

    def heatmap(self, db: Session, user_id: int, days: int = 30) -> list[dict]:
        from datetime import datetime, timedelta

        start = datetime.utcnow() - timedelta(days=days)
        logs = (
            db.query(MedicationLog)
            .filter(
                MedicationLog.user_id == user_id,
                MedicationLog.taken_at >= start,
            )
            .all()
        )
        by_date: dict[str, dict] = {}
        for log in logs:
            key = log.taken_at.strftime("%Y-%m-%d")
            if key not in by_date:
                by_date[key] = {"date": key, "taken": 0, "missed": 0, "skipped": 0}
            by_date[key][log.status] = by_date[key].get(log.status, 0) + 1
        return list(by_date.values())


class CaregiverService:

    def add(
        self,
        db: Session,
        user_id: int,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        notify_on_miss_count: int = 3,
    ) -> Caregiver:
        UserRepository(db).get_or_create(user_id)
        caregiver = Caregiver(
            user_id=user_id,
            name=name,
            email=email,
            phone=phone,
            notify_on_miss_count=notify_on_miss_count,
        )
        db.add(caregiver)
        db.commit()
        db.refresh(caregiver)
        MemoryRepository(db).log_agent(
            "CaregiverAgent",
            "add_caregiver",
            f"Added {name}",
            user_id,
        )
        return caregiver

    def list_for_user(self, db: Session, user_id: int) -> list[Caregiver]:
        return (
            db.query(Caregiver)
            .filter(Caregiver.user_id == user_id, Caregiver.active.is_(True))
            .all()
        )


class PreferenceService:

    def get_or_create(self, db: Session, user_id: int):
        from app.models.entities import UserPreference

        UserRepository(db).get_or_create(user_id)
        preference = (
            db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )
        if preference is None:
            preference = UserPreference(user_id=user_id)
            db.add(preference)
            db.commit()
            db.refresh(preference)
        return preference

    def update(self, db: Session, user_id: int, **fields):
        preference = self.get_or_create(db, user_id)
        for key, value in fields.items():
            if value is not None and hasattr(preference, key):
                setattr(preference, key, value)
        db.commit()
        db.refresh(preference)
        MemoryRepository(db).log_agent(
            "MemoryAgent",
            "update_preferences",
            str(fields),
            user_id,
        )
        return preference
