import os
import shutil
from app.bookmarks.redis_states.redis_friendly_converter import convert_redis_state_file_to_friendly_and_save
from app.bookmarks.redis_states.bookmarks_redis import handle_copy_redis_state_from_base_to_bookmark, run_redis_command, copy_blank_redis_state_to_bm_redis_before
from app.consts.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR
from app.types.bookmark_types import MatchedBookmarkObj, CurrentRunSettings
from app.utils.printing_utils import *
from app.bookmarks.redis_states.handle_load_into_redis import handle_load_into_redis


def handle_bookmark_pre_run_redis_states(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):
    """
    This function is used to handle the Redis states for a bookmark before processing is run

    First we will determine if the bookmark has a redis_before.json.

    # Cases:
    - Standard Create: We will pull from redis to save to the redis_before.json. We CAN reload that back into redis, but not necessary.

    - Standard Rerun: We will pull the redis_before.json from the bookmark directory and load it into redis.
    - Blank Slate: We will pull the initial_redis_before.json and load it into redis.
    - Use BM as Template: We will pull the redis_after.json from the base bookmark and save it to the redis_before.json. We will then load it into redis.
    - Use Last Used: We will pull the redis_after.json from the last used bookmark and save it to the redis_before.json. We will then load it into redis.

    # Changes to Flow :
    - Dry Run: No lasting changes will be made. It will still update Redis, but all redis state files will remain the same. NO code changes.
    - is_no_docker_no_redis: We will skip ALL redis operations, and proceed with updates and such that we can.
    - is_save_updates: We ignore the redis_before / redis_after states in our matched bookmark, and save any changes that happen.


    It will also handle the super dry run mode, where it will skip all redis operations.
    """

    matched_bookmark_path_rel = matched_bookmark_obj["bookmark_path_slash_rel"]
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]

    is_overwrite_bm_redis_before = current_run_settings_obj["is_save_updates"]
    is_no_saving_dry_run = current_run_settings_obj["is_no_saving_dry_run"]

    is_skip_redis_processing = current_run_settings_obj["is_no_docker_no_redis"]
    is_blank_slate = current_run_settings_obj["is_blank_slate"]
    is_use_other_bm_as_template = current_run_settings_obj["is_use_bookmark_as_base"]

    # TODO(MFB): Add one more flag for pulling in the last-used-bookmark's redis_after.json (--continue / --last-used)

    # TODO(MFB): +++ HERE +++ - handle_bookmark_pre_run_redis_states

    bm_redis_before_path = os.path.join(
        matched_bookmark_path_abs, "redis_before.json")
    is_bm_redis_before_exists = os.path.exists(bm_redis_before_path)

    if is_skip_redis_processing:
        # TODO(MFB): Do we want to skip ALL redis operations, or just the ones that save?
        print("💾 Dry run mode: Skipping all Redis operations")
        return

    # TODO(MFB): When do we just load in the current bookmark's redis_before.json to redis?
        # TODO(?): Do we need is_save_updates flag for these to be enabled to overwrite the existing redis_before.json? If so, we should just pull them into a temp file and then either into redis and/or save to the bookmark directory. Note that this will help with dry-run.

    # TODO(MFB): I think ALL of these should likely have the intermediate of saving to the temp file, and then either being pulled into redis or saved to the bookmark directory.


    # REDIS BEFORE UPDATES

    # Pull in the default redis state to redis_before.json (and eventually load it into redis)
    if is_blank_slate:
        print(
            f"🆕 Using initial blank slate Redis state for '{matched_bookmark_path_rel}'...")
        if not copy_blank_redis_state_to_bm_redis_before(matched_bookmark_path_abs):
            print("❌ Failed to copy initial Redis state")
            return 1
    elif is_use_other_bm_as_template:
        if current_run_settings_obj.get("base_bookmark_obj"):
            if not handle_copy_redis_state_from_base_to_bookmark(current_run_settings_obj["base_bookmark_obj"], matched_bookmark_obj):
                print("❌ Failed to copy base bookmark's Redis state")
                return 1
        else:
            print_color("❌ No base bookmark object found", "red")
            return 1

    else:
        # Pull in the current redis state.
        pass

    # Load Redis state
    if os.path.exists(bm_redis_before_path):
        if IS_DEBUG:
            print("📊 Loading Redis state from bookmark...")
        handle_load_into_redis(matched_bookmark_obj)

    else:
        print("💾 No existing Redis state found - saving current state...")

        # Save current Redis state as redis_before.json
        if not run_redis_command('export', 'bookmark_temp'):
            print("❌ Failed to export current Redis state")
            return 1

        # Move the exported file to the bookmark directory
        temp_redis_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp.json")
        if IS_DEBUG:
            print(f"🔍 Looking for exported Redis file at: {temp_redis_path}")

        if os.path.exists(temp_redis_path):
            if not os.path.exists(matched_bookmark_path_abs):
                if IS_DEBUG:
                    print(
                        f"📁 Creating bookmark directory: {matched_bookmark_path_abs}")
                os.makedirs(matched_bookmark_path_abs)
            final_path = os.path.join(
                matched_bookmark_path_abs, "redis_before.json")
            shutil.move(temp_redis_path, final_path)
            if IS_DEBUG:
                print(f"📋 Moved Redis state to: {final_path}")

            # Generate friendly version
            try:
                convert_redis_state_file_to_friendly_and_save(final_path)
                if IS_DEBUG:
                    print("📋 Generated friendly Redis before")
            except Exception as e:
                print(f"⚠️  Could not generate friendly Redis before: {e}")
        else:
            print(f"❌ Expected Redis export file not found: {temp_redis_path}")
            # List what files are actually in the redis dump directory
            if os.path.exists(REDIS_DUMP_DIR):
                files = os.listdir(REDIS_DUMP_DIR)
                print(f"🔍 Files in Redis dump directory: {files}")

    return 0