import os
import subprocess
import shutil
from app.consts.bookmarks_consts import IS_DEBUG, IS_LOCAL_REDIS_DEV, REDIS_DUMP_DIR
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.decorators import print_def_name
from app.utils.printing_utils import *
from standalone_utils.redis.load_into_redis_local import load_into_redis_local

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_copy_bm_redis_before_to_redis_dump(
    matched_bookmark_obj: MatchedBookmarkObj,
):
    """
    This function is used to copy the redis_before.json to the redis dump directory.
    """
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    bm_redis_before_path = os.path.join(
        matched_bookmark_path_abs, "redis_before.json")

    if not os.path.exists(bm_redis_before_path):
        print(f"❌ redis_before.json does not exist at {bm_redis_before_path}")
        return False

    # os.makedirs(REDIS_DUMP_DIR, exist_ok=True)

    temp_redis_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp.json")

    # Copy the redis_before.json to the redis dump directory and load it
    shutil.copy2(bm_redis_before_path, temp_redis_path)
    if IS_DEBUG:
        print(f"📋 Copied Redis state to: {temp_redis_path}")
    return True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_load_redis_dump_into_redis():
    """
    This function is used to load the redis state from the redis dump directory into the redis database.
    """
    try:
        if IS_LOCAL_REDIS_DEV:
            return load_into_redis_local("bookmark_temp")

        else:
            # Docker mode
            cmd = "docker exec -it session_manager python -m utils.standalone.redis_load bookmark_temp"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                print(f"❌ Redis command failed: {cmd}")
                print(f"   Error: {result.stderr}")
                print(f"   Output: {result.stdout}")
                return False

            if IS_DEBUG:
                print(
                    f"✅ Redis command succeeded: {cmd}")
            return True

    except Exception as e:
        print(f"❌ Error running Redis command: {cmd}")
        print(f"   Exception: {e}")
        return False


@print_def_name(IS_PRINT_DEF_NAME)
def handle_load_into_redis(matched_bookmark_obj: MatchedBookmarkObj):
    """
    This function is used to load the redis state into the redis database.
    It first copies the redis_before.json to the redis dump directory and then loads it into the redis database.
    It then cleans up the temp file.
    """
    if not handle_copy_bm_redis_before_to_redis_dump(matched_bookmark_obj):
        return False
    if not handle_load_redis_dump_into_redis():
        return False

    # Clean up temp file
    temp_redis_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp.json")
    if os.path.exists(temp_redis_path):
        os.remove(temp_redis_path)
        if IS_DEBUG:
            print(f"🧹 Cleaned up temp file: {temp_redis_path}")
    return True

