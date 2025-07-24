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

from app.utils.obs_utils import load_bookmark_into_obs
from app.bookmarks_meta import create_bookmark_meta
from app.utils import get_media_source_info
from redis_friendly_converter import convert_file as convert_redis_to_friendly
from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.bookmarks_redis import run_redis_command, copy_initial_redis_state
# copy_preceding_bookmark_redis_state, copy_specific_bookmark_redis_state
from app.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR, SCREENSHOT_SAVE_SCALE
from app.types.bookmark_types import MatchedBookmarkObj, CurrentRunSettings
from utils.printing_utils import print_color


def handle_matched_bookmark(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):

    ## MATCHED BOOKMARK ##
    matched_bookmark_path_rel = matched_bookmark_obj["bookmark_path_slash_rel"]
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]


    # EXISTING BOOKMARK WORKFLOW
    # print(f"📖 Bookmark '{matched_bookmark_path_rel}' exists - loading OBS state...")

    # Load the OBS bookmark using the matched name
    is_obs_loaded = load_bookmark_into_obs(matched_bookmark_obj)
    if not is_obs_loaded:
        print("❌ Failed to load OBS bookmark")
        return 1

    # Find which folder this bookmark belongs to
    live_folders = get_all_valid_root_dir_names()
    print('---- live_folders:')
    pprint(live_folders)


    if not matched_bookmark_path_rel:
        print(f"❌ Could not determine folder for bookmark '{matched_bookmark_path_rel}'")
        return 1

    # Check if redis_before.json exists in the bookmark directory
    redis_before_path = os.path.join(
        matched_bookmark_path_abs, "redis_before.json")

    if IS_DEBUG:
        print(f"🔍 Checking for existing Redis state at: {redis_before_path}")

    # Handle Redis state based on flags (skip if super dry run)
    if current_run_settings_obj["is_super_dry_run"]:
        print(f"💾 Super dry run mode: Skipping all Redis operations")
    elif current_run_settings_obj["is_blank_slate"]:
        # Handle --blank-slate flag for existing bookmark
        print(f"🆕 Using initial blank slate Redis state for '{matched_bookmark_path_rel}'...")
        if not copy_initial_redis_state(matched_bookmark_path_abs):
            print("❌ Failed to copy initial Redis state")
            return 1
        # Update the path since we just created/copied the file
        redis_before_path = os.path.join(matched_bookmark_path_abs, "redis_before.json")

    elif current_run_settings_obj["is_use_preceding_bookmark"]:
        # Handle --use-preceding-bookmark flag for existing bookmark
        if current_run_settings_obj["cli_args_list"]:
            # TODO(?): This SHOULD also look to see if we have defined a source bookmark, else fallback to preceding bookmark?
            print(f"📋 Using specified bookmark's Redis state for '{matched_bookmark_path_rel}'...")
            print_color("Not implemented!!", "red")
            # if not copy_specific_bookmark_redis_state(current_run_settings_obj["cli_args_list"], matched_bookmark_path_abs):
            #     print("❌ Failed to copy specified bookmark's Redis state")
            #     return 1
        else:
            print(f"📋 Using preceding bookmark's Redis state for '{matched_bookmark_path_rel}'...")
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
        redis_before_path = os.path.join(matched_bookmark_path_abs, "redis_before.json")

    # Load Redis state (skip if super dry run)
    if not current_run_settings_obj["is_super_dry_run"] and os.path.exists(redis_before_path):
        if IS_DEBUG:
            print(f"📊 Loading Redis state from bookmark...")

        # Copy the redis_before.json to the redis dump directory and load it
        temp_redis_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp.json")
        shutil.copy2(redis_before_path, temp_redis_path)
        if IS_DEBUG:
            print(f"📋 Copied Redis state to: {temp_redis_path}")

        if not run_redis_command(['load', 'bookmark_temp']):
            print("❌ Failed to load Redis state")
            # Debug: Check what keys exist after load
            print("🔍 Checking Redis keys after failed load...")
            debug_cmd = 'docker exec -it session_manager redis-cli keys "*" | head -20'
            subprocess.run(debug_cmd, shell=True)
            return 1

        # Clean up temp file
        if os.path.exists(temp_redis_path):
            os.remove(temp_redis_path)
            if IS_DEBUG:
                print(f"🧹 Cleaned up temp file: {temp_redis_path}")
    elif not current_run_settings_obj["is_super_dry_run"]:
        print(f"💾 No existing Redis state found - saving current state...")
        # Save current Redis state as redis_before.json
        if not run_redis_command(['export', 'bookmark_temp']):
            print("❌ Failed to export current Redis state")
            return 1

        # Move the exported file to the bookmark directory
        temp_redis_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp.json")
        if IS_DEBUG:
            print(f"🔍 Looking for exported Redis file at: {temp_redis_path}")

        if os.path.exists(temp_redis_path):
            if not os.path.exists(matched_bookmark_path_abs):
                if IS_DEBUG:
                    print(f"📁 Creating bookmark directory: {matched_bookmark_path_abs}")
                os.makedirs(matched_bookmark_path_abs)
            final_path = os.path.join(matched_bookmark_path_abs, "redis_before.json")
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

    # Take screenshot only if it doesn't exist (skip if no-obs mode)
    print(f"🧪 DEBUG: is_no_obs={current_run_settings_obj['is_no_obs']}, matched_bookmark_path_rel={matched_bookmark_path_rel}, bookmark_dir={matched_bookmark_path_abs}")
    print("🧪 DEBUG: Reached screenshot check for existing bookmark")
    if current_run_settings_obj["is_no_obs"]:
        print(f"📷 No-OBS mode: Skipping screenshot capture")
    else:
        screenshot_path = os.path.join(matched_bookmark_path_abs, "screenshot.jpg")
        if os.path.exists(screenshot_path):
            if IS_DEBUG:
                print(f"📸 Screenshot already exists, preserving: {screenshot_path}")
            print(f"📸 Using existing screenshot: {matched_bookmark_path_rel}/screenshot.jpg")
        else:
            try:
                cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)
                response = cl.send("GetSourceScreenshot", {
                    "sourceName": "Media Source",  # TODO: Make configurable if needed
                    "imageFormat": "png"
                })
                image_data = response.image_data
                if image_data.startswith("data:image/png;base64,"):
                    image_data = image_data.replace("data:image/png;base64,", "")

                decoded_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(decoded_bytes))

                # Resize using SCREENSHOT_SAVE_SCALE
                width = int(image.width * SCREENSHOT_SAVE_SCALE)
                height = int(image.height * SCREENSHOT_SAVE_SCALE)
                resized_image = image.resize((width, height))

                # Save resized image
                jpeg_path = os.path.join(matched_bookmark_path_abs, "screenshot.jpg")
                resized_image.save(jpeg_path, format="JPEG", quality=85)

                if IS_DEBUG:
                    print(f"📋 Screenshot saved to: {screenshot_path}")
                print(f"📸 Screenshot saved to: {matched_bookmark_path_rel}/screenshot.jpg")

            except Exception as e:
                print(f"⚠️  1 Could not take screenshot: {e}")
                print(f"   Please ensure OBS is running and WebSocket server is enabled")


    # Get media source info and create bookmark metadata (only if it doesn't exist)
    bookmark_meta_path = os.path.join(matched_bookmark_path_abs, "bookmark_meta.json")
    if not os.path.exists(bookmark_meta_path):
        if current_run_settings_obj["is_no_obs"]:
            # Create minimal metadata without OBS info
            minimal_media_info = {
                'file_path': '',
                'video_filename': '',
                'timestamp': 0,
                'timestamp_formatted': '00:00:00'
            }
            create_bookmark_meta(matched_bookmark_path_abs, matched_bookmark_path_rel, minimal_media_info, current_run_settings_obj["tags"])
            if IS_DEBUG:
                print(f"📋 Created minimal bookmark metadata (no OBS info)")
        else:
            media_info = get_media_source_info()
            if media_info:
                if os.path.exists(matched_bookmark_path_abs):
                    create_bookmark_meta(matched_bookmark_path_abs, matched_bookmark_path_rel, media_info, current_run_settings_obj["tags"])
                    if IS_DEBUG:
                        print(f"📋 Created bookmark metadata with tags: {current_run_settings_obj['tags']}")
                else:
                    print(f"❌ Could not create bookmark metadata - bookmark directory doesn't exist: {matched_bookmark_path_abs}")
                    return 1
    else:
        # If metadata exists and tags were provided, update the tags
        if current_run_settings_obj["tags"]:
            try:
                with open(bookmark_meta_path, 'r') as f:
                    meta_data = json.load(f)

                # Add new tags (avoid duplicates)
                existing_tags = meta_data.get('tags', [])
                for tag in current_run_settings_obj["tags"]:
                    if tag not in existing_tags:
                        existing_tags.append(tag)

                meta_data['tags'] = existing_tags
                meta_data['last_modified'] = datetime.now().isoformat()

                with open(bookmark_meta_path, 'w') as f:
                    json.dump(meta_data, f, indent=2)

                if IS_DEBUG:
                    print(f"📋 Updated existing bookmark metadata with tags: {current_run_settings_obj['tags']}")
            except Exception as e:
                print(f"⚠️  Could not update bookmark metadata with tags: {e}")
        else:
            if IS_DEBUG:
                print(f"📋 Bookmark metadata already exists, skipping creation")

    # Don't update folder metadata for existing bookmarks - only for new ones
    if IS_DEBUG:
        print(f"📋 Skipping folder metadata update for existing bookmark")

    return matched_bookmark_obj
