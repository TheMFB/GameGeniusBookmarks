import os
from typing import Literal

from app.bookmarks.redis_states.redis_friendly_converter import (
    convert_redis_state_file_to_friendly_and_save,
)
from app.bookmarks.redis_states.redis_state_handlers.handle_export_docker_redis_to_dump import (
    handle_export_docker_redis_to_redis_dump,
)
from app.bookmarks.redis_states.redis_state_handlers.handle_export_local_redis_to_dump import (
    handle_export_local_redis_to_dump,
)
from app.bookmarks.redis_states.redis_state_utils import get_temp_redis_state_name
from app.consts.bookmarks_consts import IS_DEBUG, IS_LOCAL_REDIS_DEV, REDIS_DUMP_DIR
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_export_from_redis(
    matched_bookmark_obj: MatchedBookmarkObj,
    before_or_after: Literal["before", "after"] = "after"
) -> int:
    """
    This function is used to load the redis state into the redis database.
    It first copies the redis_before.json to the redis dump directory and then loads it into the redis database.
    It then cleans up the temp file.
    """
    # Export from redis to redis dump
    if IS_LOCAL_REDIS_DEV:
        results =  handle_export_local_redis_to_dump(before_or_after)
        if results == 1:
            return 1
    else:
        results = handle_export_docker_redis_to_redis_dump(before_or_after)
        if results == 1:
            return 1

    # # Copy from redis dump to bookmark directory
    # if not handle_copy_redis_state_dump_to_bm_redis_state(matched_bookmark_obj, before_or_after):
    #     return False

    # Convert to friendly
    bm_redis_state_name = f"redis_{before_or_after}.json"
    bm_redis_state_path = os.path.join(
        matched_bookmark_obj["bookmark_path_slash_abs"], bm_redis_state_name)
    results = convert_redis_state_file_to_friendly_and_save(bm_redis_state_path)
    if results == 1:
        return 1

    # Clean up temp file
    temp_redis_state_name = get_temp_redis_state_name(before_or_after)
    temp_redis_path = os.path.join(REDIS_DUMP_DIR, temp_redis_state_name)
    if os.path.exists(temp_redis_path):
        os.remove(temp_redis_path)
        if IS_DEBUG:
            print(f"🧹 Cleaned up temp file: {temp_redis_path}")

    return 0
