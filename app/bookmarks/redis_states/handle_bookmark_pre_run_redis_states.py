import os

from app.bookmarks.redis_states.file_copy_handlers.handle_copy_redis_dump_state_to_target_bm_redis_state import (
    handle_copy_redis_dump_state_to_target_bm_redis_state,
)
from app.bookmarks.redis_states.file_copy_handlers.handle_copy_source_bm_redis_state_to_redis_dump import (
    handle_copy_source_bm_redis_state_to_redis_dump,
)
from app.bookmarks.redis_states.handle_export_from_redis import (
    handle_export_from_redis_to_redis_dump,
)
from app.bookmarks.redis_states.handle_load_into_redis import (
    handle_load_redis_dump_into_redis,
)
from app.consts.bookmarks_consts import (
    INITIAL_REDIS_STATE_DIR,
)
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj


def handle_bookmark_pre_run_redis_states(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):
    """
    This function is used to handle the Redis states for a bookmark before starting the main process.

    All of these steps will have an intermediate step of saving the redis state to a temp file so that we can always revert if needed.

    # Cases:
    - Standard Create: We will pull from redis to save to the redis_before.json. We CAN reload that back into redis, but not necessary.

    - Standard Rerun: We will pull the redis_before.json from the bookmark directory and load it into redis.
    - Blank Slate: We will pull the initial_redis_before.json and load it into redis.
    - Use BM as Template: We will pull the redis_after.json from the alt source bookmark and save it to the redis_before.json. We will then load it into redis.
    - Use Last Used: We will pull the redis_after.json from the last used bookmark and save it to the redis_before.json. We will then load it into redis.

    # Changes to Flow :
    - Dry Run: No lasting changes will be made. It will still update Redis, but all redis state files will remain the same. NO code changes.
    - is_no_docker_no_redis: We will skip ALL redis operations, and proceed with updates and such that we can.
    - is_save_updates: We ignore the redis_before / redis_after states in our matched bookmark, and save any changes that happen.
    """
    # Matched Bookmark
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    is_bm_match_redis_before_state_exist = os.path.exists(os.path.join(matched_bookmark_path_abs, "redis_before.json"))

    # Alt Source Bookmark
    source_bookmark_obj = current_run_settings_obj.get("source_bookmark_obj", None)
    is_use_alt_source_bookmark = current_run_settings_obj.get("is_use_alt_source_bookmark", None)

    # Behavioral Flags
    is_save_updates = current_run_settings_obj["is_save_updates"]
    is_overwrite_bm_redis_before = current_run_settings_obj["is_overwrite_bm_redis_before"]
    is_no_saving_dry_run = current_run_settings_obj["is_no_saving_dry_run"]
    is_blank_slate = current_run_settings_obj["is_blank_slate"]

    is_skip_redis_processing = current_run_settings_obj[
        "is_no_docker_no_redis"] or is_no_saving_dry_run
    if is_skip_redis_processing:
        print("Skipping all Redis operations (no Docker/Redis mode).")
        return 0


    ## ALT SOURCE REDIS STATE PATH ##


    if is_blank_slate:
        # If we are using is_blank_slate, we are copying the initial_redis_before.json to the temp file.
        origin_bm_redis_state_path = os.path.join(
            INITIAL_REDIS_STATE_DIR, "initial_redis_before.json")

    elif is_use_alt_source_bookmark and source_bookmark_obj:
        # Note that if we are using is_use_alt_source_bookmark, we are copying the redis_after.json from the alt source bookmark to the temp file.
        origin_bm_redis_state_path = os.path.join(
            source_bookmark_obj["bookmark_path_slash_abs"], "redis_after.json")

    elif is_bm_match_redis_before_state_exist:
        # If we have an existing bookmark, we are copying the redis_before.json to the temp file.
        origin_bm_redis_state_path = os.path.join(matched_bookmark_path_abs, "redis_before.json")

    else:
        # If no redis_before.json exists for our bookmark, we are pulling from redis to the temp file.
        origin_bm_redis_state_path = 'redis'


    ## SAVE REDIS STATE TO TEMP FILE ##


    if origin_bm_redis_state_path == 'redis':
        # Pull from Redis to the temp file.
        handle_export_from_redis_to_redis_dump(
            before_or_after="before"
        )
    else:
        # Pull from the origin bookmark/initial state to the temp file.
        handle_copy_source_bm_redis_state_to_redis_dump(
            origin_bm_redis_state_path,
            redis_temp_state_filename="bookmark_temp"
        )


    ## #LOAD TEMP TO REDIS ###

    # For all cases other than is_skip_redis_processing, we will load the temp file into redis.
    handle_load_redis_dump_into_redis() # TODO(MFB): Should this be awaited?

    ### SAVING TEMP TO BOOKMARK ###

    if is_bm_match_redis_before_state_exist and not is_save_updates and not is_overwrite_bm_redis_before:
        # We do not want to save the temp file to the bookmark directory if it already exists,
        # unless we are in is_save_updates mode.
        pass

    # Copy the temp file to the bookmark directory.
    handle_copy_redis_dump_state_to_target_bm_redis_state(
        target_bookmark_path_slash_abs=matched_bookmark_path_abs,
        target_bm_redis_state_before_or_after="before",
        redis_temp_state_filename="bookmark_temp"
    )

    return 1

