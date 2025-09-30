from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import apps.api.models.db as db_module
from apps.api.deps import get_db
from apps.api.main import app
from apps.api.models.db import Base
from apps.api.services import scan_service
import apps.worker.tasks as worker_tasks


@pytest.fixture()
def test_sessionmaker(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    monkeypatch.setattr(db_module, "engine", engine, raising=False)
    monkeypatch.setattr(db_module, "SessionLocal", TestingSessionLocal, raising=False)
    monkeypatch.setattr(worker_tasks, "SessionLocal", TestingSessionLocal, raising=False)

    yield TestingSessionLocal

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_sessionmaker):
    session = test_sessionmaker()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(test_sessionmaker):
    def override_get_db():
        db = test_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def queue_stub(monkeypatch):
    jobs: list[tuple[tuple, dict]] = []

    def enqueue(*args, **kwargs):
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        jobs.append((args, kwargs))
        return SimpleNamespace(id=job_id)

    monkeypatch.setattr(scan_service, "q", SimpleNamespace(enqueue=enqueue))
    return jobs
