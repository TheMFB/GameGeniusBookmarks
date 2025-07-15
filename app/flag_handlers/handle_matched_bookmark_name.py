import os
import json
import subprocess
import shutil
import base64
import io
from datetime import datetime
from PIL import Image
import obsws_python as obs

from app.bookmarks import load_obs_bookmark_directly
from app.bookmarks_meta import create_bookmark_meta
from app.utils import get_media_source_info
from redis_friendly_converter import convert_file as convert_redis_to_friendly
from app.bookmarks_folders import get_all_active_folders
from app.bookmarks_redis import (
    run_redis_command,
    copy_initial_redis_state,
    copy_preceding_redis_state,
    copy_specific_bookmark_redis_state
)
from app.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR, SCREENSHOT_SAVE_SCALE




def handle_matched_bookmark_name(
    matched_bookmark_name,
    bookmark_info,
    is_show_image,
    is_no_obs,
    is_super_dry_run,
    is_blank_slate,
    is_use_preceding_bookmark,
    is_save_updates,
    is_save_last_redis,
    tags,
    source_bookmark_arg
):

    ## MATCHED BOOKMARK ##


    if matched_bookmark_name:
        # TODO(KERCH): Pull this out into a "handle_matched_bookmark_name"
        # EXISTING BOOKMARK WORKFLOW
        print(f"📖 Bookmark '{matched_bookmark_name}' exists - loading OBS state...")

        # Load the OBS bookmark using the matched name
        success = load_obs_bookmark_directly(matched_bookmark_name, bookmark_info)
        if not success:
            print("❌ Failed to load OBS bookmark")
            return 1

        # Update the bookmark name for the rest of the process
        bookmark_name = matched_bookmark_name

        # Find which folder this bookmark belongs to
        folder_dir = None
        active_folders = get_all_active_folders()
        for folder_path in active_folders:
            print(f"🔍 Searching in folder: {folder_path}")  # ← add this here
            bookmark_name_full = os.path.join(folder_path, matched_bookmark_name)
            if os.path.exists(bookmark_name_full):
                folder_dir = folder_path
                folder_name = os.path.basename(folder_dir)
                print(f"🎯 Using folder: {folder_name}")

                if is_show_image:
                    screenshot_path = os.path.join(folder_dir, bookmark_name, "screenshot.jpg")
                    if os.path.exists(screenshot_path):
                        print(f"🖼️ Displaying screenshot in terminal: {screenshot_path}")
                        try:
                            result = subprocess.run(
                                ["imgcat", screenshot_path],
                                check=True,
                                capture_output=True,
                                text=True
                            )
                            print(result.stdout)

                        except subprocess.CalledProcessError as e:
                            print(f"❌ imgcat failed with error:\n{e.stderr}")
                        except Exception as e:
                            print(f"⚠️  Failed to display image in terminal: {e}")
                    else:
                        print(f"❌ No screenshot.jpg found at: {screenshot_path}")

                break

        if not folder_dir:
            print(f"❌ Could not determine folder for bookmark '{matched_bookmark_name}'")
            return 1

        # Check if redis_before.json exists in the bookmark directory
        bookmark_dir = os.path.join(folder_dir, matched_bookmark_name)
        redis_before_path = os.path.join(bookmark_dir, "redis_before.json")

        if IS_DEBUG:
            print(f"🔍 Checking for existing Redis state at: {redis_before_path}")

        # Handle Redis state based on flags (skip if super dry run)
        if is_super_dry_run:
            print(f"💾 Super dry run mode: Skipping all Redis operations")
        elif is_blank_slate:
            # Handle --blank-slate flag for existing bookmark
            print(f"🆕 Using initial blank slate Redis state for '{matched_bookmark_name}'...")
            if not copy_initial_redis_state(matched_bookmark_name, folder_dir):
                print("❌ Failed to copy initial Redis state")
                return 1
            # Update the path since we just created/copied the file
            redis_before_path = os.path.join(bookmark_dir, "redis_before.json")

        elif is_use_preceding_bookmark:
            # Handle --use-preceding-bookmark flag for existing bookmark
            if source_bookmark_arg:
                print(f"📋 Using specified bookmark's Redis state for '{matched_bookmark_name}'...")
                if not copy_specific_bookmark_redis_state(source_bookmark_arg, matched_bookmark_name, folder_dir):
                    print("❌ Failed to copy specified bookmark's Redis state")
                    return 1
            else:
                print(f"📋 Using preceding bookmark's Redis state for '{matched_bookmark_name}'...")
                if not copy_preceding_redis_state(matched_bookmark_name, folder_dir):
                    print("❌ Failed to copy preceding Redis state")
                    return 1

            # If is_save_updates is enabled, save the pulled-in redis state as redis_before.json
            if is_save_updates:
                print(f"💾 Saving pulled-in Redis state as redis_before.json...")
                # The copy functions already create redis_before.json, so we just need to ensure it exists
                if os.path.exists(redis_before_path):
                    if IS_DEBUG:
                        print(f"📋 Redis before state saved: {redis_before_path}")

            # Update the path since we just created/copied the file
            redis_before_path = os.path.join(bookmark_dir, "redis_before.json")

        # Load Redis state (skip if super dry run)
        if not is_super_dry_run and os.path.exists(redis_before_path):
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
        elif not is_super_dry_run:
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
                if not os.path.exists(bookmark_dir):
                    if IS_DEBUG:
                        print(f"📁 Creating bookmark directory: {bookmark_dir}")
                    os.makedirs(bookmark_dir)
                final_path = os.path.join(bookmark_dir, "redis_before.json")
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
        print(f"🧪 DEBUG: is_no_obs={is_no_obs}, matched_bookmark_name={matched_bookmark_name}, bookmark_dir={bookmark_dir}")
        print("🧪 DEBUG: Reached screenshot check for existing bookmark")
        if is_no_obs:
            print(f"📷 No-OBS mode: Skipping screenshot capture")
        else:
            screenshot_path = os.path.join(bookmark_dir, "screenshot.jpg")
            if os.path.exists(screenshot_path):
                if IS_DEBUG:
                    print(f"📸 Screenshot already exists, preserving: {screenshot_path}")
                print(f"📸 Using existing screenshot: {matched_bookmark_name or bookmark_name}/screenshot.jpg")
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
                    jpeg_path = os.path.join(bookmark_dir, "screenshot.jpg")
                    resized_image.save(jpeg_path, format="JPEG", quality=85)

                    if IS_DEBUG:
                        print(f"📋 Screenshot saved to: {screenshot_path}")
                    print(f"📸 Screenshot saved to: {matched_bookmark_name or bookmark_name}/screenshot.jpg")

                except Exception as e:
                    print(f"⚠️  Could not take screenshot: {e}")
                    print(f"   Please ensure OBS is running and WebSocket server is enabled")


        # Get media source info and create bookmark metadata (only if it doesn't exist)
        bookmark_meta_path = os.path.join(bookmark_dir, "bookmark_meta.json")
        if not os.path.exists(bookmark_meta_path):
            if is_no_obs:
                # Create minimal metadata without OBS info
                minimal_media_info = {
                    'file_path': '',
                    'video_filename': '',
                    'timestamp': 0,
                    'timestamp_formatted': '00:00:00'
                }
                create_bookmark_meta(bookmark_dir, matched_bookmark_name, minimal_media_info, tags)
                if IS_DEBUG:
                    print(f"📋 Created minimal bookmark metadata (no OBS info)")
            else:
                media_info = get_media_source_info()
                if media_info:
                    if os.path.exists(bookmark_dir):
                        create_bookmark_meta(bookmark_dir, matched_bookmark_name, media_info, tags)
                        if IS_DEBUG:
                            print(f"📋 Created bookmark metadata with tags: {tags}")
                    else:
                        print(f"❌ Could not create bookmark metadata - bookmark directory doesn't exist: {bookmark_dir}")
                        return 1
        else:
            # If metadata exists and tags were provided, update the tags
            if tags:
                try:
                    with open(bookmark_meta_path, 'r') as f:
                        meta_data = json.load(f)

                    # Add new tags (avoid duplicates)
                    existing_tags = meta_data.get('tags', [])
                    for tag in tags:
                        if tag not in existing_tags:
                            existing_tags.append(tag)

                    meta_data['tags'] = existing_tags
                    meta_data['last_modified'] = datetime.now().isoformat()

                    with open(bookmark_meta_path, 'w') as f:
                        json.dump(meta_data, f, indent=2)

                    if IS_DEBUG:
                        print(f"📋 Updated existing bookmark metadata with tags: {tags}")
                except Exception as e:
                    print(f"⚠️  Could not update bookmark metadata with tags: {e}")
            else:
                if IS_DEBUG:
                    print(f"📋 Bookmark metadata already exists, skipping creation")

        # Don't update folder metadata for existing bookmarks - only for new ones
        if IS_DEBUG:
            print(f"📋 Skipping folder metadata update for existing bookmark")

    return folder_dir, bookmark_name
