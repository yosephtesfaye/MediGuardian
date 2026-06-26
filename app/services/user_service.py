from sqlalchemy.orm import Session

from app.models.entities import (
    AgentLog,
    Caregiver,
    ConversationMemory,
    Medication,
    MedicationLog,
    Notification,
    Reminder,
    Schedule,
    User,
    UserPreference,
)


def get_or_create_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id, name=f"User {user_id}")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def log_agent_action(
    db: Session,
    agent_name: str,
    action: str,
    details: str | None = None,
    user_id: int | None = None,
) -> None:
    db.add(
        AgentLog(
            user_id=user_id,
            agent_name=agent_name,
            action=action,
            details=details,
        )
    )
    db.commit()
