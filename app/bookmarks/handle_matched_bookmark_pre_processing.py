from app.utils.obs_utils import load_bookmark_into_obs
from app.types.bookmark_types import MatchedBookmarkObj, CurrentRunSettings
from app.utils.printing_utils import *
from app.bookmarks.redis_states.handle_bookmark_pre_run_redis_states import handle_bookmark_pre_run_redis_states
from app.obs.handle_bookmark_obs import save_obs_screenshot_to_bookmark_path, save_obs_media_info_to_bookmark_meta
from app.bookmarks.navigation.process_base_bookmark import process_base_bookmark

def handle_matched_bookmark_pre_processing(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):
    """
    This function is used to handle the pre-processing of a matched bookmark.

    It will handle the following:
    - Load the Redis state into redis
    - Load the OBS bookmark into OBS
    """
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]

    # SANITY CHECK

    if not matched_bookmark_path_abs or not os.path.exists(matched_bookmark_path_abs):
        print(f"❌ Bookmark Path does not exist: '{matched_bookmark_path_abs}'")
        return 1

    # NAV BASE BOOKMARK
    process_base_bookmark(matched_bookmark_obj, current_run_settings_obj)

    # REDIS STATES

    handle_bookmark_pre_run_redis_states(matched_bookmark_obj, current_run_settings_obj)

    # OBS

    if current_run_settings_obj["is_no_obs"]:
        print("📷 No-OBS mode: Skipping screenshot capture and metadata update")
    else:
        # Load the OBS bookmark using the matched name
        is_obs_loaded = load_bookmark_into_obs(matched_bookmark_obj)
        if not is_obs_loaded:
            print("❌ Failed to load OBS bookmark")
            return 1

        # Save screenshot and metadata
        save_obs_screenshot_to_bookmark_path(matched_bookmark_obj, current_run_settings_obj)
        save_obs_media_info_to_bookmark_meta(matched_bookmark_obj, current_run_settings_obj)

    return matched_bookmark_obj
