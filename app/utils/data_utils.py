from typing import Any

from app.consts.bookmarks_consts import IS_DEBUG


def get_nested_value_from_colon_path(
    data: dict[str, Any], path: str
) -> str | bool | None:
    """
    Resolve a colon-delimited path like:
    "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:battle_timeline_phase"
    into a nested dictionary lookup.

    Returns:
        The resolved value if found, or None if any part is missing.
    """
    try:
        keys = path.split(":")
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        if isinstance(current, (str, bool)):
            return current
    except Exception as e:
        if IS_DEBUG:
            print(f"⚠️ Failed to resolve path '{path}': {e}")
        return None
