import json
from pathlib import Path
from typing import Any, Optional

from app.bookmarks.auto_tags.create_auto_tags import create_auto_tags
from app.consts.bookmarks_consts import IS_APPLY_AUTOTAGS
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

    # Now extract the screen_statuses.current_screen_name safely
    screen_statuses = game_state_data.get("screen_statuses", {})
    map_battle_mode_statuses = game_state_data.get("map_battle_mode_statuses", {})

    auto_tags = create_auto_tags(
        current_screen_name=screen_statuses.get("current_screen_name"),
        team_objective_control_state=map_battle_mode_statuses.get(
            "team_objective_control_state"
        ),
        battle_timeline_phase=map_battle_mode_statuses.get("battle_timeline_phase"),
        team_attack_or_defend=map_battle_mode_statuses.get("team_attack_or_defend"),
        game_mode_name=map_battle_mode_statuses.get("game_mode_name"),
        map_battle_mode_name=map_battle_mode_statuses.get("map_battle_mode_name"),
        stage_name=map_battle_mode_statuses.get("stage_name"),
        stage_location_name=map_battle_mode_statuses.get("stage_location_name"),
        final_victory_or_defeat=map_battle_mode_statuses.get("final_victory_or_defeat"),
    )

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
