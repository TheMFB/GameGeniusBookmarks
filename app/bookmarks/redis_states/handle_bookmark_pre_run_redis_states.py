import os

from app.bookmarks.redis_states.file_copy_handlers.handle_copy_redis_dump_state_to_target_bm_redis_state import (
    handle_copy_redis_dump_state_to_target_bm_redis_state,
)
from app.bookmarks.redis_states.file_copy_handlers.handle_copy_source_bm_redis_state_to_redis_dump import (
    handle_copy_source_bm_redis_state_to_redis_dump,
)
from app.bookmarks.redis_states.redis_state_handlers.handle_export_from_redis import (
    handle_export_from_redis,
)
from app.bookmarks.redis_states.redis_state_handlers.handle_load_dump_into_docker_redis import (
    handle_load_dump_into_docker_redis,
)
from app.bookmarks.redis_states.redis_state_handlers.handle_load_into_redis import handle_load_into_redis
from app.consts.bookmarks_consts import (
    INITIAL_REDIS_STATE_DIR,
)
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def determine_origin_bm_redis_state_path_from_context(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
) -> str:
    """
    This function is used to get the origin bookmark redis state path.
    """
    # Matched Bookmark
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    is_bm_match_redis_before_state_exist = os.path.exists(
        os.path.join(matched_bookmark_path_abs, "redis_before.json"))

    # Alt Source Bookmark
    source_bookmark_obj = current_run_settings_obj.get(
        "source_bookmark_obj", None)
    is_use_alt_source_bookmark = current_run_settings_obj.get(
        "is_use_alt_source_bookmark", None)

    # Behavioral Flags
    is_blank_slate = current_run_settings_obj["is_blank_slate"]

    # Blank Slate: copy the initial_redis_before.json to the temp file.
    if is_blank_slate:
        return os.path.join(INITIAL_REDIS_STATE_DIR, "initial_redis_before.json")

    # Alt Source: copy the redis_after.json from the alt source bookmark to the temp file.
    if is_use_alt_source_bookmark and source_bookmark_obj:
        return os.path.join(source_bookmark_obj["bookmark_path_slash_abs"], "redis_after.json")

    # Bookmark with existing redis_before.json: copy the redis_before.json to the temp file.
    if is_bm_match_redis_before_state_exist:
        return os.path.join(matched_bookmark_path_abs, "redis_before.json")

    # Else: Pull state directly from Redis.
    return 'redis'


@print_def_name(IS_PRINT_DEF_NAME)
def handle_bookmark_pre_run_redis_states(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
) -> int:
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

    ## INIT ##

    # Matched Bookmark
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    is_bm_match_redis_before_state_exist = os.path.exists(
        os.path.join(matched_bookmark_path_abs, "redis_before.json"))

    # Behavioral Flags
    is_save_updates = current_run_settings_obj["is_save_updates"]
    is_overwrite_bm_redis_before = current_run_settings_obj["is_overwrite_bm_redis_before"]
    is_no_saving_dry_run = current_run_settings_obj["is_no_saving_dry_run"]

    is_skip_redis_processing = current_run_settings_obj[
        "is_no_docker_no_redis"] or is_no_saving_dry_run
    if is_skip_redis_processing:
        print("Skipping all Redis operations (no Docker/Redis mode).")
        return 0

    # Alt Source: Determine the origin of the redis state.
    origin_bm_redis_state_path = determine_origin_bm_redis_state_path_from_context(
        matched_bookmark_obj, current_run_settings_obj)

    ## SAVE REDIS STATE TO TEMP FILE ##

    # Origin : Redis -> Export Redis state to the temp file.
    if origin_bm_redis_state_path == 'redis':
        result = handle_export_from_redis(
            before_or_after="before"
        )
        if result != 0:
            return result


    # Origin: bookmark/initial state -> Copy to the temp file.
    else:
        result = handle_copy_source_bm_redis_state_to_redis_dump(
            origin_bm_redis_state_path,
            redis_temp_state_filename="bookmark_temp"
        )
        if result != 0:
            return result

    ### LOAD TEMP TO REDIS ###

    # For all cases other than is_skip_redis_processing and when the state is already in redis, we will load the temp file into redis.
    if origin_bm_redis_state_path != 'redis':
        handle_load_into_redis(
            before_or_after="before"
        )

    ### SAVING TEMP TO BOOKMARK ###

    if is_bm_match_redis_before_state_exist and (not is_save_updates or not is_overwrite_bm_redis_before):
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
