"""
Application entry point — MediGuardian AI v1.0
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.memory import router as memory_router
from app.api.v1.chat import router as chat_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.family import router as family_router
from app.api.v1.health import router as health_router
from app.api.v1.medications import router as medications_router
from app.api.v1.ocr import router as ocr_router
from app.api.v1.reports import router as reports_router
from app.api.v1.traces import router as traces_router
from app.api.v1.voice import router as voice_router
from app.core.config import settings
from app.core.constants import APP_DESCRIPTION, APP_NAME, APP_VERSION
from app.core.logging import logger
from app.core.middleware import setup_middleware
from app.database.session import init_db
from app.exceptions.errors import MediGuardianError
from app.exceptions.handlers import (
    generic_exception_handler,
    mediguardian_exception_handler,
)
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.GEMINI_API_KEY:
        os.environ.setdefault("GOOGLE_API_KEY", settings.GEMINI_API_KEY)
        os.environ.setdefault("GEMINI_API_KEY", settings.GEMINI_API_KEY)

    logger.info("Starting %s %s [%s]", APP_NAME, APP_VERSION, settings.APP_ENV)
    logger.info("Database: %s", settings.DATABASE_URL)

    init_db()
    start_scheduler()

    yield

    stop_scheduler()
    logger.info("Application stopped")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Chat", "description": "AI concierge conversation"},
        {"name": "Dashboard", "description": "Aggregated dashboard data"},
        {"name": "Medications", "description": "Medication CRUD & adherence"},
        {"name": "OCR", "description": "Prescription image extraction"},
        {"name": "Reports", "description": "PDF/CSV export"},
        {"name": "Voice", "description": "Text-to-speech reminders"},
        {"name": "Family", "description": "Multi-patient family mode"},
        {"name": "Agent Traces", "description": "Agent reasoning logs"},
        {"name": "Memory", "description": "Long-term semantic memory inspection"},
        {"name": "Health", "description": "Health checks"},
    ],
)

setup_middleware(app)
app.add_exception_handler(MediGuardianError, mediguardian_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(medications_router)
app.include_router(ocr_router)
app.include_router(reports_router)
app.include_router(voice_router)
app.include_router(family_router)
app.include_router(traces_router)
app.include_router(memory_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "dashboard": "http://localhost:5173",
        "status": "running",
    }
