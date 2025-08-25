from typing import Any

from app.bookmarks.auto_tags.auto_tag_config import AUTO_TAG_CONFIG
from app.consts.bookmarks_consts import IS_DEBUG
from app.utils.data_utils import get_nested_value_from_colon_path


def create_auto_tags(redis_after_data: dict[str, Any]) -> list[str]:
    """
    Converts redis_after_data into a list of auto-tags using config-driven rules.
    """
    tags: set[str] = set()

    for rule in AUTO_TAG_CONFIG:
        if IS_DEBUG:
            print("\n======================")
            print("🔍 Evaluating rule:")
            for k, v in rule.items():
                print(f"  {k}: {v}")

        if not rule.get("is_enabled", True):
            continue

        key_path = rule.get("key")
        if not key_path:
            if IS_DEBUG:
                print(f"⚠️ Skipping rule with missing 'key': {rule}")
            continue

        raw_value = get_nested_value_from_colon_path(redis_after_data, key_path)

        if IS_DEBUG:
            print(f"🔑 Rule: {key_path}")
            print(f"🔍 Resolved value: {raw_value}")

        if raw_value is None:
            undefined_tag = rule.get("undefined_string")
            if undefined_tag:
                tags.add(undefined_tag)
            elif IS_DEBUG:
                print(f"⚠️ Key not found: {key_path}")
            continue

        if isinstance(raw_value, bool):
            if raw_value:
                true_tag = rule.get("true_string")
                if true_tag:
                    tags.add(true_tag)
            else:
                false_tag = rule.get("false_string")
                if false_tag:
                    tags.add(false_tag)

        if not isinstance(raw_value, str):
            continue  # Skip unsupported types for now

        tag: str = raw_value

        prepend = rule.get("prepend_string")
        append = rule.get("append_string")

        if prepend:
            tag = prepend + tag
        if append:
            tag = tag + append

        tags.add(tag)

    return sorted(tags)
