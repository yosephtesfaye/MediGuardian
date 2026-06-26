from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.entities import Medication, Notification, Reminder, Schedule
from app.repositories.memory_repository import MemoryRepository


class ReminderService:

    def generate_schedules(self, db: Session, user_id: int, days: int = 7) -> list[Reminder]:
        medications = (
            db.query(Medication)
            .filter(Medication.user_id == user_id, Medication.active.is_(True))
            .all()
        )
        created: list[Reminder] = []
        now = datetime.utcnow()

        for medication in medications:
            for schedule in medication.schedules:
                for day_offset in range(days):
                    target_date = now.date() + timedelta(days=day_offset)
                    weekday = target_date.strftime("%a").lower()[:3]
                    if weekday not in schedule.days_of_week.split(","):
                        continue

                    hour, minute = map(int, schedule.time_of_day.split(":"))
                    scheduled_at = datetime(
                        target_date.year,
                        target_date.month,
                        target_date.day,
                        hour,
                        minute,
                    )
                    if scheduled_at < now:
                        continue

                    existing = (
                        db.query(Reminder)
                        .filter(
                            Reminder.schedule_id == schedule.id,
                            Reminder.scheduled_at == scheduled_at,
                        )
                        .first()
                    )
                    if existing:
                        continue

                    reminder = Reminder(
                        schedule_id=schedule.id,
                        user_id=user_id,
                        scheduled_at=scheduled_at,
                        status="pending",
                    )
                    db.add(reminder)
                    created.append(reminder)

        db.commit()
        for reminder in created:
            db.refresh(reminder)

        MemoryRepository(db).log_agent(
            "ReminderAgent",
            "generate_schedules",
            f"Generated {len(created)} reminders (consulted MedicationAgent data)",
            user_id,
            trace="Collaboration: fetched active medications → built schedule windows",
        )
        return created

    def send_due_reminders(self, db: Session) -> list[Notification]:
        now = datetime.utcnow()
        due = (
            db.query(Reminder)
            .filter(Reminder.status == "pending", Reminder.scheduled_at <= now)
            .all()
        )
        notifications: list[Notification] = []

        for reminder in due:
            schedule = db.get(Schedule, reminder.schedule_id)
            medication = db.get(Medication, schedule.medication_id)
            message = (
                f"Reminder: take {medication.name} ({medication.dosage}) "
                f"at {reminder.scheduled_at.strftime('%H:%M')}."
            )
            notification = Notification(
                user_id=reminder.user_id,
                type="reminder",
                message=message,
                status="sent",
                sent_at=now,
            )
            db.add(notification)
            reminder.status = "sent"
            reminder.sent_at = now
            notifications.append(notification)

        db.commit()
        return notifications

    def list_today(self, db: Session, user_id: int) -> list[dict]:
        today = datetime.utcnow().date()
        reminders = (
            db.query(Reminder)
            .filter(Reminder.user_id == user_id)
            .all()
        )
        results = []
        for reminder in reminders:
            if reminder.scheduled_at.date() != today:
                continue
            schedule = db.get(Schedule, reminder.schedule_id)
            medication = db.get(Medication, schedule.medication_id)
            results.append({
                "id": reminder.id,
                "medication": medication.name,
                "dosage": medication.dosage,
                "time": reminder.scheduled_at.strftime("%H:%M"),
                "status": reminder.status,
            })
        return sorted(results, key=lambda r: r["time"])
