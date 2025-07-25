import sys
import os
from pprint import pprint
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import json
from datetime import datetime

from app.bookmark_dir_processes import (
    find_bookmark_dir_by_name,
    create_dir_with_name,
    select_dir_for_new_bookmark,
    create_folder_meta,
)
from app.bookmarks_meta import create_bookmark_meta
from app.bookmarks_redis import copy_initial_redis_state
# copy_preceding_bookmark_redis_state, copy_specific_bookmark_redis_state,

from app.bookmarks_consts import IS_DEBUG
from app.utils import get_media_source_info, print_color, print_def_name, convert_exact_bookmark_path_to_dict
from app.flag_handlers.save_obs_screenshot import save_obs_screenshot
from app.flag_handlers.save_redis_and_friendly_json import save_redis_and_friendly_json
from app.types.bookmark_types import CurrentRunSettings

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_bookmark_not_found(
    cli_bookmark_dir: str,
    cli_bookmark_tail_name: str,
    current_run_settings_obj: CurrentRunSettings,
):
    """
    The bookmark was not found / we have opted to create a new bookmark.

    """

    print_color('---- bookmark_tail_name:', 'cyan')
    pprint(cli_bookmark_tail_name)
    print_color('---- cli_bookmark_dir:', 'cyan')
    pprint(cli_bookmark_dir)

    if not cli_bookmark_tail_name:
        print("❌ No bookmark name provided")
        return 1

    ## NEW BOOKMARK ##
    print(
        f"🆕 Bookmark '{cli_bookmark_tail_name}' doesn't exist - creating new bookmark...")

    # Handle folder:bookmark format
    if cli_bookmark_dir:
        print_color('---- cli_bookmark_dir:', 'cyan')
        pprint(cli_bookmark_dir)

        # Check if specified folder exists
        # TODO(MFB): Failing:
        print('++++ find_bookmark_dir_by_name')
        bookmark_dir = find_bookmark_dir_by_name(cli_bookmark_dir)
        print_color('---- 1 folder_dir found:', 'magenta')
        pprint(bookmark_dir)

        if not bookmark_dir:
            print(f"📁 Creating folder: '{cli_bookmark_dir}'")
            bookmark_dir = create_dir_with_name(cli_bookmark_dir)
            print_color('---- 2 folder_dir:', 'magenta')
            pprint(bookmark_dir)
            if not bookmark_dir:
                print(f"❌ Failed to create folder '{cli_bookmark_dir}'")
                return 1
        else:
            print(f"✅ Using existing folder: '{cli_bookmark_dir}'")

        print_color('handle_bookmark_not_found bookmark_dir:', 'red')
        pprint(bookmark_dir)
        print_color('handle_bookmark_not_found bookmark_tail_name:', 'red')
        pprint(cli_bookmark_tail_name)

        print(f"🆕 Creating new bookmark at: '{cli_bookmark_dir}'")

    else:
        # Let user select which folder to create the bookmark in
        folder_dir = select_dir_for_new_bookmark(cli_bookmark_tail_name)
        print_color('---- 3 folder_dir:', 'magenta')
        pprint(folder_dir)
        if not folder_dir:
            print("❌ No folder selected, cancelling")
            return 1

    # TODO(KERCH): +++ Somewhere around this file, we need to be re-creating bookmark obj with any found/updated information. Creating it here with cli does not make sense.

    print_color('---- cli_bookmark_dir:', 'cyan')
    pprint(cli_bookmark_dir)
    print_color('---- cli_bookmark_tail_name:', 'cyan')
    pprint(cli_bookmark_tail_name)

    # Create bookmark directory
    cli_bookmark_obj = convert_exact_bookmark_path_to_dict(
        cli_bookmark_dir, cli_bookmark_tail_name)

    bookmark_dir_abs = cli_bookmark_obj["bookmark_dir_slash_abs"]
    bookmark_path_slash_abs = cli_bookmark_obj["bookmark_path_slash_abs"]

    os.makedirs(bookmark_dir_abs, exist_ok=True)


    # Handle Redis state based on flags (skip if super dry run)
    # TODO(KERCH): If we are in just dry run mode, we need to be saving the redis state. If we are in super dry run mode, we should not save the redis state.
    if current_run_settings_obj["is_super_dry_run"]:
        print(f"💾 Super dry run mode: Skipping all Redis operations")
    elif current_run_settings_obj["is_blank_slate"]:
        # Handle --blank-slate flag for new bookmark
        print(
            f"🆕 Using initial blank slate Redis state for new bookmark '{cli_bookmark_tail_name}'...")
        if not copy_initial_redis_state(bookmark_dir_abs):
            print("❌ Failed to copy initial Redis state")
            return 1
    elif current_run_settings_obj["is_use_preceding_bookmark"]:
        # Handle --use-preceding-bookmark flag for new bookmark
        if current_run_settings_obj["cli_args_list"]:
            print(
                f"📋 Using specified bookmark's Redis state for new bookmark '{cli_bookmark_tail_name}'...")
            print_color("Not implemented!!", "red")
            # if not copy_specific_bookmark_redis_state(cli_args_list, bookmark_tail_name, folder_dir):
            #     print("❌ Failed to copy specified bookmark's Redis state")
            #     return 1
        else:
            print(
                f"📋 Using preceding bookmark's Redis state for new bookmark '{cli_bookmark_tail_name}'...")
            print_color("Not implemented!!", "red")
            # if not copy_preceding_bookmark_redis_state(bookmark_tail_name, folder_dir):
            #     print("❌ Failed to copy preceding Redis state")
            #     return 1

        # If is_save_updates is enabled, save the pulled-in redis state as redis_before.json
        if current_run_settings_obj["is_save_updates"]:
            print(f"💾 Saving pulled-in Redis state as redis_before.json...")
            # The copy functions already create redis_before.json, so we just need to ensure it exists
            bookmark_dir = os.path.join(folder_dir, cli_bookmark_tail_name)
            redis_before_path = os.path.join(bookmark_dir, "redis_before.json")
            if os.path.exists(redis_before_path):
                if IS_DEBUG:
                    print(f"📋 Redis before state saved: {redis_before_path}")

    # TODO(MFB): ++++++++ HERE ++++++++

    # Normal flow - save current Redis state (skip if super dry run)
    # TODO(KERCH): If we are in just dry run mode, we need to be saving the redis state. If we are in super dry run mode, we should not save the redis state.
    if not current_run_settings_obj["is_super_dry_run"]:
        save_redis_and_friendly_json(bookmark_path_slash_abs)


    # Get media source info and create bookmark metadata
    if current_run_settings_obj["is_no_obs"]:
        # Create minimal metadata without OBS info
        minimal_media_info = {
            'file_path': '',
            'video_filename': '',
            'timestamp': 0,
            'timestamp_formatted': '00:00:00'
        }
        create_bookmark_meta(bookmark_dir, cli_bookmark_tail_name, minimal_media_info, current_run_settings_obj["tags"])
        print(f"📋 Created minimal bookmark metadata (no OBS info) with tags: {current_run_settings_obj["tags"]}")
        print(f"📷 No-OBS mode: Skipping screenshot capture")

    else:
        media_info = get_media_source_info()
        if media_info:
            if os.path.exists(bookmark_dir):
                create_bookmark_meta(bookmark_dir, cli_bookmark_tail_name, media_info, current_run_settings_obj["tags"])
                # TODO(MFB): Need to check if the screenshot exists and if it does, don't save it again unless we have the update/save flag on.
                save_obs_screenshot(bookmark_path_slash_abs)

                print(f"📋 Created bookmark metadata with tags: {current_run_settings_obj["tags"]}")

                # ✅ Final confirmation message
                # Convert full bookmark path to colons (for CLI-style display)
                relative_path = os.path.relpath(bookmark_dir, folder_dir)
                normalized_path = relative_path.replace('/', ':')
                folder_name = os.path.basename(folder_dir)

                print(f"✅ Created new bookmark: {folder_name}:{normalized_path}")

    # Check if this is the first bookmark in the folder
    # TODO(MFB): Not sure why we have this?
    # folder_bookmarks = load_bookmarks_from_folder(folder_dir)
    # is_first_bookmark = len(folder_bookmarks) == 0

    # Create folder metadata for nested bookmarks
    # TODO(MFB): bookmark_tail_name should never have a slash in it.
    if '/' in cli_bookmark_tail_name:
        print_color("🧪 DEBUG: '/' in cli_bookmark_tail_name", "red")
        path_parts = cli_bookmark_tail_name.split('/')
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

    print_color('---- folder_dir:', 'red')
    bookmark_obj = convert_exact_bookmark_path_to_dict(folder_dir, cli_bookmark_tail_name)

    return bookmark_obj
