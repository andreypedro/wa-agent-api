"""Centralised storage helpers for Agno components."""

import os
from typing import Dict, Literal, Optional

from dotenv import load_dotenv

# Storage modules not available in current agno version
# Using simple in-memory storage approach
print("[DATABASE] Using in-memory storage (no persistence between restarts)")

load_dotenv()

StorageMode = Literal["agent", "team", "workflow", "workflow_v2"]

_TABLE_NAMES: Dict[StorageMode, str] = {
    "agent": "agent_sessions",
    "team": "team_sessions",
    "workflow": "workflow_sessions",
    "workflow_v2": "workflow_sessions_v2",
}

# Simple in-memory storage cache (not used since storage is unavailable)
_STORAGE_CACHE: Dict[str, any] = {}


def get_database_storage(mode: StorageMode = "workflow_v2"):
    """Return None since storage modules are not available in current agno version."""
    return None


def get_workflow_storage():
    """Return None since storage is not available."""
    return None


def get_agent_storage():
    """Return None since storage is not available."""
    return None


def get_session_storage():
    """Alias kept for backwards compatibility with existing imports."""
    return get_workflow_storage()
