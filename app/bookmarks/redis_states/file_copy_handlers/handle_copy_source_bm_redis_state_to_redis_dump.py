import os
import shutil
from typing import Literal

from app.consts.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def handle_copy_source_bm_redis_state_to_redis_dump(
    source_bookmark_path_slash_abs: str,
    redis_temp_state_filename: Literal["bookmark_temp", "bookmark_temp_after"]
):
    """
    Handles saving the final Redis state (bookmark_temp or bookmark_temp_after) to redis_after.json or redis_before.json
    Returns: True if redis_after was saved, False otherwise
    """

    redis_temp_state_filename_json = redis_temp_state_filename + ".json"
    redis_dump_state_path = os.path.join(REDIS_DUMP_DIR, redis_temp_state_filename)

    # Make sure the source file exists
    if not os.path.exists(source_bookmark_path_slash_abs):
        print(
            f"❌ Bookmark Redis state file does not exist: {source_bookmark_path_slash_abs}")
        return False


    if IS_DEBUG:
        print(
            f"💾 Saving {source_bookmark_path_slash_abs} to Redis Temp as {redis_temp_state_filename_json}...")

    # if not run_redis_command('export', 'bookmark_temp_after'):
    #     print("❌ Failed to export final Redis state")
    #     return False

    # Move the final Redis export to the bookmark directory
    shutil.move(redis_dump_state_path, source_bookmark_path_slash_abs)
    if IS_DEBUG:
        print(
            f"💾 Saved final Redis state to: {source_bookmark_path_slash_abs}")


    return False
