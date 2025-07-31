import os

from app.bookmarks.navigation.process_base_bookmark import process_base_bookmark
from app.bookmarks.redis_states.handle_bookmark_pre_run_redis_states import (
    handle_bookmark_pre_run_redis_states,
)
from app.obs.handle_bookmark_obs import (
    handle_bookmark_obs_pre_run,
)
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj


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

    obs_results = handle_bookmark_obs_pre_run(matched_bookmark_obj, current_run_settings_obj)
    if obs_results != 0:
        return obs_results

    return matched_bookmark_obj
