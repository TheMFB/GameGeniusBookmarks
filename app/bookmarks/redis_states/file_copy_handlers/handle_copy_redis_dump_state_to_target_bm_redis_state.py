import os
import shutil
from typing import Literal

from app.bookmarks.redis_states.redis_friendly_converter import (
    convert_redis_state_file_to_friendly_and_save,
)
from app.consts.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR
from app.utils.decorators import print_def_name
from app.utils.printing_utils import print_dev

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)

def handle_copy_redis_dump_state_to_target_bm_redis_state(
    target_bookmark_path_slash_abs: str,
    target_bm_redis_state_before_or_after: Literal["before", "after"],
    redis_temp_state_filename: Literal["bookmark_temp", "bookmark_temp_after"],
) -> int:
    """
    Handles saving the final Redis state (bookmark_temp or bookmark_temp_after) to redis_after.json or redis_before.json
    Returns: True if redis_after was saved, False otherwise
    """

    # Redis dump state
    redis_temp_state_filename_json = redis_temp_state_filename + ".json"
    redis_dump_state_filepath = os.path.join(
        REDIS_DUMP_DIR, redis_temp_state_filename_json)

    # Make sure the source file exists
    if not os.path.exists(redis_dump_state_filepath):
        print(
            f"❌ Redis dump state file does not exist: {redis_dump_state_filepath}")
        return 1

    # Target bookmark redis state
    target_bm_redis_state_filename_json = f"redis_{target_bm_redis_state_before_or_after}.json"
    target_bm_redis_state_filepath = os.path.join(
        target_bookmark_path_slash_abs, target_bm_redis_state_filename_json)

    if IS_DEBUG:
        print(
            f"💾 Saving Redis dump state:\n{redis_dump_state_filepath}\nto target bookmark:\n{target_bm_redis_state_filepath}...")

    # Move the final Redis export to the bookmark directory
    shutil.move(redis_dump_state_filepath, target_bm_redis_state_filepath)
    if IS_DEBUG:
        print(
            f"💾 Saved final Redis state to: {target_bm_redis_state_filepath}")

    print_dev(
        '---- convert_redis_state_file_to_friendly_and_save target_bm_redis_state_filepath:', 'magenta')
    print_dev(target_bm_redis_state_filepath)

    # Convert to friendly
    results = convert_redis_state_file_to_friendly_and_save(
        target_bm_redis_state_filepath)
    if results == 1:
        return 1

    return 0
