"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
from pprint import pprint
import os
import sys
import subprocess
import time
import json
from networkx import to_dict_of_dicts
import obsws_python as obs
from datetime import datetime
from PIL import Image
import io

from app.bookmarks import interactive_fuzzy_lookup
from app.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR, ASYNC_WAIT_TIME, OPTIONS_HELP, USAGE_HELP, IS_PRINT_JUST_CURRENT_FOLDER_BOOKMARKS
from app.bookmarks_folders import get_all_active_folders, parse_folder_bookmark_arg, create_new_folder, find_folder_by_name, create_folder_with_name, select_folder_for_new_bookmark, update_folder_last_bookmark
from app.bookmarks_redis import copy_preceding_redis_state, copy_specific_bookmark_redis_state, copy_initial_redis_state, run_redis_command
from app.bookmarks import get_bookmark_info, load_obs_bookmark_directly, load_bookmarks_from_folder, normalize_path, is_strict_equal, save_last_used_bookmark, get_last_used_bookmark_display, resolve_navigation_bookmark, get_last_used_bookmark
from app.bookmarks_print import print_all_folders_and_bookmarks
from app.bookmarks_meta import create_bookmark_meta, create_folder_meta, create_folder_meta
from app.utils import print_color, get_media_source_info
from redis_friendly_converter import convert_file as convert_redis_to_friendly
from app.flag_handlers import help, ls, which, find_preceding_bookmark, open_video, find_tags


SCREENSHOT_SAVE_SCALE = 0.25  # Scale screenshots to 25% of original size

# Define supported flags
supported_flags = [
    "-a",
    "--add",
    "-s",
    "--save-updates",
    "-p",
    "--use-preceding-bookmark",
    "-b",
    "--blank-slate",
    "-d",
    "--dry-run",
    "-sd",
    "--super-dry-run",
    "--no-obs",
    "--save-last-redis",
    "-v",
    "--open-video",
    "-t",
    "--tags",
    "--show-image",
]

def run_main_process():
    """Run the main game processor"""
    try:
        cmd = 'docker exec -it game_processor_backend python ./main.py --run-once --gg_user_id="DEV_GG_USER_ID"'
        if IS_DEBUG:
            print(f"🔧 Running main process...")
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running main process: {e}")
        return False

def main():
    # Parse command line arguments
    args = sys.argv[1:]

    # All of these will halt the process and only do what it does here:

    # Print help/usage if no arguments or -h/--help is present
    if not args or '-h' in args or '--help' in args:
        return help()

    # Handle -ls or --ls
    if '-ls' in args or '--ls' in args:
        return ls(args)

    # Handle --which or -w (fuzzy bookmark match check)
    if '--which' in args or '-w' in args:
        return which(args)

    # Check for video opening flags
    if "--open-video" in args or "-v" in args:
        return open_video(args)

    # Otherwise, we have a bookmark/reserved bookmark name

    bookmark_arg = args[0]

    # Check if this is a navigation command
    navigation_commands = ["next", "previous", "first", "last"]
    is_navigation = bookmark_arg in navigation_commands

    # Check for unsupported flags
    unsupported_flags = [arg for arg in args if arg.startswith("--") and arg not in supported_flags]
    if unsupported_flags:
        print(f"⚠️  Warning: Unsupported flags detected: {unsupported_flags}")
        print(OPTIONS_HELP)
        print()



    is_save_last_redis = "--save-last-redis" in args or "-s" in args
    is_save_updates = "--save-updates" in args or "-s" in args
    is_use_preceding_bookmark = "--use-preceding-bookmark" in args or "-p" in args
    is_blank_slate = "--blank-slate" in args or "-b" in args
    is_dry_run = "--dry-run" in args or "-d" in args
    is_super_dry_run = "--super-dry-run" in args or "-sd" in args
    is_no_obs = "--no-obs" in args  # ✅ FIXED this line
    is_show_image = "--show-image" in args
    is_add_bookmark = "--add" in args or "-a" in args

    if is_super_dry_run:
        print("💧 SUPER DRY RUN: Will skip Redis operations and Docker commands.")
        print("💧 Still creating/updating bookmarks and metadata.")

    # Parse the source bookmark for --use-preceding-bookmark if specified

    if is_use_preceding_bookmark:
        source_bookmark_arg = find_preceding_bookmark(args)

    # Parse tags from command line
    if "--tags" in args or "-t" in args:
        tags = find_tags(args)

    # TODO(KERCH): ++++ Pick up cleanup from here.

    if IS_DEBUG:
        print(f"🔍 Debug - Args: {args}")
        print(f"🔍 Debug - is_save_last_redis: {is_save_last_redis}")
        print(f"🔍 Debug - is_save_updates: {is_save_updates}")
        print(f"🔍 Debug - is_use_preceding_bookmark: {is_use_preceding_bookmark}")
        print(f"🔍 Debug - source_bookmark_arg: {source_bookmark_arg}")
        print(f"🔍 Debug - is_blank_slate: {is_blank_slate}")
        print(f"🔍 Debug - is_dry_run: {is_dry_run}")
        print(f"🔍 Debug - is_super_dry_run: {is_super_dry_run}")
        print(f"🔍 Debug - tags: {tags}")
        print(f"🔍 Debug - is_no_obs: {is_no_obs}")

    # Parse folder:bookmark format if present (only if not navigation)
    specified_folder_name, bookmark_path = parse_folder_bookmark_arg(bookmark_arg)

    if specified_folder_name:
        print(f"🎯 Specified folder: '{specified_folder_name}', bookmark path: '{bookmark_path}'")

    # Handle navigation commands
    if is_navigation:
        # Get the last used bookmark to determine the folder
        last_used_info = get_last_used_bookmark()
        if not last_used_info:
            print(f"❌ No last used bookmark found. Cannot navigate with '{bookmark_arg}'")
            return 1

        folder_name = last_used_info.get("folder_name")

        # Find the folder directory
        folder_dir = None
        active_folders = get_all_active_folders()
        for folder_path in active_folders:
            if os.path.basename(folder_path) == folder_name:
                folder_dir = folder_path
                break

        if not folder_dir:
            print(f"❌ Could not find folder directory for '{folder_name}'")
            return 1

        # Resolve the navigation command
        bookmark_path, bookmark_info = resolve_navigation_bookmark(bookmark_arg, folder_dir)
        if not bookmark_path:
            return 1

        # Set the folder directory for the rest of the workflow
        matched_bookmark_name = bookmark_path
    else:
        # Normal bookmark lookup
        matched_bookmark_name, bookmark_info = get_bookmark_info(bookmark_arg)

    if IS_DEBUG:
        print(f"🎯 Starting integrated runonce-redis workflow for bookmark: '{matched_bookmark_name}'")
        print(f"🔧 Redis dump directory: {REDIS_DUMP_DIR}")
        if is_save_last_redis:
            print(f"💾 Mode: Save current Redis state as redis_after.json")
        if is_save_updates:
            print(f"💾 Mode: Save redis state updates (before and after)")
        if is_use_preceding_bookmark:
            print(f"📋 Mode: Use preceding bookmark's redis_after.json as redis_before.json")
        if is_blank_slate:
            print(f"🆕 Mode: Use initial blank slate Redis state")
        if is_dry_run:
            print(f"📖 Mode: Load bookmark only (no main process)")
        if open_video:
            print(f"🎬 Mode: Open video in OBS (paused)")
        if is_super_dry_run:
            print(f"💾 Super dry run mode: Skipping all OBS operations")
        if is_no_obs:
            print(f"📷 No-OBS mode: Skipping all OBS operations")

    # Ensure Redis dump directory exists
    if not os.path.exists(REDIS_DUMP_DIR):
        if IS_DEBUG:
            print(f"📁 Creating Redis dump directory: {REDIS_DUMP_DIR}")
        os.makedirs(REDIS_DUMP_DIR)

    # Check if bookmark exists (with fuzzy matching)
    # This check is now redundant if we are resolving a navigation command
    # if not is_add_bookmark and not matched_bookmark_name:
    #     print(f"❌ Bookmark '{bookmark_arg}' not found. Use -a or --add to create it.")
    #     return 1
    # If the bookmark exists, continue as normal (do not return early)

    # If adding and bookmark exists, prompt for update
    if is_add_bookmark and matched_bookmark_name:
        if is_strict_equal(matched_bookmark_name, bookmark_arg):
            print(
                f"⚠️  Bookmark '{matched_bookmark_name}' already exists (partial match).")
            print("What would you like to do?")
            print("  1. Update before redis json")
            print("  2. Update after redis json")
            print("  3. Update both")
            print("  4. Cancel")
            while True:
                choice = input("Enter choice (1-4): ").strip()
                if choice == "1":
                    overwrite_redis_after = False
                    break
                elif choice == "2":
                    overwrite_redis_after = True
                    break
                elif choice == "3":
                    overwrite_redis_after = True
                    # We'll handle both updates in the workflow below
                    break
                elif choice == "4":
                    print("❌ Cancelled.")
                    return 1
                else:
                    print("❌ Invalid choice. Please enter 1-4.")
        else:
            matched_bookmark_name = None

    # Main workflow: Load existing bookmark OR create new one
    folder_dir = None  # Track the folder directory throughout the workflow


    ## MATCHED BOOKMARK ##


    if matched_bookmark_name:
        # EXISTING BOOKMARK WORKFLOW
        print(f"📖 Bookmark '{matched_bookmark_name}' exists - loading OBS state...")

        # Load the OBS bookmark using the matched name
        success = load_obs_bookmark_directly(matched_bookmark_name, bookmark_info)
        if not success:
            print("❌ Failed to load OBS bookmark")
            return 1

        # Update the bookmark name for the rest of the process
        bookmark_path = matched_bookmark_name

        # Find which folder this bookmark belongs to
        active_folders = get_all_active_folders()
        for folder_path in active_folders:
            print(f"🔍 Searching in folder: {folder_path}")  # ← add this here
            bookmark_path_full = os.path.join(folder_path, matched_bookmark_name)
            if os.path.exists(bookmark_path_full):
                folder_dir = folder_path
                folder_name = os.path.basename(folder_dir)
                print(f"🎯 Using folder: {folder_name}")

                if is_show_image:
                    screenshot_path = os.path.join(folder_dir, bookmark_path, "screenshot.jpg")
                    if os.path.exists(screenshot_path):
                        print(f"🖼️ Displaying screenshot in terminal: {screenshot_path}")
                        try:
                            pass
                            # result = subprocess.run(
                            #     ["imgcat", screenshot_path],
                            #     check=True,
                            #     capture_output=True,
                            #     text=True
                            # )
                            # print(result.stdout)
                            # TODO(): Add this.
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

        # Handle --use-preceding-bookmark flag for existing bookmark
        if is_use_preceding_bookmark:
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

        # Handle --blank-slate flag for existing bookmark
        elif is_blank_slate:
            print(f"🆕 Using initial blank slate Redis state for '{matched_bookmark_name}'...")
            if not copy_initial_redis_state(matched_bookmark_name, folder_dir):
                print("❌ Failed to copy initial Redis state")
                return 1
            # Update the path since we just created/copied the file
            redis_before_path = os.path.join(bookmark_dir, "redis_before.json")

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
            import shutil
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
                import shutil
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
                print(f"📸 Using existing screenshot: {matched_bookmark_name or bookmark_path}/screenshot.jpg")
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

                    import base64
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
                    print(f"📸 Screenshot saved to: {matched_bookmark_name or bookmark_path}/screenshot.jpg")

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


    ## NEW BOOKMARK ##


    else:
        print("🧪 DEBUG: Entering new bookmark workflow")
        # NEW BOOKMARK WORKFLOW (either no matches found OR user chose to create new)
        print(f"🆕 Bookmark '{bookmark_path}' doesn't exist - creating new bookmark...")

        # Handle folder:bookmark format
        if specified_folder_name:
            # Check if specified folder exists
            folder_dir = find_folder_by_name(specified_folder_name)
            if not folder_dir:
                print(f"📁 Folder '{specified_folder_name}' doesn't exist - creating it...")
                folder_dir = create_folder_with_name(specified_folder_name)
                if not folder_dir:
                    print(f"❌ Failed to create folder '{specified_folder_name}'")
                    return 1
            else:
                print(f"✅ Using existing folder: '{specified_folder_name}'")
        else:
            # Let user select which folder to create the bookmark in
            folder_dir = select_folder_for_new_bookmark(bookmark_path)
            if not folder_dir:
                print("❌ No folder selected, cancelling")
                return 1

        # Create bookmark directory
        bookmark_dir = os.path.join(folder_dir, bookmark_path)
        if not os.path.exists(bookmark_dir):
            os.makedirs(bookmark_dir)

        # Handle Redis state based on flags (skip if super dry run)
        if is_super_dry_run:
            print(f"💾 Super dry run mode: Skipping all Redis operations")
        elif is_blank_slate:
            # Handle --blank-slate flag for new bookmark
            print(f"🆕 Using initial blank slate Redis state for new bookmark '{bookmark_path}'...")
            if not copy_initial_redis_state(bookmark_path, folder_dir):
                print("❌ Failed to copy initial Redis state")
                return 1
        elif is_use_preceding_bookmark:
            # Handle --use-preceding-bookmark flag for new bookmark
            if source_bookmark_arg:
                print(f"📋 Using specified bookmark's Redis state for new bookmark '{bookmark_path}'...")
                if not copy_specific_bookmark_redis_state(source_bookmark_arg, bookmark_path, folder_dir):
                    print("❌ Failed to copy specified bookmark's Redis state")
                    return 1
            else:
                print(f"📋 Using preceding bookmark's Redis state for new bookmark '{bookmark_path}'...")
                if not copy_preceding_redis_state(bookmark_path, folder_dir):
                    print("❌ Failed to copy preceding Redis state")
                    return 1

            # If is_save_updates is enabled, save the pulled-in redis state as redis_before.json
            if is_save_updates:
                print(f"💾 Saving pulled-in Redis state as redis_before.json...")
                # The copy functions already create redis_before.json, so we just need to ensure it exists
                bookmark_dir = os.path.join(folder_dir, bookmark_path)
                redis_before_path = os.path.join(bookmark_dir, "redis_before.json")
                if os.path.exists(redis_before_path):
                    if IS_DEBUG:
                        print(f"📋 Redis before state saved: {redis_before_path}")
        else:
            # Normal flow - save current Redis state (skip if super dry run)
            if not is_super_dry_run:
                print(f"💾 Saving current Redis state for new bookmark '{bookmark_path}'...")
                if not run_redis_command(['export', 'bookmark_temp']):
                    print("⚠️ Failed to export current Redis state — continuing anyway for debug purposes")
                    # Don't return here — keep going so screenshot can run

                # Check if the export actually created the file
                temp_redis_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp.json")
                if IS_DEBUG:
                    print(f"🔍 Checking for exported Redis file at: {temp_redis_path}")

                if not os.path.exists(temp_redis_path):
                    print(f"❌ Expected Redis export file not found: {temp_redis_path}")
                    # List what files are actually in the redis dump directory
                    if os.path.exists(REDIS_DUMP_DIR):
                        files = os.listdir(REDIS_DUMP_DIR)
                        print(f"🔍 Files in Redis dump directory: {files}")

                # Move the Redis export to the bookmark directory
                if os.path.exists(temp_redis_path) and os.path.exists(bookmark_dir):
                    import shutil
                    final_path = os.path.join(bookmark_dir, "redis_before.json")
                    shutil.move(temp_redis_path, final_path)
                    print(f"💾 Saved Redis state to: {final_path}")

                    # Generate friendly version
                    try:
                        convert_redis_to_friendly(final_path)
                        if IS_DEBUG:
                            print(f"📋 Generated friendly Redis before")
                    except Exception as e:
                        print(f"⚠️  Could not generate friendly Redis before: {e}")
                else:
                    print(f"❌ Could not move Redis file - temp_path exists: {os.path.exists(temp_redis_path)}, bookmark_dir exists: {os.path.exists(bookmark_dir) if bookmark_dir else 'bookmark_dir is None'}")

        # Take screenshot directly using existing function (skip if no-obs mode)
        if is_no_obs:
            print(f"📷 No-OBS mode: Skipping screenshot capture")
        else:
            screenshot_path = os.path.join(bookmark_dir, "screenshot.jpg")
            try:
                cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)
                response = cl.send("GetSourceScreenshot", {
                    "sourceName": "Media Source",  # TODO: Make configurable if needed
                    "imageFormat": "png"
                })
                image_data = response.image_data
                if image_data.startswith("data:image/png;base64,"):
                    image_data = image_data.replace("data:image/png;base64,", "")

                import base64
                decoded_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(decoded_bytes))

                # Resize using SCREENSHOT_SAVE_SCALE
                width = int(image.width * SCREENSHOT_SAVE_SCALE)
                height = int(image.height * SCREENSHOT_SAVE_SCALE)
                resized_image = image.resize((width, height))

                # Save resized image (overwrite if it already exists)
                jpeg_path = os.path.join(bookmark_dir, "screenshot.jpg")
                resized_image.save(jpeg_path, format="JPEG", quality=85)


                if IS_DEBUG:
                    print(f"📋 Screenshot saved to: {screenshot_path}")
                print(f"📸 Screenshot saved to: {matched_bookmark_name or bookmark_path}/screenshot.jpg")

            except Exception as e:
                print(f"⚠️  Could not take screenshot: {e}")
                print(f"   Please ensure OBS is running and WebSocket server is enabled")


        # Get media source info and create bookmark metadata
        if is_no_obs:
            # Create minimal metadata without OBS info
            minimal_media_info = {
                'file_path': '',
                'video_filename': '',
                'timestamp': 0,
                'timestamp_formatted': '00:00:00'
            }
            create_bookmark_meta(bookmark_dir, bookmark_path, minimal_media_info, tags)
            print(f"📋 Created minimal bookmark metadata (no OBS info) with tags: {tags}")
        else:
            media_info = get_media_source_info()
            if media_info:
                if os.path.exists(bookmark_dir):
                    create_bookmark_meta(bookmark_dir, bookmark_path, media_info, tags)
                    print(f"📋 Created bookmark metadata with tags: {tags}")

        # Check if this is the first bookmark in the folder
        folder_bookmarks = load_bookmarks_from_folder(folder_dir)
        is_first_bookmark = len(folder_bookmarks) == 0

        # Create folder metadata for nested bookmarks
        if '/' in bookmark_path:
            path_parts = bookmark_path.split('/')
            current_path = folder_dir

            # Create metadata for each folder level (except the bookmark itself)
            for i, folder_name in enumerate(path_parts[:-1]):
                current_path = os.path.join(current_path, folder_name)

                # Create folder if it doesn't exist
                if not os.path.exists(current_path):
                    os.makedirs(current_path)

                # Create folder metadata if it doesn't exist
                folder_meta_file = os.path.join(current_path, "folder_meta.json")
                if not os.path.exists(folder_meta_file):
                    create_folder_meta(current_path, folder_name)
                    if IS_DEBUG:
                        print(f"📋 Created folder metadata for: {folder_name}")

            # Set description in the last directory of the bookmark path (not the folder root)
            last_dir_path = os.path.join(folder_dir, *path_parts[:-1])
            folder_meta_file = os.path.join(last_dir_path, "folder_meta.json")
            video_filename = ""
            if media_info and media_info.get('file_path'):
                video_filename = os.path.basename(media_info['file_path'])
            # Create or update folder meta with video filename as description
            if os.path.exists(folder_meta_file):
                try:
                    with open(folder_meta_file, 'r') as f:
                        meta_data = json.load(f)
                except json.JSONDecodeError:
                    meta_data = {}
            else:
                meta_data = {
                    "created_at": datetime.now().isoformat(),
                    "description": "",
                    "tags": []
                }
            if video_filename:
                meta_data["description"] = video_filename
            meta_data["last_modified"] = datetime.now().isoformat()
            try:
                with open(folder_meta_file, 'w') as f:
                    json.dump(meta_data, f, indent=2)
                if IS_DEBUG:
                    print(f"📋 Updated folder metadata for '{os.path.basename(last_dir_path)}' with video filename: {video_filename}")
            except Exception as e:
                print(f"❌ Error updating folder metadata: {e}")

    # Run the main process (unless dry run modes)
    if not is_dry_run and not is_super_dry_run:
        if IS_DEBUG:
            print(f"🚀 Running main process...")
        print('')
        if not run_main_process():
            print("❌ Main process failed")
            return 1

        # Wait for async processes to complete
        if IS_DEBUG:
            print(f"⏳ Waiting for async processes to complete...")
        time.sleep(ASYNC_WAIT_TIME)
    else:
        if is_super_dry_run:
            print(f"💾 Super dry run mode: Skipping main process execution")
        else:
            print(f"📖 Load-only mode: Skipping main process execution")

    # Check if redis_after.json already exists before saving final state (skip in dry run modes)
    should_save_redis_after = False  # Default value for dry run modes
    if not is_dry_run and not is_super_dry_run:
        redis_after_exists = False
        if folder_dir:
            bookmark_dir = os.path.join(folder_dir, bookmark_path)
            final_after_path = os.path.join(bookmark_dir, "redis_after.json")
            redis_after_exists = os.path.exists(final_after_path)

            if IS_DEBUG:
                print(f"🔍 Debug - redis_after_exists: {redis_after_exists}")
                print(f"🔍 Debug - is_save_updates: {is_save_updates}")
                print(f"🔍 Debug - final_after_path: {final_after_path}")

            # Save final Redis state if is_save_updates is enabled or if it doesn't exist
            should_save_redis_after = is_save_updates or not redis_after_exists

            if should_save_redis_after:
                if is_save_updates and redis_after_exists:
                    print(f"💾 Overwriting existing Redis after state...")
                else:
                    print(f"💾 Saving final Redis state...")

                if not run_redis_command(['export', 'bookmark_temp_after']):
                    print("❌ Failed to export final Redis state")
                    return 1

                # Move the final Redis export to the bookmark directory
                if folder_dir:
                    bookmark_dir = os.path.join(folder_dir, bookmark_path)
                    temp_redis_after_path = os.path.join(REDIS_DUMP_DIR, "bookmark_temp_after.json")

                    if IS_DEBUG:
                        print(f"🔍 Looking for final Redis export at: {temp_redis_after_path}")

                    if os.path.exists(temp_redis_after_path) and os.path.exists(bookmark_dir):
                        import shutil
                        final_after_path = os.path.join(bookmark_dir, "redis_after.json")
                        shutil.move(temp_redis_after_path, final_after_path)
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
                        # List what files are actually in the redis dump directory
                        if os.path.exists(REDIS_DUMP_DIR):
                            files = os.listdir(REDIS_DUMP_DIR)
                            print(f"🔍 Files in Redis dump directory: {files}")
    else:
        if is_super_dry_run:
            print(f"💾 Super dry run mode: Skipping final Redis state save")
        else:
            print(f"📖 Load-only mode: Skipping final Redis state save")

    # Save the last used bookmark at the end of successful operations
    if folder_dir:
        folder_name = os.path.basename(folder_dir)
        save_last_used_bookmark(folder_name, bookmark_path)
        if IS_DEBUG:
            print(f"📋 Saved last used bookmark: '{folder_name}:{bookmark_path}'")

        # Handle --preview flag
    if '--preview' in args or '-pv' in args:
        import platform

        screenshot_path = os.path.join(folder_dir, bookmark_path, "screenshot.jpg")
        if os.path.exists(screenshot_path):
            print(f"🖼️ Previewing screenshot: {screenshot_path}")
            if platform.system() == "Darwin":
                subprocess.run(["open", screenshot_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", screenshot_path])
            elif platform.system() == "Windows":
                os.startfile(screenshot_path)
            else:
                print(f"⚠️ Preview not supported on this platform.")
            return 0
        else:
            print(f"❌ No screenshot.jpg found for bookmark '{bookmark_path}'")
            return 1

    # Don't update folder metadata at the end - only update when actually creating new folders
    if IS_DEBUG and folder_dir:
        folder_name = os.path.basename(folder_dir)
        print(f"📋 Skipping final folder metadata update for '{folder_name}'")

    if is_super_dry_run:
        print(f"✅ Super dry run workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_path}'")
            print(f"   OBS bookmark loaded")
            print(f"   No Redis operations performed")
    elif is_dry_run:
        print(f"✅ Load-only workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_path}'")
            print(f"   OBS bookmark loaded")
            print(f"   Redis before: {bookmark_path}/redis_before.json")
    elif is_no_obs:
        print(f"✅ No-OBS workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_path}'")
            print(f"   No OBS operations performed")
            print(f"   No Redis operations performed")
    else:
        print(f"✅ Integrated workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_path}'")
            print(f"   OBS screenshot: {bookmark_path}/screenshot.jpg")
            print(f"   Redis before: {bookmark_path}/redis_before.json")
            if should_save_redis_after:
                print(f"   Redis after: {bookmark_path}/redis_after.json (new)")
            else:
                print(f"   Redis after: {bookmark_path}/redis_after.json (existing)")
    print('=' * 60)
    print('')



    # Print all folders and bookmarks with current one highlighted
    if folder_dir:
        current_folder_name = os.path.basename(folder_dir)
        print_all_folders_and_bookmarks(current_folder_name, bookmark_path, IS_PRINT_JUST_CURRENT_FOLDER_BOOKMARKS)


    return 0

if __name__ == "__main__":
    sys.exit(main())