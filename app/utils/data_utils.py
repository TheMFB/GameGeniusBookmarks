from typing import Any, cast


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
    keys = path.split(":")
    current = data

    for i, key in enumerate(keys):
        if isinstance(current, dict):
            if key == "*":
                for subkey in current:
                    result = get_nested_value_from_colon_path(
                        cast(dict[str, Any], current[subkey]),
                        ":".join(keys[i + 1 :]),
                    )
                    if result is not None:
                        return result
                return None
            elif key in current:
                current = current[key]
            else:
                return None
        else:
            return None
    if isinstance(current, (str, bool)):
        return current

    return None


def nest_flat_colon_keys(flat_dict: dict[str, Any]) -> dict[str, Any]:
    nested = {}
    for full_key, value in flat_dict.items():
        parts = full_key.split(":")
        current = nested
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    return nested
