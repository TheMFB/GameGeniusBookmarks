import os
import shutil

from app.bookmarks.redis_states.bookmarks_redis import run_redis_command
from app.bookmarks.redis_states.redis_friendly_converter import (
    convert_redis_state_file_to_friendly_and_save,
)
from app.consts.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR
from app.utils.decorators import print_def_name
from app.utils.printing_utils import pprint, print_color

IS_PRINT_DEF_NAME = True

# TODO(MFB): Break this up into two functions. Saving the redis state and updating the bookmark redis_before.json.

@print_def_name(IS_PRINT_DEF_NAME)
def handle_save_redis_state_and_update_bm_redis_before(bookmark_path_slash_abs: str):
    print_color('---- bookmark_path_slash_abs:', 'magenta')
    pprint(bookmark_path_slash_abs)

    if IS_DEBUG:
        print(f"💾 Saving current Redis state '{bookmark_path_slash_abs}'...")

    if not run_redis_command('export', 'bookmark_temp'):
        print("⚠️ Failed to export current Redis state — continuing anyway for debug purposes")
        return

    temp_redis_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp.json")
    if IS_DEBUG:
        print(f"🔍 Checking for exported Redis file at: {temp_redis_path}")

    if not os.path.exists(temp_redis_path):
        print(f"❌ Expected Redis export file not found: {temp_redis_path}")
        if os.path.exists(REDIS_DUMP_DIR):
            files = os.listdir(REDIS_DUMP_DIR)
            print(f"🔍 Files in Redis dump directory: {files}")
        return

    if not os.path.exists(bookmark_path_slash_abs):
        print(f"❌ Bookmark directory does not exist: {bookmark_path_slash_abs}")
        return

    final_path = os.path.join(bookmark_path_slash_abs, "redis_before.json")
    shutil.move(temp_redis_path, final_path)
    print(f"💾 Saved Redis state to: {final_path}")

    try:
        convert_redis_state_file_to_friendly_and_save(final_path)
        if IS_DEBUG:
            print("📋 Generated friendly Redis before")
    except Exception as e:
        print(f"⚠️  Could not generate friendly Redis before: {e}")
