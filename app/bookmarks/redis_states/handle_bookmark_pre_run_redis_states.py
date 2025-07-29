import os
import shutil
from app.bookmarks.redis_states.redis_friendly_converter import convert_redis_state_file_to_friendly_and_save
from app.bookmarks.redis_states.bookmarks_redis import run_redis_command, copy_blank_redis_state_to_bm_redis_before
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

    It will determine if it needs to pull from redis, another bookmark's redis_after state, or the blank slate state.
    It will then save the redis_before.json (if applicable) and load the redis state into redis.
    """

    matched_bookmark_path_rel = matched_bookmark_obj["bookmark_path_slash_rel"]
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]

    is_overwrite_bm_redis_before = current_run_settings_obj["is_save_updates"]
    is_no_saving_dry_run = current_run_settings_obj["is_no_saving_dry_run"]
    is_skip_redis_processing = current_run_settings_obj["is_no_docker_no_redis"]
    is_blank_slate = current_run_settings_obj["is_blank_slate"]
    is_use_other_bm_as_template = current_run_settings_obj["is_use_bookmark_as_base"]
    is_use_last_used_bookmark = current_run_settings_obj.get("is_use_last_used_bookmark", False)

    # TODO(MFB): Add one more flag for pulling in the last-used-bookmark's redis_after.json (--continue / --last-used)

    bm_redis_before_path = os.path.join(
        matched_bookmark_path_abs, "redis_before.json")
    is_bm_redis_before_exists = os.path.exists(bm_redis_before_path)

    if is_skip_redis_processing:
        print(f"💾 Super dry run mode: Skipping all Redis operations")
        return

    # TODO(MFB): When do we just load in the current bookmark's redis_before.json to redis?


    # REDIS BEFORE UPDATES

    if is_blank_slate:
        # Pull in the default redis state to redis_before.json (and eventually load it into redis)
        print(
            f"🆕 Using initial blank slate Redis state for '{matched_bookmark_path_rel}'...")
        # TODO(MFB): Look into this:
        if not copy_blank_redis_state_to_bm_redis_before(matched_bookmark_path_abs):
            print("❌ Failed to copy initial Redis state")
            return 1
    elif is_use_other_bm_as_template:
        # Handle --use-preceding-bookmark flag for existing bookmark
        # if current_run_settings_obj["cli_nav_arg_string"]:
        #     # TODO(?): This SHOULD also look to see if we have defined a source bookmark, else fallback to preceding bookmark?
        #     print(
        #         f"📋 Using specified bookmark's Redis state for '{matched_bookmark_path_rel}'...")
        #     print_color("Not implemented!!", "red")
        #     # if not copy_specific_bookmark_redis_state(current_run_settings_obj["cli_nav_arg_string"], matched_bookmark_path_abs):
        #     #     print("❌ Failed to copy specified bookmark's Redis state")
        #     #     return 1
        # else:
        #     print(
        #         f"📋 Using preceding bookmark's Redis state for '{matched_bookmark_path_rel}'...")
        #     print_color("Not implemented!!", "red")
        #     # if not copy_preceding_bookmark_redis_state(matched_bookmark_obj):
        #     #     print("❌ Failed to copy preceding Redis state")
        #     #     return 1

        # # If is_save_updates is enabled, save the pulled-in redis state as redis_before.json
        # if current_run_settings_obj["is_save_updates"]:
        #     print(f"💾 Saving pulled-in Redis state as redis_before.json...")
        #     # The copy functions already create redis_before.json, so we just need to ensure it exists
        #     if os.path.exists(bm_redis_before_path):
        #         if IS_DEBUG:
        #             print(f"📋 Redis before state saved: {bm_redis_before_path}")

        # TODO(MFB): Find the bookmark that is being referenced and pull that redis_after.json into redis_before.json -- Have we saved all of the options (nav vs declared bm) to the current_run_settings_obj?
        # TODO(MFB): If the bookmark is not found, print an error and return 1
        pass
    elif is_use_last_used_bookmark:
        # Pull in the redis_after.json from the last used bookmark into the current bookmark's redis_before.json
        pass
    else:
        # Pull in the current redis state.
        pass


    # Load Redis state (skip if super dry run)
    if os.path.exists(bm_redis_before_path):
        if IS_DEBUG:
            print(f"📊 Loading Redis state from bookmark...")

        handle_load_into_redis(matched_bookmark_obj)


    else:
        print(f"💾 No existing Redis state found - saving current state...")
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