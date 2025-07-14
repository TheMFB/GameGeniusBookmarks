"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
from pprint import pprint
import os
import sys
import subprocess
import time
import json
import obsws_python as obs
from datetime import datetime
from PIL import Image
import io


from app.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR, ASYNC_WAIT_TIME, OPTIONS_HELP, USAGE_HELP, IS_PRINT_JUST_CURRENT_FOLDER_BOOKMARKS
from app.bookmarks_folders import get_all_active_folders, parse_folder_bookmark_arg, create_new_folder, find_folder_by_name, create_folder_with_name, select_folder_for_new_bookmark, update_folder_last_bookmark
from app.bookmarks_redis import copy_preceding_redis_state, copy_specific_bookmark_redis_state, copy_initial_redis_state, run_redis_command
from app.bookmarks import get_bookmark_info, load_obs_bookmark_directly, load_bookmarks_from_folder, normalize_path, is_strict_equal, save_last_used_bookmark, get_last_used_bookmark_display, resolve_navigation_bookmark, get_last_used_bookmark
from app.bookmarks_print import print_all_folders_and_bookmarks
from app.bookmarks_meta import create_bookmark_meta, create_folder_meta, create_folder_meta
from app.utils import print_color, get_media_source_info
from redis_friendly_converter import convert_file as convert_redis_to_friendly

SCREENSHOT_SAVE_SCALE = 0.25  # Scale screenshots to 25% of original size

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

    # Print help/usage if no arguments or -h/--help is present
    if not args or '-h' in args or '--help' in args:
        print(OPTIONS_HELP)

        # Show last used bookmark if available
        last_used_display = get_last_used_bookmark_display()
        if last_used_display:
            print(f"\n Last used bookmark: {last_used_display}")

        print_all_folders_and_bookmarks()
        return 0

        # Handle -ls or --ls
    if '-ls' in args or '--ls' in args:
        # Remove -ls so we can check what came before it
        args_copy = args.copy()
        args_copy.remove('-ls') if '-ls' in args_copy else args_copy.remove('--ls')

        # If no folder path is provided: list everything
        if not args_copy:
            print_all_folders_and_bookmarks()
            return 0

        # If a folder path is provided, list only that folder
        folder_arg = args_copy[0]
        from app.bookmarks_print import print_bookmarks_in_folder

        folder_path = find_folder_by_name(folder_arg)
        if folder_path:
            print_bookmarks_in_folder(folder_path)
            return 0
        else:
            print(f"❌ Folder '{folder_arg}' not found (no fuzzy matching allowed with -ls)")
            return 1

    # Handle --which or -w (fuzzy bookmark match check)
    if '--which' in args or '-w' in args:
        which_flag = '--which' if '--which' in args else '-w'
        args_copy = args.copy()
        args_copy.remove(which_flag)

        # If no bookmark search term is given, show error
        if not args_copy:
            print(f"❌ No bookmark name provided before {which_flag}")
            print("Usage: bm <bookmark_path> --which")
            return 1

        fuzzy_input = args_copy[0]

        from app.bookmarks import find_matching_bookmark

        # Perform fuzzy matching
        matches = find_matching_bookmark(fuzzy_input, "obs_bookmark_saves")

        # Filter out non-string matches (like metadata dicts)
        matches = [m for m in matches if isinstance(m, str)]

        if not matches:
            print(f"❌ No bookmarks matched '{fuzzy_input}'")
            return 1

        if len(matches) == 1:
            print("✅ Match found:")
            print(f"  • {matches[0]}")
            return 0

        # If multiple matches found
        print(f"⚠️  Multiple bookmarks matched '{fuzzy_input}':")
        for m in matches:
            print(f"  • {m}")
        print("Please be more specific.")
        return 1


    bookmark_arg = args[0]

    # Check if this is a navigation command
    navigation_commands = ["next", "previous", "first", "last"]
    is_navigation = bookmark_arg in navigation_commands

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
    ]

    # Check for unsupported flags
    unsupported_flags = [arg for arg in args if arg.startswith("--") and arg not in supported_flags]
    if unsupported_flags:
        print(f"⚠️  Warning: Unsupported flags detected: {unsupported_flags}")
        print(OPTIONS_HELP)
        print()

    save_last_redis = "--save-last-redis" in args or "-s" in args
    save_updates = "--save-updates" in args or "-s" in args
    use_preceding_bookmark = "--use-preceding-bookmark" in args or "-p" in args
    blank_slate = "--blank-slate" in args or "-b" in args
    is_dry_run = "--dry-run" in args or "-d" in args
    is_super_dry_run = "--super-dry-run" in args or "-sd" in args
    is_no_obs = "--no-obs" in args  # ✅ FIXED this line

    if is_super_dry_run:
        print("💧 SUPER DRY RUN: Skipping all Redis and OBS integration.")
        print("💧 No state changes, screenshotting, or Docker commands will run.")
        return 0

    add_bookmark = "--add" in args or "-a" in args

    # Check for video opening flags
    open_video = "--open-video" in args or "-v" in args

    # Parse the source bookmark for --use-preceding-bookmark if specified
    source_bookmark_arg = None
    if use_preceding_bookmark:
        # Find the index of the use_preceding_bookmark flag
        preceding_flags = ["--use-preceding-bookmark", "-p"]
        for flag in preceding_flags:
            if flag in args:
                flag_index = args.index(flag)
                # Check if there's an argument after the flag that's not another flag
                if flag_index + 1 < len(args) and not args[flag_index + 1].startswith("-"):
                    source_bookmark_arg = args[flag_index + 1]
                    if IS_DEBUG:
                        print(f"🔍 Found source bookmark argument: '{source_bookmark_arg}'")
                break

    # Parse the video path for --open-video if specified
    video_path = None
    if open_video:
        # Find the index of the open_video flag
        video_flags = ["--open-video", "-v"]
        for flag in video_flags:
            if flag in args:
                flag_index = args.index(flag)
                # Check if there's an argument after the flag that's not another flag
                if flag_index + 1 < len(args) and not args[flag_index + 1].startswith("-"):
                    video_path = args[flag_index + 1]
                    if IS_DEBUG:
                        print(f"🔍 Found video path argument: '{video_path}'")
                break

    # Parse tags from command line
    tags = []
    if "--tags" in args or "-t" in args:
        # Find the index of the tags flag
        tags_flags = ["--tags", "-t"]
        for flag in tags_flags:
            if flag in args:
                flag_index = args.index(flag)
                # Collect all arguments after the flag until we hit another flag
                i = flag_index + 1
                while i < len(args) and not args[i].startswith("-"):
                    tags.append(args[i])
                    i += 1
                break

    if IS_DEBUG:
        print(f"🔍 Debug - Args: {args}")
        print(f"🔍 Debug - save_last_redis: {save_last_redis}")
        print(f"🔍 Debug - save_updates: {save_updates}")
        print(f"🔍 Debug - use_preceding_bookmark: {use_preceding_bookmark}")
        print(f"🔍 Debug - source_bookmark_arg: {source_bookmark_arg}")
        print(f"🔍 Debug - blank_slate: {blank_slate}")
        print(f"🔍 Debug - is_dry_run: {is_dry_run}")
        print(f"🔍 Debug - is_super_dry_run: {is_super_dry_run}")
        print(f"🔍 Debug - open_video: {open_video}")
        print(f"🔍 Debug - video_path: {video_path}")
        print(f"🔍 Debug - tags: {tags}")
        print(f"🔍 Debug - is_no_obs: {is_no_obs}")

    # Handle video opening mode
    if open_video:
        if not video_path:
            print(f"❌ Video path required for --open-video flag")
            print(OPTIONS_HELP)
            return 1

        print(f"🎬 Opening video in OBS: {video_path}")

        # Import the open_video_in_obs function
        from app.utils import open_video_in_obs

        if open_video_in_obs(video_path):
            print(f"✅ Video opened successfully!")
            return 0
        else:
            print(f"❌ Failed to open video in OBS")
            return 1

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
        folder_dir = folder_dir
        matched_bookmark_name = bookmark_path
    else:
        # Normal bookmark lookup
        matched_bookmark_name, bookmark_info = get_bookmark_info(bookmark_arg)

    if IS_DEBUG:
        print(f"🎯 Starting integrated runonce-redis workflow for bookmark: '{matched_bookmark_name}'")
        print(f"🔧 Redis dump directory: {REDIS_DUMP_DIR}")
        if save_last_redis:
            print(f"💾 Mode: Save current Redis state as redis_after.json")
        if save_updates:
            print(f"💾 Mode: Save redis state updates (before and after)")
        if use_preceding_bookmark:
            print(f"📋 Mode: Use preceding bookmark's redis_after.json as redis_before.json")
        if blank_slate:
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
    # if not add_bookmark and not matched_bookmark_name:
    #     print(f"❌ Bookmark '{bookmark_arg}' not found. Use -a or --add to create it.")
    #     return 1
    # If the bookmark exists, continue as normal (do not return early)

    # If adding and bookmark exists, prompt for update
    if add_bookmark and matched_bookmark_name:
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
            bookmark_path_full = os.path.join(folder_path, matched_bookmark_name)
            if os.path.exists(bookmark_path_full):
                folder_dir = folder_path
                folder_name = os.path.basename(folder_dir)
                print(f"🎯 Using folder: {folder_name}")
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
        if use_preceding_bookmark:
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

            # If save_updates is enabled, save the pulled-in redis state as redis_before.json
            if save_updates:
                print(f"💾 Saving pulled-in Redis state as redis_before.json...")
                # The copy functions already create redis_before.json, so we just need to ensure it exists
                if os.path.exists(redis_before_path):
                    if IS_DEBUG:
                        print(f"📋 Redis before state saved: {redis_before_path}")

            # Update the path since we just created/copied the file
            redis_before_path = os.path.join(bookmark_dir, "redis_before.json")

        # Handle --blank-slate flag for existing bookmark
        elif blank_slate:
            print(f"🆕 Using initial blank slate Redis state for '{matched_bookmark_name}'...")
            if not copy_initial_redis_state(matched_bookmark_name, folder_dir):
                print("❌ Failed to copy initial Redis state")
                return 1
            # Update the path since we just created/copied the file
            redis_before_path = os.path.join(bookmark_dir, "redis_before.json")

        # Handle Redis state based on flags (skip if super dry run)
        if is_super_dry_run:
            print(f"💾 Super dry run mode: Skipping all Redis operations")
        elif blank_slate:
            # Handle --blank-slate flag for existing bookmark
            print(f"🆕 Using initial blank slate Redis state for '{matched_bookmark_name}'...")
            if not copy_initial_redis_state(matched_bookmark_name, folder_dir):
                print("❌ Failed to copy initial Redis state")
                return 1
            # Update the path since we just created/copied the file
            redis_before_path = os.path.join(bookmark_dir, "redis_before.json")

        elif use_preceding_bookmark:
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

            # If save_updates is enabled, save the pulled-in redis state as redis_before.json
            if save_updates:
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

        # Take screenshot directly using existing function (skip if no-obs mode)
        print(f"🧪 DEBUG: is_no_obs={is_no_obs}, matched_bookmark_name={matched_bookmark_name}, bookmark_dir={bookmark_dir}")
        print("🧪 DEBUG: Reached screenshot check for new bookmark")
        if is_no_obs:
            print(f"📷 No-OBS mode: Skipping screenshot capture")
        else:
            screenshot_path = os.path.join(bookmark_dir, "screenshot.png")
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
                resized_image.save(screenshot_path)

                if IS_DEBUG:
                    print(f"📋 Screenshot saved to: {screenshot_path}")
                print(f"📸 Screenshot saved to: {matched_bookmark_name or bookmark_path}/screenshot.png")

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
        elif blank_slate:
            # Handle --blank-slate flag for new bookmark
            print(f"🆕 Using initial blank slate Redis state for new bookmark '{bookmark_path}'...")
            if not copy_initial_redis_state(bookmark_path, folder_dir):
                print("❌ Failed to copy initial Redis state")
                return 1
        elif use_preceding_bookmark:
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

            # If save_updates is enabled, save the pulled-in redis state as redis_before.json
            if save_updates:
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
            screenshot_path = os.path.join(bookmark_dir, "screenshot.png")
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
                resized_image.save(screenshot_path)

                if IS_DEBUG:
                    print(f"📋 Screenshot saved to: {screenshot_path}")
                print(f"📸 Screenshot saved to: {matched_bookmark_name or bookmark_path}/screenshot.png")

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
                print(f"🔍 Debug - save_updates: {save_updates}")
                print(f"🔍 Debug - final_after_path: {final_after_path}")

            # Save final Redis state if save_updates is enabled or if it doesn't exist
            should_save_redis_after = save_updates or not redis_after_exists

            if should_save_redis_after:
                if save_updates and redis_after_exists:
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
            print(f"   OBS screenshot: {bookmark_path}/screenshot.png")
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

