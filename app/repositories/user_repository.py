from sqlalchemy.orm import Session

from app.models.entities import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_or_create(self, user_id: int, name: str | None = None) -> User:
        user = self.get(user_id)
        if user is None:
            user = User(id=user_id, name=name or f"User {user_id}")
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user

    def list_patients_for_caregiver(self, caregiver_user_id: int) -> list[User]:
        from app.models.entities import FamilyLink

        links = (
            self.db.query(FamilyLink)
            .filter(
                FamilyLink.caregiver_user_id == caregiver_user_id,
                FamilyLink.active.is_(True),
            )
            .all()
        )
        patient_ids = [link.patient_user_id for link in links]
        if not patient_ids:
            return []
        return self.db.query(User).filter(User.id.in_(patient_ids)).all()
