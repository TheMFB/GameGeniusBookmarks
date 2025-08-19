import json
import os

from app.bookmarks.auto_tags.process_auto_tags import process_auto_tags
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj


def safe_process_auto_tags(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings | None = None,
) -> None:
    """
    Loads redis_after.json and runs process_auto_tags.
    Handles missing files and logs any errors.
    """
    bookmark_dir_slash_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    redis_after_path = os.path.join(bookmark_dir_slash_abs, "redis_after.json")
    try:
        with open(redis_after_path, "r") as f:
            redis_after_data = json.load(f)
        process_auto_tags(
            redis_after_data=redis_after_data,
            matched_bookmark_obj=matched_bookmark_obj,
            current_run_settings_obj=current_run_settings_obj,
        )
    except FileNotFoundError:
        print(
            f"⚠️ No redis_after.json found for auto-tagging in {bookmark_dir_slash_abs}"
        )
    except Exception as e:
        print(f"⚠️ Auto-tagging failed: {e}")
