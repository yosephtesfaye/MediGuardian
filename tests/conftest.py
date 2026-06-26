import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.base import Base


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from app.models import entities  # noqa: F401
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(autouse=True)
def override_db(test_engine, monkeypatch):
    TestSession = sessionmaker(bind=test_engine)

    def _get_test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr("app.database.session.SessionLocal", TestSession)
    monkeypatch.setattr("app.dependencies.get_db", _get_test_db)

    # Clear tables between tests
    db = TestSession()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()
