import os
import shutil
from app.bookmarks_consts import REDIS_DUMP_DIR, IS_DEBUG # type: ignore
from app.bookmarks_redis import run_redis_command
from redis_friendly_converter import convert_file as convert_redis_to_friendly
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def save_redis_and_friendly_json(bookmark_name: str, bookmark_dir: str):
    print(f"💾 Saving current Redis state for new bookmark '{bookmark_name}'...")

    if not run_redis_command(['export', 'bookmark_temp']):
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

    if not os.path.exists(bookmark_dir):
        print(f"❌ Bookmark directory does not exist: {bookmark_dir}")
        return

    final_path = os.path.join(bookmark_dir, "redis_before.json")
    shutil.move(temp_redis_path, final_path)
    print(f"💾 Saved Redis state to: {final_path}")

    try:
        convert_redis_to_friendly(final_path)
        if IS_DEBUG:
            print(f"📋 Generated friendly Redis before")
    except Exception as e:
        print(f"⚠️  Could not generate friendly Redis before: {e}")
