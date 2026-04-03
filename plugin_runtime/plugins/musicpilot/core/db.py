"""Database primitives for Phase 2 metadata persistence."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from .. import models as _models  # noqa: F401
from ..models.base import Base
from .config import DEFAULT_DATABASE_PATH, settings


DEFAULT_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def initialize_database_schema() -> None:
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_schema_sync()


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _apply_lightweight_schema_sync() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    organize_record_columns = {
        "organize_backend": "VARCHAR(16)",
        "strategy": "VARCHAR(64)",
        "library_type": "VARCHAR(32)",
        "root_path": "TEXT",
        "target_relative_path": "TEXT",
        "conflict_policy": "VARCHAR(32)",
        "capability_source": "VARCHAR(64)",
        "fallback_reason": "TEXT",
        "failure_reason": "TEXT",
        "verification_state": "VARCHAR(32)",
    }

    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        if "organize_records" not in tables:
            return

        existing_columns = {column["name"] for column in inspector.get_columns("organize_records")}
        for column_name, column_ddl in organize_record_columns.items():
            if column_name in existing_columns:
                continue
            connection.execute(text(f"ALTER TABLE organize_records ADD COLUMN {column_name} {column_ddl}"))
