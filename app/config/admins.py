"""
Admin access helpers.

Admin IDs are loaded from a local JSON file so private Telegram IDs do not
need to be hardcoded in the source code. The legacy ADMIN_ID environment
variable is still supported as a fallback.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.config.settings import settings

DEFAULT_ADMIN_CONFIG_PATH = Path(os.getenv("ADMIN_CONFIG_PATH", "config/admins.json"))


def _parse_admin_id(value: Any) -> int | None:
    """
    Safely parses Telegram admin IDs from JSON values.
    """
    if isinstance(value, bool):
        return None

    try:
        admin_id = int(str(value).strip())
    except (TypeError, ValueError):
        return None

    return admin_id if admin_id > 0 else None


def load_admin_ids(config_path: str | Path | None = None) -> set[int]:
    """
    Loads allowed admin Telegram IDs from config/admins.json.

    Supported JSON formats:
    - {"admin_ids": [123456789, "987654321"]}
    - [123456789, "987654321"]
    """
    admin_ids: set[int] = set()

    if settings.ADMIN_ID is not None:
        admin_ids.add(settings.ADMIN_ID)

    path = Path(config_path) if config_path else DEFAULT_ADMIN_CONFIG_PATH

    if not path.exists():
        return admin_ids

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return admin_ids

    raw_ids = data.get("admin_ids", []) if isinstance(data, dict) else data

    if not isinstance(raw_ids, list):
        return admin_ids

    for raw_id in raw_ids:
        admin_id = _parse_admin_id(raw_id)
        if admin_id is not None:
            admin_ids.add(admin_id)

    return admin_ids


def is_admin_user(user_id: int | None) -> bool:
    """
    Checks whether a Telegram user has admin access.
    """
    if user_id is None:
        return False

    return user_id in load_admin_ids()
