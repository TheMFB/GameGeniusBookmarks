import os
import subprocess
import shutil
from app.bookmarks.redis_states.redis_friendly_converter import convert_redis_state_file_to_friendly_and_save
from app.consts.bookmarks_consts import IS_DEBUG, IS_LOCAL_REDIS_DEV, REDIS_DUMP_DIR
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.decorators import print_def_name
from app.utils.printing_utils import *
from standalone_utils.redis.load_into_redis_local import load_into_redis_local

IS_PRINT_DEF_NAME = True

def get_temp_redis_state_name(before_or_after: Literal["before", "after"]) -> str:
    return f"bookmark_temp{'_after' if before_or_after == 'after' else ''}"

# TODO(MFB): Does this need separate params for the dump and the bookmark?
@print_def_name(IS_PRINT_DEF_NAME)
def handle_copy_redis_state_dump_to_bm_redis_state(
    matched_bookmark_obj: MatchedBookmarkObj,
    before_or_after: Literal["before", "after"]
):
    """
    This function is used to copy a redis state from the redis dump directory to the bookmark directory.
    (bookmark_temp -> redis_before.json)
    (bookmark_temp_after -> redis_after.json)
    """
    bm_redis_state_name = f"redis_{before_or_after}.json"
    temp_redis_state_name = get_temp_redis_state_name(before_or_after)


    bm_redis_state_path = os.path.join(
        matched_bookmark_obj["bookmark_path_slash_abs"], bm_redis_state_name)

    temp_redis_path = os.path.join(REDIS_DUMP_DIR, temp_redis_state_name)
    if not os.path.exists(temp_redis_path):
        print(f"❌ {temp_redis_state_name} does not exist at {temp_redis_path}")
        return False

    # Copy the redis_after.json to the bookmark directory
    shutil.copy2(temp_redis_path, bm_redis_state_path)
    if IS_DEBUG:
        print(f"📋 Copied Redis state to: {bm_redis_state_path}")
    return True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_export_from_redis_to_redis_dump(
    before_or_after: Literal["before", "after"]
):
    """
    This function is used to export the redis state from the redis database to the redis dump directory.
    """
    temp_redis_state_name = get_temp_redis_state_name(before_or_after)

    try:
        if IS_LOCAL_REDIS_DEV:
            return load_into_redis_local(temp_redis_state_name)

        else:
            # Docker mode
            cmd = f"docker exec -it session_manager python -m utils.standalone.redis_load {temp_redis_state_name}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, check=False)

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
def handle_export_from_redis(
    matched_bookmark_obj: MatchedBookmarkObj,
    before_or_after: Literal["before", "after"] = "after"
):
    """
    This function is used to load the redis state into the redis database.
    It first copies the redis_before.json to the redis dump directory and then loads it into the redis database.
    It then cleans up the temp file.
    """
    # Export from redis to redis dump
    if not handle_export_from_redis_to_redis_dump(before_or_after):
        return False

    # Copy from redis dump to bookmark directory
    if not handle_copy_redis_state_dump_to_bm_redis_state(matched_bookmark_obj, before_or_after):
        return False

    # Convert to friendly
    bm_redis_state_name = f"redis_{before_or_after}.json"
    bm_redis_state_path = os.path.join(
        matched_bookmark_obj["bookmark_path_slash_abs"], bm_redis_state_name)
    if not convert_redis_state_file_to_friendly_and_save(bm_redis_state_path):
        return False

    # Clean up temp file
    temp_redis_state_name = get_temp_redis_state_name(before_or_after)
    temp_redis_path = os.path.join(REDIS_DUMP_DIR, temp_redis_state_name)
    if os.path.exists(temp_redis_path):
        os.remove(temp_redis_path)
        if IS_DEBUG:
            print(f"🧹 Cleaned up temp file: {temp_redis_path}")
    return True
