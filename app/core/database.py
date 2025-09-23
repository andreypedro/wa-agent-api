"""Centralised storage helpers for Agno components."""

import os
from typing import Dict, Optional, Literal

from dotenv import load_dotenv

from agno.storage.base import Storage
from agno.storage.sqlite import SqliteStorage
from agno.storage.postgres import PostgresStorage

load_dotenv()

StorageMode = Literal["agent", "team", "workflow", "workflow_v2"]

_TABLE_NAMES: Dict[StorageMode, str] = {
    "agent": "agent_sessions",
    "team": "team_sessions",
    "workflow": "workflow_sessions",
    "workflow_v2": "workflow_sessions_v2",
}

_STORAGE_CACHE: Dict[str, Storage] = {}


def get_database_storage(mode: StorageMode = "workflow_v2") -> Optional[Storage]:
    """Return a cached storage instance configured for the requested mode."""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[DATABASE] No DATABASE_URL configured, using in-memory storage (history will be lost on restart)")
        return None

    table_name = _TABLE_NAMES.get(mode, "sessions")
    cache_key = f"{database_url}:{mode}:{table_name}"
    if cache_key in _STORAGE_CACHE:
        return _STORAGE_CACHE[cache_key]

    try:
        if database_url.startswith("sqlite"):
            db_path = database_url.replace("sqlite:///", "")
            print(f"[DATABASE] Using SQLite database: {db_path} ({table_name})")
            storage = SqliteStorage(
                table_name=table_name,
                db_file=db_path,
                mode=mode,
                auto_upgrade_schema=True,
            )
            storage.mode = mode
        elif database_url.startswith("postgresql"):
            print(f"[DATABASE] Using PostgreSQL database ({table_name})")
            storage = PostgresStorage(
                table_name=table_name,
                db_url=database_url,
                mode=mode,
                auto_upgrade_schema=True,
            )
            storage.mode = mode
        else:
            print(f"[DATABASE] Unsupported database URL format: {database_url}")
            print("[DATABASE] Supported formats: sqlite:///path/to/db.db or postgresql://user:pass@host:port/db")
            return None
    except Exception as exc:
        print(f"[DATABASE] Error initializing database storage: {exc}")
        print("[DATABASE] Falling back to in-memory storage")
        return None

    _STORAGE_CACHE[cache_key] = storage
    return storage


def get_workflow_storage() -> Optional[Storage]:
    """Shortcut for workflow_v2 storage configuration."""

    return get_database_storage(mode="workflow_v2")


def get_agent_storage() -> Optional[Storage]:
    """Shortcut for agent storage configuration."""

    return get_database_storage(mode="agent")


def get_session_storage() -> Optional[Storage]:
    """Alias kept for backwards compatibility with existing imports."""

    return get_workflow_storage()
