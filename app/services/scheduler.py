from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logging import logger
from app.database.session import SessionLocal
from app.services.reminder_service import ReminderService

_scheduler: BackgroundScheduler | None = None
_reminder_service = ReminderService()


def _process_reminders() -> None:
    db = SessionLocal()
    try:
        notifications = _reminder_service.send_due_reminders(db)
        if notifications:
            logger.info("Sent %s reminder notifications", len(notifications))
    except Exception:
        logger.exception("Reminder job failed")
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _process_reminders,
        trigger="interval",
        minutes=1,
        id="send_reminders",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Reminder scheduler started")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Reminder scheduler stopped")
