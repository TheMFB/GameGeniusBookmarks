import json
from pathlib import Path
from typing import Any, Optional

from app.bookmarks.auto_tags.auto_tag_config import AUTO_TAG_CONFIG
from app.consts.bookmarks_consts import IS_APPLY_AUTOTAGS, IS_DEBUG
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj


def process_auto_tags(
    redis_after_data: dict[str, Any],
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: Optional[CurrentRunSettings] = None,
) -> None:
    """
    Pulls values from redis_after_data and applies them as auto-tags to the matched bookmark.
    """
    if not IS_APPLY_AUTOTAGS:
        if IS_DEBUG:
            print("⚠️ Skipping auto-tagging (IS_APPLY_AUTOTAGS is False).")
        return

    print("🔍 Processing auto-tags...")

    # Find the game_state entry dynamically
    game_state_data = None
    for key, value in redis_after_data.items():
        if key.endswith(":game_state"):
            game_state_data = value
            break

    if not game_state_data:
        print("❌ Could not find :game_state in redis_after_data")
        return

    auto_tags: list[str] = []

    for rule in AUTO_TAG_CONFIG:
        if not rule.get("is_enabled", True):
            continue

        relative_key_path = rule.get("key", "").split(":game_state:")[-1]
        raw_value = extract_value_by_key_path(game_state_data, relative_key_path)

        # Handle None
        if raw_value is None:
            tag = rule.get("undefined_string")
            if tag:
                auto_tags.append(tag)
            continue

        # Convert booleans
        if isinstance(raw_value, bool):
            true_string = rule.get("true_string")
            false_string = rule.get("false_string")

            if raw_value and true_string:
                tag = true_string
            elif not raw_value and false_string:
                tag = false_string
            else:
                continue
        else:
            tag = str(raw_value)

        if IS_DEBUG:
            print(f"✔️ Rule matched: key={rule.get('key')} → tag={tag}")

        auto_tags.append(tag)

    print("🏷️ Generated auto-tags:", auto_tags)

    # Attach auto_tags to the bookmark's info
    if "bookmark_info" not in matched_bookmark_obj:
        matched_bookmark_obj["bookmark_info"] = {
            "bookmark_tail_name": matched_bookmark_obj.get("bookmark_tail_name", ""),
            "video_filename": "",
            "timestamp": 0.0,
            "timestamp_formatted": "",
            "tags": [],
            "auto_tags": auto_tags,
            "created_at": "",
        }
    else:
        matched_bookmark_obj["bookmark_info"]["auto_tags"] = auto_tags

    # Save back to disk (overwrite the bookmark file)
    bookmark_path = (
        Path(matched_bookmark_obj["bookmark_path_slash_abs"]) / "bookmark_meta.json"
    )
    try:
        # Check if we should skip confirmation
        is_skip_auto_tag_confirmation = (
            current_run_settings_obj.get("is_skip_auto_tag_confirmation", False)
            if current_run_settings_obj
            else False
        )

        if not is_skip_auto_tag_confirmation:
            # Try to load current auto-tags from disk (if present)
            try:
                with open(bookmark_path, "r") as f:
                    existing_data = json.load(f)
                    old_tags = (
                        existing_data.get("bookmark_info", {}).get("auto_tags", [])
                        if "bookmark_info" in existing_data
                        else []
                    )
            except Exception:
                old_tags: list[str] = []

            if old_tags != auto_tags:
                print("\n📋 Proposed Auto-Tag Update:")
                print("Old tags:", old_tags)
                print("New tags:", auto_tags)
                while True:
                    user_input = (
                        input("\nApply these auto-tags? (y/n): ").strip().lower()
                    )
                    if user_input == "y":
                        break
                    elif user_input == "n":
                        print("⚠️ Auto-tagging canceled by user.\n")
                        return
                    else:
                        print("❌ Invalid input. Please enter 'y' or 'n'.")

        with open(bookmark_path, "r") as f:
            bm_json = json.load(f)
        # Update top-level auto_tags
        if "auto_tags" in bm_json:
            # Old-style top-level auto_tags, remove it
            del bm_json["auto_tags"]
        if "bookmark_info" not in bm_json:
            bm_json["bookmark_info"] = {
                "bookmark_tail_name": bm_json.get("bookmark_tail_name", ""),
                "video_filename": bm_json.get("video_filename", ""),
                "timestamp": bm_json.get("timestamp", 0.0),
                "timestamp_formatted": bm_json.get("timestamp_formatted", ""),
                "tags": bm_json.get("tags", []),
                "auto_tags": auto_tags,
                "created_at": bm_json.get("created_at", ""),
            }
        else:
            bm_json["bookmark_info"]["auto_tags"] = auto_tags
        with open(bookmark_path, "w") as f:
            json.dump(bm_json, f, indent=2)
        print(f"✅ Auto-tags written to {bookmark_path}")
    except Exception as e:
        print(f"⚠️ Could not write auto-tags: {e}")


def extract_value_by_key_path(data: dict[str, Any], key_path: str) -> Any:
    keys = key_path.split(":")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current
