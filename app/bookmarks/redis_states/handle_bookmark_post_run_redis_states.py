import os

from app.bookmarks.redis_states.file_copy_handlers.handle_copy_redis_dump_state_to_target_bm_redis_state import (
    handle_copy_redis_dump_state_to_target_bm_redis_state,
)
from app.bookmarks.redis_states.redis_state_handlers.handle_export_from_redis import (
    handle_export_from_redis,
)
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_bookmark_post_run_redis_states(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
) -> int:
    """
    This function is used to handle the Redis states for a bookmark after processing is run

    It will determine if it needs to save the redis_after state to redis_after.json+
    - Pull the redis state into temp
    - Determine if we need to save the redis_after state to the bookmark
    """

    ## INIT ##

    # Matched Bookmark
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    is_bm_match_redis_after_state_exist = os.path.exists(
        os.path.join(matched_bookmark_path_abs, "redis_after.json"))

    # Behavioral Flags
    is_save_updates = current_run_settings_obj["is_save_updates"]
    is_overwrite_bm_redis_after = current_run_settings_obj["is_overwrite_bm_redis_after"]
    is_no_saving_dry_run = current_run_settings_obj["is_no_saving_dry_run"]

    is_skip_redis_processing = current_run_settings_obj[
        "is_no_docker_no_redis"] or is_no_saving_dry_run

    ## SAVE REDIS STATE TO TEMP FILE ##

    if is_skip_redis_processing:
        print("Skipping all Redis operations (no Docker/Redis mode).")
        return 0

    # We never pull the redis-after state from another bookmark (atm), so always export from Redis unless dry run.
    # TODO(MFB): Figure our which of the two we should be using here.
    handle_export_from_redis(
        matched_bookmark_obj=matched_bookmark_obj,
        before_or_after="after"
    )

    # handle_export_from_redis_to_redis_dump(
    #     filename="bookmark_temp_after"
    # )

    ### SAVING TEMP TO BOOKMARK ###

    if is_bm_match_redis_after_state_exist and (not is_save_updates or not is_overwrite_bm_redis_after):
        # We do not want to save the temp file to the bookmark directory if it already exists,
        # unless we are in is_save_updates mode.
        return 0

    # Copy the temp file to the bookmark directory.
    handle_copy_redis_dump_state_to_target_bm_redis_state(
        target_bookmark_path_slash_abs=matched_bookmark_path_abs,
        target_bm_redis_state_before_or_after="before",
        redis_temp_state_filename="bookmark_temp"
    )

    return 0
