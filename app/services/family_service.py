from sqlalchemy.orm import Session

from app.exceptions.errors import NotFoundError, ValidationError
from app.models.entities import FamilyLink
from app.repositories.memory_repository import MemoryRepository
from app.repositories.user_repository import UserRepository


class FamilyService:

    def link_patient(
        self,
        db: Session,
        caregiver_user_id: int,
        patient_user_id: int,
        relationship: str = "family",
    ) -> FamilyLink:
        if caregiver_user_id == patient_user_id:
            raise ValidationError("Caregiver and patient must be different users.")

        users = UserRepository(db)
        users.get_or_create(caregiver_user_id, name=f"Caregiver {caregiver_user_id}")
        users.get_or_create(patient_user_id, name=f"Patient {patient_user_id}")

        existing = (
            db.query(FamilyLink)
            .filter(
                FamilyLink.caregiver_user_id == caregiver_user_id,
                FamilyLink.patient_user_id == patient_user_id,
            )
            .first()
        )
        if existing:
            existing.active = True
            existing.relationship = relationship
            db.commit()
            db.refresh(existing)
            return existing

        link = FamilyLink(
            caregiver_user_id=caregiver_user_id,
            patient_user_id=patient_user_id,
            relationship=relationship,
        )
        db.add(link)
        db.commit()
        db.refresh(link)

        MemoryRepository(db).log_agent(
            "CaregiverAgent",
            "link_family",
            f"Caregiver {caregiver_user_id} → Patient {patient_user_id}",
            caregiver_user_id,
        )
        return link

    def list_patients(self, db: Session, caregiver_user_id: int) -> list[dict]:
        users = UserRepository(db).list_patients_for_caregiver(caregiver_user_id)
        return [{"id": u.id, "name": u.name, "email": u.email} for u in users]

    def unlink(
        self,
        db: Session,
        caregiver_user_id: int,
        patient_user_id: int,
    ) -> None:
        link = (
            db.query(FamilyLink)
            .filter(
                FamilyLink.caregiver_user_id == caregiver_user_id,
                FamilyLink.patient_user_id == patient_user_id,
            )
            .first()
        )
        if link is None:
            raise NotFoundError("FamilyLink", patient_user_id)
        link.active = False
        db.commit()
