import subprocess
import os
from typing import Literal
from app.consts.bookmarks_consts import IS_DEBUG, INITIAL_REDIS_STATE_DIR, IS_LOCAL_REDIS_DEV
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.decorators import print_def_name
from app.utils.printing_utils import *
from standalone_utils.redis.export_from_redis import export_from_redis
from standalone_utils.redis.load_into_redis_local import load_into_redis_local

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def run_redis_command(
    load_or_export: Literal["load", "export"],
    location: Literal["bookmark_temp", "bookmark_temp_after"]
):
    """Run Redis management command"""
    try:
        if IS_LOCAL_REDIS_DEV:
            # Local mode: call export_from_redis.py or load_into_redis.py directly
            if load_or_export == "export":
                return export_from_redis(location)
            elif load_or_export == "load":
                return load_into_redis_local(location)
            else:
                print(f"❌ Unsupported Redis command: {load_or_export}")
                return False

        else:
            # Docker mode
            cmd = f"docker exec -it session_manager python -m utils.standalone.redis_{load_or_export} {location}"
            print_dev('---- cmd:', 'magenta')
            print_dev(cmd)
            print('')
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                print(f"❌ Redis command failed: {load_or_export} {location}")
                print(f"   Error: {result.stderr}")
                print(f"   Output: {result.stdout}")
                return False

            if IS_DEBUG:
                print(f"✅ Redis command succeeded: {load_or_export} {location}")
            return True

    except Exception as e:
        print(f"❌ Error running Redis command: {load_or_export} {location}")
        print(f"   Exception: {e}")
        return False


@print_def_name(IS_PRINT_DEF_NAME)
def copy_blank_redis_state_to_bm_redis_before(bookmark_path_slash_abs: str):
    """Copy initial Redis state files to the bookmark directory"""
    # Paths to initial state files
    initial_redis = os.path.join(
        INITIAL_REDIS_STATE_DIR, "initial_redis_before.json")
    initial_friendly = os.path.join(
        INITIAL_REDIS_STATE_DIR, "initial_friendly_redis_before.json")

    # Copy initial redis state
    current_before = os.path.join(bookmark_path_slash_abs, "redis_before.json")
    current_friendly_before = os.path.join(
        bookmark_path_slash_abs, "friendly_redis_before.json")

    try:
        import shutil

        if os.path.exists(initial_redis):
            shutil.copy2(initial_redis, current_before)
            print("📋 Copied initial_redis_before.json to redis_before.json")
        else:
            print(f"❌ Initial Redis state file not found: {initial_redis}")
            return False

        if os.path.exists(initial_friendly):
            shutil.copy2(initial_friendly, current_friendly_before)
        else:
            print(
                f"❌ Initial friendly Redis state file not found: {initial_friendly}")
            return False

        return True
    except Exception as e:
        print(f"❌ Error copying initial Redis state: {e}")
        return False


def handle_copy_redis_state_from_base_to_bookmark(
        base_bookmark_obj: MatchedBookmarkObj,
        target_bookmark_obj: MatchedBookmarkObj
):
    """
    Copy redis_after.json from a specific bookmark to redis_before.json of target bookmark
    
    """
    # TODO(MFB): Does this need to load into redis, from here, or should
    base_bm_path_abs = base_bookmark_obj.get("bookmark_path_slash_abs")
    target_bm_path_abs = target_bookmark_obj.get("bookmark_path_slash_abs")

    # Copy redis_after.json from base to redis_before.json of target
    base_redis_after_state_path = os.path.join(base_bm_path_abs, "redis_after.json")
    target_redis_before_state_path = os.path.join(target_bm_path_abs, "redis_before.json")

    if not os.path.exists(base_redis_after_state_path):
        print(
            f"❌ Base bookmark redis state '{base_redis_after_state_path}' does not exist")
        return False

    try:
        import shutil
        shutil.copy2(base_redis_after_state_path, target_redis_before_state_path)
        print(
            f"✅ Copied redis_after.json from '{base_bookmark_obj['bookmark_path_slash_rel']}' to '{target_bookmark_obj['bookmark_path_slash_rel']}' redis_before.json")

        # Also copy friendly version if it exists
        base_friendly_after_state_path = os.path.join(base_bm_path_abs, "friendly_redis_after.json")
        target_friendly_before_state_path = os.path.join(target_bm_path_abs, "friendly_redis_before.json")

        if os.path.exists(base_friendly_after_state_path):
            shutil.copy2(base_friendly_after_state_path, target_friendly_before_state_path)
            print(
                f"✅ Copied friendly_redis_after.json from '{base_bookmark_obj['bookmark_path_slash_rel']}' to '{target_bookmark_obj['bookmark_path_slash_rel']}' friendly_redis_before.json")
        else:
            print("⚠️  base bookmark has no friendly_redis_after.json")

        return True
    except Exception as e:
        print(
            f"❌ Error copying Redis state from '{base_redis_after_state_path}:{target_redis_before_state_path}': {e}")
        return False
