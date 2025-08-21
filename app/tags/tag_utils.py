from typing import Any

from app.consts.bookmarks_consts import ACTIVE_TAG_TYPE


def get_effective_tags(bookmark_json: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    bookmark_info = bookmark_json.get("bookmark_info", {})

    if ACTIVE_TAG_TYPE in ("user_tags", "both"):
        tags += bookmark_info.get("tags", [])
        tags += bookmark_json.get("tags", [])

    if ACTIVE_TAG_TYPE in ("auto_tags", "both"):
        tags += bookmark_info.get("auto_tags", [])

    seen: set[str] = set()
    return [tag for tag in tags if tag not in seen and not seen.add(tag)]
