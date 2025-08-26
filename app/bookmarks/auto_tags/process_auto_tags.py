import json
from pathlib import Path
from typing import Any, Optional

from app.bookmarks.auto_tags.create_auto_tags import create_auto_tags
from app.consts.bookmarks_consts import IS_APPLY_AUTOTAGS, IS_DEBUG
from app.types.bookmark_types import (
    BookmarkInfo,
    CurrentRunSettings,
    MatchedBookmarkObj,
)
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
    tags_by_hierarchy = create_auto_tags(redis_after_data_nested)
    auto_tags = tags_by_hierarchy.get("t1", [])

    # Attach t2/t3 tags to parent/grandparent bookmark_info
    if current_run_settings_obj:
        current_bm = current_run_settings_obj.get("current_bookmark_obj")
        if current_bm:
            if "bookmark_info" not in current_bm:
                current_bm["bookmark_info"] = {
                    "bookmark_tail_name": current_bm.get("bookmark_tail_name", ""),
                    "video_filename": "",
                    "timestamp": 0.0,
                    "timestamp_formatted": "",
                    "tags": [],
                    "auto_tags": [],
                    "created_at": "",
                }

            bm_info: BookmarkInfo = current_bm["bookmark_info"]

            # Apply t1 to current bookmark (in memory)
            if "t1" in tags_by_hierarchy:
                bm_info["auto_tags"] = tags_by_hierarchy["t1"]

            # Apply t2 and t3 to parent/grandparent (in memory)
            if "t2" in tags_by_hierarchy:
                bm_info["auto_tags_t2"] = tags_by_hierarchy["t2"]
            if "t3" in tags_by_hierarchy:
                bm_info["auto_tags_t3"] = tags_by_hierarchy["t3"]

    if IS_DEBUG:
        print("🏷️ All generated tags by hierarchy:", tags_by_hierarchy)
        print("🏷️ Selected auto-tags for current bookmark (t1):", auto_tags)

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

    matched_path = Path(matched_bookmark_obj["bookmark_path_slash_abs"])
    parent_path = matched_path.parent if matched_path.parent != matched_path else None
    grandparent_path = (
        parent_path.parent
        if parent_path and parent_path.parent != parent_path
        else None
    )

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

        bm_json.pop("auto_tags", None)  # Clean up old format

        bookmark_info = bm_json.setdefault("bookmark_info", {})

        # Clean up any previously existing tiered tags
        bookmark_info.pop("auto_tags_t2", None)
        bookmark_info.pop("auto_tags_t3", None)

        # Write current tags
        bookmark_info["auto_tags"] = auto_tags

        if "t2" in tags_by_hierarchy:
            bookmark_info["auto_tags_t2"] = tags_by_hierarchy["t2"]

        if "t3" in tags_by_hierarchy:
            bookmark_info["auto_tags_t3"] = tags_by_hierarchy["t3"]

        with open(bookmark_path, "w") as f:
            json.dump(bm_json, f, indent=2)
        print(f"✅ Auto-tags written to {bookmark_path}")

        # --- Handle auto_tags_t2 and auto_tags_t3 ---
        for path_obj, tag_key in [
            (parent_path, "auto_tags_t2"),
            (grandparent_path, "auto_tags_t3"),
        ]:
            if path_obj and tag_key in tags_by_hierarchy:
                meta_path = path_obj / "bookmark_meta.json"
                try:
                    with open(meta_path, "r") as f:
                        parent_meta = json.load(f)
                except FileNotFoundError:
                    parent_meta = {}

                parent_bm_info = parent_meta.setdefault("bookmark_info", {})

                hierarchy_level = tag_key[-2:]  # extracts "t2" or "t3"
                parent_bm_info[tag_key] = tags_by_hierarchy[hierarchy_level]

                try:
                    with open(meta_path, "w") as f:
                        json.dump(parent_meta, f, indent=2)
                    print(f"✅ {tag_key} written to {meta_path}")
                except Exception as e:
                    print(f"⚠️ Failed to write {tag_key} to {meta_path}: {e}")

    except Exception as e:
        print(f"⚠️ Could not write auto-tags: {e}")
