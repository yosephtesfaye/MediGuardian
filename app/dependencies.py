from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.agents.coordinator.service import CoordinatorService
from app.database.session import SessionLocal
from app.repositories.medication_repository import MedicationRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.user_repository import UserRepository
from app.services.adherence_service import AdherenceService
from app.services.dashboard_service import DashboardService
from app.services.family_service import FamilyService
from app.services.medication_service import MedicationService
from app.services.ocr_service import OCRService
from app.services.report_service import ReportService
from app.services.voice_service import VoiceService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_medication_repo(db: Session = Depends(get_db)) -> MedicationRepository:
    return MedicationRepository(db)


def get_memory_repo(db: Session = Depends(get_db)) -> MemoryRepository:
    return MemoryRepository(db)


@lru_cache
def get_coordinator_service() -> CoordinatorService:
    return CoordinatorService()


@lru_cache
def get_medication_service() -> MedicationService:
    return MedicationService()


@lru_cache
def get_adherence_service() -> AdherenceService:
    return AdherenceService()


@lru_cache
def get_dashboard_service() -> DashboardService:
    return DashboardService()


@lru_cache
def get_family_service() -> FamilyService:
    return FamilyService()


@lru_cache
def get_ocr_service() -> OCRService:
    return OCRService()


@lru_cache
def get_report_service() -> ReportService:
    return ReportService()


@lru_cache
def get_voice_service() -> VoiceService:
    return VoiceService()
