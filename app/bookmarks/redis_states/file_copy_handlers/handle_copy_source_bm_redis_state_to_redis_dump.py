import os
import shutil
from typing import Literal

from app.consts.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def handle_copy_bookmark_redis_state_to_redis_dump(
    source_bookmark_obj: MatchedBookmarkObj,
    bm_redis_state_type: Literal["before", "after"],
    redis_temp_state_filename: Literal["bookmark_temp", "bookmark_temp_after"]
):
    """
    Handles saving the final Redis state (bookmark_temp or bookmark_temp_after) to redis_after.json or redis_before.json
    Returns: True if redis_after was saved, False otherwise
    """
    bookmark_path_slash_abs = source_bookmark_obj["bookmark_path_slash_abs"]

    bookmark_redis_state_filename = "redis_" + bm_redis_state_type + ".json"
    bookmark_redis_state_path = os.path.join(bookmark_path_slash_abs, bookmark_redis_state_filename)

    redis_temp_state_filename_json = redis_temp_state_filename + ".json"
    redis_dump_state_path = os.path.join(REDIS_DUMP_DIR, redis_temp_state_filename)

    # Make sure the source file exists
    if not os.path.exists(bookmark_redis_state_path):
        print(f"❌ Bookmark Redis state file does not exist: {bookmark_redis_state_path}")
        return False


    if IS_DEBUG:
        print(
            f"💾 Saving {bookmark_redis_state_path} to Redis Temp as {redis_temp_state_filename_json}...")

    # if not run_redis_command('export', 'bookmark_temp_after'):
    #     print("❌ Failed to export final Redis state")
    #     return False

    # Move the final Redis export to the bookmark directory
    shutil.move(redis_dump_state_path, bookmark_redis_state_path)
    if IS_DEBUG:
        print(f"💾 Saved final Redis state to: {bookmark_redis_state_path}")


    return False
