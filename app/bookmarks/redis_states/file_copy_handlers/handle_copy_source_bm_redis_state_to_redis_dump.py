import os
import shutil
from typing import Literal

from app.consts.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def handle_copy_source_bm_redis_state_to_redis_dump(
    origin_bm_redis_state_path: str,
    redis_temp_state_filename: Literal["bookmark_temp", "bookmark_temp_after"]
) -> int:
    """
    Handles moving the source bookmark's Redis state to the Redis dump directory.
    Returns: 0 if successful, 1 if error.
    """

    redis_temp_state_filename_json = redis_temp_state_filename + ".json"
    redis_dump_state_path_json = os.path.join(REDIS_DUMP_DIR, redis_temp_state_filename_json)

    # Make sure the source file exists
    if not os.path.exists(origin_bm_redis_state_path):
        print(
            f"❌ Bookmark Redis state file does not exist: {origin_bm_redis_state_path}")
        return 1

    if IS_DEBUG:
        print(
            f"💾 Saving {origin_bm_redis_state_path} to Redis Temp as {redis_temp_state_filename_json}...")

    # Move the source file to the dump directory
    shutil.copy(origin_bm_redis_state_path, redis_dump_state_path_json)
    if IS_DEBUG:
        print(
            f"💾 Saved the target final Redis state \n {origin_bm_redis_state_path} \n to dump directory: \n {redis_dump_state_path_json}")

    return 0
