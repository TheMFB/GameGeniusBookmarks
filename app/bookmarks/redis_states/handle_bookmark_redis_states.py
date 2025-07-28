from pprint import pprint
import os
import json
import subprocess
import shutil
import base64
import io
from datetime import datetime
from PIL import Image
import obsws_python as obs

from app.utils.obs_utils import load_bookmark_into_obs, get_media_source_info
from app.bookmarks_meta import create_bookmark_meta
from redis_friendly_converter import convert_file as convert_redis_to_friendly
from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.bookmarks_redis import run_redis_command, copy_initial_redis_state
# copy_preceding_bookmark_redis_state, copy_specific_bookmark_redis_state
from app.consts.bookmarks_consts import IS_DEBUG, IS_LOCAL_REDIS_DEV, REDIS_DUMP_DIR, SCREENSHOT_SAVE_SCALE
from app.types.bookmark_types import MatchedBookmarkObj, CurrentRunSettings
from app.utils.printing_utils import *



def handle_bookmark_redis_states(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):
    matched_bookmark_path_rel = matched_bookmark_obj["bookmark_path_slash_rel"]
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]

    # Check if redis_before.json exists in the bookmark directory
    redis_before_path = os.path.join(
        matched_bookmark_path_abs, "redis_before.json")

    # Handle Redis state based on flags (skip if super dry run)
    if current_run_settings_obj["is_no_docker_no_redis"]:
        print(f"💾 Super dry run mode: Skipping all Redis operations")
    elif current_run_settings_obj["is_blank_slate"]:
        # Handle --blank-slate flag for existing bookmark
        print(
            f"🆕 Using initial blank slate Redis state for '{matched_bookmark_path_rel}'...")
        if not copy_initial_redis_state(matched_bookmark_path_abs):
            print("❌ Failed to copy initial Redis state")
            return 1
        # Update the path since we just created/copied the file
        redis_before_path = os.path.join(
            matched_bookmark_path_abs, "redis_before.json")

    elif current_run_settings_obj["is_use_preceding_bookmark"]:
        # Handle --use-preceding-bookmark flag for existing bookmark
        if current_run_settings_obj["cli_nav_arg_string"]:
            # TODO(?): This SHOULD also look to see if we have defined a source bookmark, else fallback to preceding bookmark?
            print(
                f"📋 Using specified bookmark's Redis state for '{matched_bookmark_path_rel}'...")
            print_color("Not implemented!!", "red")
            # if not copy_specific_bookmark_redis_state(current_run_settings_obj["cli_nav_arg_string"], matched_bookmark_path_abs):
            #     print("❌ Failed to copy specified bookmark's Redis state")
            #     return 1
        else:
            print(
                f"📋 Using preceding bookmark's Redis state for '{matched_bookmark_path_rel}'...")
            print_color("Not implemented!!", "red")
            # if not copy_preceding_bookmark_redis_state(matched_bookmark_obj):
            #     print("❌ Failed to copy preceding Redis state")
            #     return 1

        # If is_save_updates is enabled, save the pulled-in redis state as redis_before.json
        if current_run_settings_obj["is_save_updates"]:
            print(f"💾 Saving pulled-in Redis state as redis_before.json...")
            # The copy functions already create redis_before.json, so we just need to ensure it exists
            if os.path.exists(redis_before_path):
                if IS_DEBUG:
                    print(f"📋 Redis before state saved: {redis_before_path}")

        # Update the path since we just created/copied the file
        redis_before_path = os.path.join(
            matched_bookmark_path_abs, "redis_before.json")

    # Load Redis state (skip if super dry run)
    # TODO(KERCH): If we are in just dry run mode, we need to be saving the redis state. If we are in super dry run mode, we should not save the redis state.
    if not current_run_settings_obj["is_no_docker_no_redis"] and os.path.exists(redis_before_path):
        if IS_DEBUG:
            print(f"📊 Loading Redis state from bookmark...")

        # Copy the redis_before.json to the redis dump directory and load it
        temp_redis_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp.json")
        shutil.copy2(redis_before_path, temp_redis_path)
        if IS_DEBUG:
            print(f"📋 Copied Redis state to: {temp_redis_path}")

        run_redis_results = run_redis_command('load', 'bookmark_temp')

        if not run_redis_results:
            print("❌ Failed to load Redis state")
            # Debug: Check what keys exist after load
            if not IS_LOCAL_REDIS_DEV:
                print("🔍 Checking Redis keys after failed load...")
                debug_cmd = 'docker exec -it session_manager redis-cli keys "*" | head -20'
                subprocess.run(debug_cmd, shell=True)
            return 1

        # Clean up temp file
        if os.path.exists(temp_redis_path):
            os.remove(temp_redis_path)
            if IS_DEBUG:
                print(f"🧹 Cleaned up temp file: {temp_redis_path}")
    # TODO(KERCH): If we are in just dry run mode, we need to be saving the redis state. If we are in super dry run mode, we should not save the redis state.
    elif not current_run_settings_obj["is_no_docker_no_redis"]:
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
                convert_redis_to_friendly(final_path)
                if IS_DEBUG:
                    print(f"📋 Generated friendly Redis before")
            except Exception as e:
                print(f"⚠️  Could not generate friendly Redis before: {e}")
        else:
            print(f"❌ Expected Redis export file not found: {temp_redis_path}")
            # List what files are actually in the redis dump directory
            if os.path.exists(REDIS_DUMP_DIR):
                files = os.listdir(REDIS_DUMP_DIR)
                print(f"🔍 Files in Redis dump directory: {files}")

    return 0