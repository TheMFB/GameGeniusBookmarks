import subprocess
import os
from typing import Literal

from app.bookmarks_consts import IS_DEBUG, INITIAL_REDIS_STATE_DIR, IS_LOCAL_REDIS_DEV
from app.utils.decorators import print_def_name
from app.utils.printing_utils import *

IS_PRINT_DEF_NAME = True

# TODO(KERCH): Keep going from here -- I changed the parameters here to be more align to what you're used to seeing.
@print_def_name(IS_PRINT_DEF_NAME)
def run_redis_command(
    load_or_export: Literal["load", "export"],
    location: Literal["bookmark_temp", "bookmark_temp_after"]
):
    """Run Redis management command"""
    try:
        if IS_LOCAL_REDIS_DEV:
            # Local mode: call redis_export.py or redis_load.py directly
            if load_or_export is "export":
                from standalone_utils.redis.redis_export import redis_export
                return redis_export()
            elif load_or_export is "load":
                from standalone_utils.redis.redis_load import redis_load
                return redis_load("obs_bookmark_saves/test/game_01/redis_after.json")
            else:
                print(f"❌ Unsupported Redis command: {load_or_export}")
                return False

        else:
            # Docker mode
            cmd = f"docker exec -it session_manager python -m utils.standalone.redis_{load_or_export} {location}"
            print_dev('---- cmd:', 'magenta')
            print_dev(cmd)
            print('')

        if IS_DEBUG:
            print(f"🔧 Running Redis command: {load_or_export} {location}")
            print(f"📦 Full shell command: {cmd}")

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True)

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



# def copy_preceding_bookmark_redis_state(matched_bookmark_obj: MatchedBookmarkObj):
#     """Copy redis_after.json from the preceding bookmark to redis_before.json of current bookmark"""
#     # TODO(KERCH): ++ We need to determine the preceding bookmark for the parent folder. However, if instead we define a bookmark after "--use-preceding-bookmark" or "-p", we should use that bookmark's redis_after.json instead.
#     preceding_bookmark = find_preceding_bookmark_args(bookmark_name, folder_dir)
#     if not preceding_bookmark:
#         print(f"❌ No preceding bookmark found for '{bookmark_name}'")
#         return False

#     # Handle nested paths for preceding bookmark
#     preceding_dir = os.path.join(folder_dir, preceding_bookmark)
#     current_dir = os.path.join(folder_dir, bookmark_name)

#     # Ensure current bookmark directory exists
#     if not os.path.exists(current_dir):
#         os.makedirs(current_dir)

#     # Copy redis_after.json from preceding to redis_before.json of current
#     preceding_after = os.path.join(preceding_dir, "redis_after.json")
#     current_before = os.path.join(current_dir, "redis_before.json")

#     if not os.path.exists(preceding_after):
#         print(
#             f"❌ Preceding bookmark '{preceding_bookmark}' has no redis_after.json")
#         return False

#     try:
#         import shutil
#         if os.path.exists(preceding_after):
#             shutil.copy2(preceding_after, current_before)
#         else:
#             print(
#                 f"❌ Preceding bookmark '{preceding_bookmark}' has no redis_after.json")
#             return False

#         # Also copy friendly version if it exists
#         preceding_friendly_after = os.path.join(
#             preceding_dir, "friendly_redis_after.json")
#         current_friendly_before = os.path.join(
#             current_dir, "friendly_redis_before.json")

#         if os.path.exists(preceding_friendly_after):
#             shutil.copy2(preceding_friendly_after, current_friendly_before)
#         else:
#             print(
#                 f"❌ Preceding bookmark '{preceding_bookmark}' has no friendly_redis_after.json")
#             return False

#         return True
#     except Exception as e:
#         print(f"❌ Error copying preceding Redis state: {e}")
#         return False


# def copy_specific_bookmark_redis_state(cli_args_list, target_bookmark_path_abs):
#     """Copy redis_after.json from a specific bookmark to redis_before.json of target bookmark"""
#     # Parse the source bookmark argument (may be "bookmark" or "folder:bookmark")
#     source_folder_name, source_bookmark_name = parse_cli_bookmark_args(
#         cli_args_list)

#     if IS_DEBUG:
#         print(
#             f"🔍 Copying from source: folder='{source_folder_name}', bookmark='{source_bookmark_name}'")

#     # Find the source bookmark
#     source_bookmark_info = None
#     source_folder_dir = None

#     if source_folder_name:
#         # Specific folder specified
#         source_folder_dir = find_bookmark_dir_by_name(source_folder_name)
#         if not source_folder_dir:
#             print(f"❌ Source folder '{source_folder_name}' not found")
#             return False

#         # Find bookmark in that folder
#         matched_name, source_bookmark_info = find_matching_bookmarks(
#             source_bookmark_name, source_folder_dir)
#         if not matched_name:
#             print(
#                 f"❌ Source bookmark '{source_bookmark_name}' not found in folder '{source_folder_name}'")
#             return False
#         source_bookmark_name = matched_name
#     else:
#         # Search across all folders
#         live_folders = get_all_valid_root_dir_names()
#         for folder_path in live_folders:
#             matched_name, bookmark_info = find_matching_bookmarks(
#                 source_bookmark_name, folder_path)
#             if matched_name:
#                 source_bookmark_name = matched_name
#                 source_bookmark_info = bookmark_info
#                 source_folder_dir = folder_path
#                 source_folder_name = os.path.basename(folder_path)
#                 break

#         if not source_bookmark_info:
#             print(
#                 f"❌ Source bookmark '{source_bookmark_name}' not found in any folder")
#             return False

#     print(
#         f"📋 Copying Redis state from '{source_folder_name}:{source_bookmark_name}' to '{target_bookmark_path_abs}'")


#     # Copy redis_after.json from source to redis_before.json of target
#     source_after = os.path.join(
#         source_folder_dir, source_bookmark_name, "redis_after.json")
#     target_before = os.path.join(target_bookmark_path_abs, "redis_before.json")

#     if not os.path.exists(source_after):
#         print(
#             f"❌ Source bookmark '{source_folder_name}:{source_bookmark_name}' has no redis_after.json")
#         return False

#     try:
#         import shutil
#         shutil.copy2(source_after, target_before)
#         print(
#             f"✅ Copied redis_after.json from '{source_folder_name}:{source_bookmark_name}'")

#         # Also copy friendly version if it exists
#         source_friendly_after = os.path.join(
#             source_folder_dir, source_bookmark_name, "friendly_redis_after.json")
#         target_friendly_before = os.path.join(
#             target_bookmark_path_abs, "friendly_redis_before.json")

#         if os.path.exists(source_friendly_after):
#             shutil.copy2(source_friendly_after, target_friendly_before)
#             print(
#                 f"✅ Copied friendly_redis_after.json from '{source_folder_name}:{source_bookmark_name}'")
#         else:
#             print(f"⚠️  Source bookmark has no friendly_redis_after.json")

#         return True
#     except Exception as e:
#         print(
#             f"❌ Error copying Redis state from '{source_folder_name}:{source_bookmark_name}': {e}")
#         return False

@print_def_name(IS_PRINT_DEF_NAME)
def copy_initial_redis_state(bookmark_path_slash_abs: str):
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
            print(f"📋 Copied initial_redis_before.json to redis_before.json")
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
