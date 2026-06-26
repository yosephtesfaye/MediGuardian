from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.database.base import Base

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def _run_migrations() -> None:
    """Lightweight schema migrations for SQLite dev databases."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    insp = inspect(engine)
    if "agent_logs" in insp.get_table_names():
        columns = {c["name"] for c in insp.get_columns("agent_logs")}
        if "trace" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE agent_logs ADD COLUMN trace TEXT"))


def init_db() -> None:
    from app.models import entities  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _run_migrations()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
