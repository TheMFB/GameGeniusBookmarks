import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import json
import io
import base64
from datetime import datetime
from PIL import Image
import obsws_python as obs  # or however you import OBS

from app.bookmarks_folders import (
    find_folder_by_name,
    create_folder_with_name,
    select_folder_for_new_bookmark,
    create_folder_meta,
)
from app.bookmarks import load_bookmarks_from_folder
from app.bookmarks_meta import create_bookmark_meta
from app.bookmarks_redis import (
    run_redis_command,
    copy_initial_redis_state,
    copy_preceding_redis_state,
    copy_specific_bookmark_redis_state,
)
from redis_friendly_converter import convert_file as convert_redis_to_friendly
from app.bookmarks_consts import REDIS_DUMP_DIR, IS_DEBUG, SCREENSHOT_SAVE_SCALE
from app.utils import get_media_source_info
from app.flag_handlers.save_obs_screenshot import save_obs_screenshot
from app.flag_handlers.save_redis_and_friendly_json import save_redis_and_friendly_json




def handle_bookmark_not_found(
    bookmark_name,
    specified_folder_path,
    is_super_dry_run,
    is_blank_slate,
    is_use_preceding_bookmark,
    is_save_updates,
    is_no_obs,
    tags,
    source_bookmark_arg
):

    ## NEW BOOKMARK ##
    print("🧪 DEBUG: Entering new bookmark workflow")
    print(f"🆕 Bookmark '{bookmark_name}' doesn't exist - creating new bookmark...")

    # Handle folder:bookmark format
    if specified_folder_path:
        # Check if specified folder exists
        folder_dir = find_folder_by_name(specified_folder_path)
        if not folder_dir:
            print(f"📁 Folder '{specified_folder_path}' doesn't exist - creating it...")
            folder_dir = create_folder_with_name(specified_folder_path)
            if not folder_dir:
                print(f"❌ Failed to create folder '{specified_folder_path}'")
                return 1
        else:
            print(f"✅ Using existing folder: '{specified_folder_path}'")
    else:
        # Let user select which folder to create the bookmark in
        folder_dir = select_folder_for_new_bookmark(bookmark_name)
        if not folder_dir:
            print("❌ No folder selected, cancelling")
            return 1

    # Create bookmark directory
    bookmark_dir = os.path.join(folder_dir, bookmark_name)
    if not os.path.exists(bookmark_dir):
        os.makedirs(bookmark_dir)

    # Handle Redis state based on flags (skip if super dry run)
    if is_super_dry_run:
        print(f"💾 Super dry run mode: Skipping all Redis operations")
    elif is_blank_slate:
        # Handle --blank-slate flag for new bookmark
        print(f"🆕 Using initial blank slate Redis state for new bookmark '{bookmark_name}'...")
        if not copy_initial_redis_state(bookmark_name, folder_dir):
            print("❌ Failed to copy initial Redis state")
            return 1
    elif is_use_preceding_bookmark:
        # Handle --use-preceding-bookmark flag for new bookmark
        if source_bookmark_arg:
            print(f"📋 Using specified bookmark's Redis state for new bookmark '{bookmark_name}'...")
            if not copy_specific_bookmark_redis_state(source_bookmark_arg, bookmark_name, folder_dir):
                print("❌ Failed to copy specified bookmark's Redis state")
                return 1
        else:
            print(f"📋 Using preceding bookmark's Redis state for new bookmark '{bookmark_name}'...")
            if not copy_preceding_redis_state(bookmark_name, folder_dir):
                print("❌ Failed to copy preceding Redis state")
                return 1

        # If is_save_updates is enabled, save the pulled-in redis state as redis_before.json
        if is_save_updates:
            print(f"💾 Saving pulled-in Redis state as redis_before.json...")
            # The copy functions already create redis_before.json, so we just need to ensure it exists
            bookmark_dir = os.path.join(folder_dir, bookmark_name)
            redis_before_path = os.path.join(bookmark_dir, "redis_before.json")
            if os.path.exists(redis_before_path):
                if IS_DEBUG:
                    print(f"📋 Redis before state saved: {redis_before_path}")


    # Normal flow - save current Redis state (skip if super dry run)
    if not is_super_dry_run:
        save_redis_and_friendly_json(bookmark_name, bookmark_dir)


    # Take screenshot directly using existing function (skip if no-obs mode)
    if is_no_obs:
        print(f"📷 No-OBS mode: Skipping screenshot capture")

    else:
        save_obs_screenshot(bookmark_dir, bookmark_name)

    # Get media source info and create bookmark metadata
    if is_no_obs:
        # Create minimal metadata without OBS info
        minimal_media_info = {
            'file_path': '',
            'video_filename': '',
            'timestamp': 0,
            'timestamp_formatted': '00:00:00'
        }
        create_bookmark_meta(bookmark_dir, bookmark_name, minimal_media_info, tags)
        print(f"📋 Created minimal bookmark metadata (no OBS info) with tags: {tags}")
    else:
        media_info = get_media_source_info()
        if media_info:
            if os.path.exists(bookmark_dir):
                create_bookmark_meta(bookmark_dir, bookmark_name, media_info, tags)
                print(f"📋 Created bookmark metadata with tags: {tags}")

    # Check if this is the first bookmark in the folder
    folder_bookmarks = load_bookmarks_from_folder(folder_dir)
    is_first_bookmark = len(folder_bookmarks) == 0

    # Create folder metadata for nested bookmarks
    if '/' in bookmark_name:
        path_parts = bookmark_name.split('/')
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

    return folder_dir
