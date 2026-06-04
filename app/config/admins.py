"""
Admin access helpers.

Admin IDs are loaded from a local JSON file so private Telegram IDs do not
need to be hardcoded in the source code. The legacy ADMIN_ID environment
variable is still supported as a fallback.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
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


def _load_admin_ids_from_file(path: Path) -> set[int]:
    """
    Loads admin IDs from a JSON file without environment fallback.
    """
    if not path.exists():
        return set()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()

    raw_ids = data.get("admin_ids", []) if isinstance(data, dict) else data

    if not isinstance(raw_ids, list):
        return set()

    admin_ids: set[int] = set()

    for raw_id in raw_ids:
        admin_id = _parse_admin_id(raw_id)
        if admin_id is not None:
            admin_ids.add(admin_id)

    return admin_ids


@lru_cache(maxsize=8)
def _load_admin_ids_cached(path_value: str, environment_admin_id: int | None) -> frozenset[int]:
    """
    Loads admin IDs once per config path/environment value pair.
    """
    admin_ids = _load_admin_ids_from_file(Path(path_value))

    if environment_admin_id is not None:
        admin_ids.add(environment_admin_id)

    return frozenset(admin_ids)


def clear_admin_ids_cache() -> None:
    """
    Clears cached admin IDs.
    Useful for tests or after changing config/admins.json during runtime.
    """
    _load_admin_ids_cached.cache_clear()


def load_admin_ids(config_path: str | Path | None = None) -> set[int]:
    """
    Loads allowed admin Telegram IDs from config/admins.json.

    Supported JSON formats:
    - {"admin_ids": [123456789, "987654321"]}
    - [123456789, "987654321"]

    The default path is cached to avoid opening/parsing JSON on every message.
    """
    path = Path(config_path) if config_path else DEFAULT_ADMIN_CONFIG_PATH
    return set(_load_admin_ids_cached(str(path), settings.ADMIN_ID))


def is_admin_user(user_id: int | None) -> bool:
    """
    Checks whether a Telegram user has admin access.
    """
    if user_id is None:
        return False

    return user_id in load_admin_ids()
