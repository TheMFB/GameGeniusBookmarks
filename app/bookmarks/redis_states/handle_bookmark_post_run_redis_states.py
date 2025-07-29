import os
import subprocess
import shutil
from app.bookmarks.redis_states.bookmarks_redis import run_redis_command, copy_blank_redis_state_to_bm_redis_before
# copy_preceding_bookmark_redis_state, copy_specific_bookmark_redis_state
from app.consts.bookmarks_consts import IS_DEBUG, IS_LOCAL_REDIS_DEV, REDIS_DUMP_DIR
from app.types.bookmark_types import MatchedBookmarkObj, CurrentRunSettings
from app.utils.printing_utils import *

def handle_bookmark_post_run_redis_states(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):
    """
    This function is used to handle the Redis states for a bookmark after processing is run

    It will determine if it needs to save the redis_after state to redis_after.json+
    - Pull the redis state into temp
    - Determine if we need to save the redis_after state to the bookmark


    """
    matched_bookmark_path_rel = matched_bookmark_obj["bookmark_path_slash_rel"]
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]

    is_overwrite_bm_redis_after = current_run_settings_obj["is_save_updates"] # Will overwrite existing redis_before.json
    is_skip_redis_processing = current_run_settings_obj["is_no_docker_no_redis"]

    bm_redis_after_path = os.path.join(matched_bookmark_path_abs, "redis_after.json")



    if is_overwrite_bm_redis_after:
        if os.path.exists(bm_redis_after_path):
            print(f"💾 Saving redis_after state to {bm_redis_after_path}")
        else:
            print(f"❌ redis_after.json does not exist at {bm_redis_after_path}")

    pass