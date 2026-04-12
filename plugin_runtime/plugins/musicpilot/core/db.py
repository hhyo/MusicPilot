"""Database primitives for the simplified MusicPilot runtime."""

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


def rebuild_sqlite_database() -> None:
    if not settings.database_url.startswith("sqlite"):
        raise RuntimeError("Database rebuild is only supported for SQLite.")

    engine.dispose()
    for path in [
        DEFAULT_DATABASE_PATH,
        DEFAULT_DATABASE_PATH.with_suffix(f"{DEFAULT_DATABASE_PATH.suffix}-wal"),
        DEFAULT_DATABASE_PATH.with_suffix(f"{DEFAULT_DATABASE_PATH.suffix}-shm"),
    ]:
        if path.exists():
            path.unlink()


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _apply_lightweight_schema_sync() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    table_columns = {
        "search_jobs": {
            "music_recognition_assessment": "JSON",
        },
        "subscriptions": {
            "music_media_input": "JSON",
            "music_meta_base": "JSON",
            "music_recognition_assessment": "JSON",
            "music_media_info": "JSON",
        },
        "subscription_runs": {
            "music_media_input": "JSON",
            "music_meta_base": "JSON",
            "music_recognition_assessment": "JSON",
            "music_media_info": "JSON",
        },
        "organize_records": {
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
            "music_media_input": "JSON",
            "music_meta_base": "JSON",
            "music_recognition_assessment": "JSON",
            "music_media_info": "JSON",
        },
    }

    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        for table_name, column_map in table_columns.items():
            if table_name not in tables:
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_ddl in column_map.items():
                if column_name in existing_columns:
                    continue
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_ddl}"))
