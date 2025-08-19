import json
from pathlib import Path
from typing import Any, Optional

from app.bookmarks.auto_tags.create_auto_tags import create_auto_tags
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj


def process_auto_tags(
    redis_after_data: dict[str, Any],
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: Optional[CurrentRunSettings] = None,
) -> None:
    """
    Pulls values from redis_after_data and applies them as auto-tags to the matched bookmark.
    """
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
    map_battle_mode_statuses = game_state_data.get(
        "map_battle_mode_statuses", {}
    )  # <-- THIS LINE!

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
    matched_bookmark_obj["auto_tags"] = auto_tags

    # Save back to disk (overwrite the bookmark file)
    bookmark_path = (
        Path(matched_bookmark_obj["bookmark_path_slash_abs"]) / "bookmark_meta.json"
    )
    try:
        with open(bookmark_path, "r") as f:
            bm_json = json.load(f)
        # Update top-level auto_tags
        bm_json["auto_tags"] = auto_tags
        with open(bookmark_path, "w") as f:
            json.dump(bm_json, f, indent=2)
        print(f"✅ Auto-tags written to {bookmark_path}")
    except Exception as e:
        print(f"⚠️ Could not write auto-tags: {e}")
