import os

from app.bookmarks.auto_tags.auto_tags_utils import safe_process_auto_tags
from app.bookmarks.navigation.process_alt_source_bookmark import (
    process_alt_source_bookmark,
)
from app.bookmarks.redis_states.handle_bookmark_pre_run_redis_states import (
    handle_bookmark_pre_run_redis_states,
)
from app.obs.handle_bookmark_obs import (
    handle_bookmark_obs_pre_run,
)
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_matched_bookmark_pre_processing(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
) -> int:
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

    # RESOLVE SOURCE BOOKMARK

    is_use_alt_source_bookmark = current_run_settings_obj.get(
        "is_use_alt_source_bookmark", False
    )
    if is_use_alt_source_bookmark:
        alt_source_bookmark_results = process_alt_source_bookmark(
            matched_bookmark_obj, current_run_settings_obj
        )
        if isinstance(alt_source_bookmark_results, int):
            print("❌ No source bookmark found")
            return alt_source_bookmark_results
        current_run_settings_obj = alt_source_bookmark_results

    # REDIS STATES

    results = handle_bookmark_pre_run_redis_states(
        matched_bookmark_obj, current_run_settings_obj
    )
    if results != 0:
        print("❌ Error in handle_bookmark_pre_run_redis_states")
        return results

    safe_process_auto_tags(
        matched_bookmark_obj,
        current_run_settings_obj=current_run_settings_obj,
    )

    # OBS

    return handle_bookmark_obs_pre_run(matched_bookmark_obj, current_run_settings_obj)
