import os
import shutil
from app.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR
from redis_friendly_converter import convert_file as convert_redis_to_friendly
from app.bookmarks_redis import run_redis_command
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def handle_save_redis_after_json(matched_bookmark_obj, current_run_settings_obj):
    """
    Handles saving the final Redis state to redis_after.json
    Returns: True if redis_after was saved, False otherwise
    """
    bookmark_dir_slash_abs = matched_bookmark_obj["bookmark_dir_slash_abs"]
    bookmark_tail_name = matched_bookmark_obj["bookmark_tail_name"]
    # TODO(MFB): Do we need both of these?
    is_save_updates = current_run_settings_obj["is_save_updates"] or current_run_settings_obj["is_overwrite_redis_after"]

    if IS_DEBUG:
        print(f"🔍 Debug - bookmark_dir_slash_abs: {bookmark_dir_slash_abs}")
        print(f"🔍 Debug - bookmark_tail_name: {bookmark_tail_name}")
        print(f"🔍 Debug - is_save_updates: {is_save_updates}")

    redis_after_exists = False
    if bookmark_dir_slash_abs:
        bookmark_dir = os.path.join(bookmark_dir_slash_abs, bookmark_tail_name)
        final_after_path = os.path.join(bookmark_dir, "redis_after.json")
        redis_after_exists = os.path.exists(final_after_path)

        if IS_DEBUG:
            print(f"🔍 Debug - redis_after_exists: {redis_after_exists}")
            print(f"🔍 Debug - is_save_updates: {is_save_updates}")
            print(f"🔍 Debug - final_after_path: {final_after_path}")

        should_save_redis_after = is_save_updates or not redis_after_exists

        if should_save_redis_after:
            if IS_DEBUG:
                if is_save_updates and redis_after_exists:
                    print(f"💾 Overwriting existing Redis after state...")
                else:
                    print(f"💾 Saving final Redis state...")

            if not run_redis_command('export', 'bookmark_temp_after'):
                print("❌ Failed to export final Redis state")
                return False

            # Move the final Redis export to the bookmark directory
            temp_redis_after_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp_after.json")
            if os.path.exists(temp_redis_after_path) and os.path.exists(bookmark_dir):
                final_after_path = os.path.join(bookmark_dir, "redis_after.json")
                shutil.move(temp_redis_after_path, final_after_path)
                if IS_DEBUG:
                    print(f"💾 Saved final Redis state to: {final_after_path}")

                # Generate friendly version
                try:
                    convert_redis_to_friendly(final_after_path)
                    if IS_DEBUG:
                        print(f"📋 Generated friendly Redis after")
                except Exception as e:
                    print(f"⚠️  Could not generate friendly Redis after: {e}")
            else:
                print(f"❌ Could not move final Redis file - temp_after exists: {os.path.exists(temp_redis_after_path)}, bookmark_dir exists: {os.path.exists(bookmark_dir) if bookmark_dir else 'bookmark_dir is None'}")
                if os.path.exists(REDIS_DUMP_DIR):
                    files = os.listdir(REDIS_DUMP_DIR)
                    print(f"🔍 Files in Redis dump directory: {files}")

        return should_save_redis_after

    return False
