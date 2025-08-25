import json
from pathlib import Path
from typing import Any, Optional

from app.bookmarks.auto_tags.create_auto_tags import create_auto_tags
from app.consts.bookmarks_consts import IS_APPLY_AUTOTAGS, IS_DEBUG
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.data_utils import nest_flat_colon_keys


def process_auto_tags(
    redis_after_data: dict[str, Any],
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: Optional[CurrentRunSettings] = None,
) -> None:
    """
    Applies auto-tags to a matched bookmark and writes them to disk.
    Tags are generated via config and confirmed with user unless overridden.
    """
    if IS_DEBUG:
        print(f"🧩 redis_after_data top-level keys: {list(redis_after_data.keys())}")

    if not IS_APPLY_AUTOTAGS:
        if IS_DEBUG:
            print("⚠️ Skipping auto-tagging (IS_APPLY_AUTOTAGS is False).")
        return

    print("🔍 Processing auto-tags...")

    redis_after_data_nested = nest_flat_colon_keys(redis_after_data)
    auto_tags = create_auto_tags(redis_after_data_nested)

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
        # Handle user confirmation for applying auto-tags
        auto_tag_confirm_answer = (
            current_run_settings_obj.get("auto_tag_confirm_answer")
            if current_run_settings_obj
            else None
        )

        if auto_tag_confirm_answer == "no":
            print("⚠️ Auto-tagging skipped (auto_tag_confirm_answer='no').\n")
            return
        elif auto_tag_confirm_answer == "yes":
            pass
        else:
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
        bm_json.pop("auto_tags", None)
        bm_json.setdefault("bookmark_info", {})
        bm_json["bookmark_info"]["auto_tags"] = auto_tags
        with open(bookmark_path, "w") as f:
            json.dump(bm_json, f, indent=2)
        print(f"✅ Auto-tags written to {bookmark_path}")
    except Exception as e:
        print(f"⚠️ Could not write auto-tags: {e}")
