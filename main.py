"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
import sys
import subprocess
from pprint import pprint
# from networkx import to_dict_of_dicts

from app.utils import print_color, convert_bookmark_path_to_dict
from app.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR, IS_PRINT_JUST_CURRENT_FOLDER_BOOKMARKS
from app.bookmark_dir_processes import parse_cli_bookmark_args
from app.bookmarks import get_bookmark_info, save_last_used_bookmark, is_bookmark_path_in_live_bookmarks_strict
from app.bookmarks_print import print_all_folders_and_bookmarks
from app.flag_handlers import handle_matched_bookmark, handle_bookmark_not_found, handle_main_process, handle_redis_operations, process_flags, ProcessedFlags
from app.bookmarks.navigation import process_navigation, navigation_commands
from app.types import MatchedBookmarkObj

def main():
    matched_bookmark_obj: MatchedBookmarkObj | None = None
    # bookmark_tail_name = None

    args = sys.argv[1:]
    args_for_run_bookmarks = args[0]

    # Process Flags
    process_flags_obj: ProcessedFlags | int = process_flags(args)
    if process_flags_obj == 0 or process_flags_obj == 1:
        # See if the user sent a "routed flag" that terminates the program after use
        return process_flags_obj

    # Process CLI bookmark Input
    cli_bookmark_dir, bookmark_tail_name = parse_cli_bookmark_args(
        args_for_run_bookmarks)

    # CLI Bookmark Object
    cli_bookmark_obj = convert_bookmark_path_to_dict(cli_bookmark_dir, bookmark_tail_name)


    # Navigation
    matched_bookmark_obj = process_navigation(args_for_run_bookmarks)
    if matched_bookmark_obj == 0 or matched_bookmark_obj == 1:
        # If navigation failed, return the error code
        return matched_bookmark_obj


    # # TODO(MFB): Dafuq? - This will only look at the tail and then ask the user what to do...
    # # Normal bookmark lookup
    # matched_bookmark_path_rel, bookmark_info = get_bookmark_info(
    #     bookmark_tail_name)
    # print('+++++ get_bookmark_info matched_bookmark_path_rel:')
    # pprint(matched_bookmark_path_rel)


    # Check for exact bookmark path match
    if not matched_bookmark_obj and process_flags_obj["is_add_bookmark"] and cli_bookmark_obj["bookmark_path_colon_rel"]:
        print_color('---- is_add_bookmark and cli_bookmark_dir ----', 'magenta')

        if is_bookmark_path_in_live_bookmarks_strict(
                cli_bookmark_obj):
            # We have an exact match, prompt the user what to do with the Redis saves
            print(f"⚠️ Bookmark already exists: {cli_bookmark_obj["bookmark_dir_colon_rel"]}")
            print("What would you like to do?")
            print("  1. Load existing")
            print("  2. Overwrite before redis")
            print("  3. Overwrite after redis")
            print("  4. Overwrite both")
            print("  5. Cancel")
            while True:
                choice = input("Enter choice (1–5): ").strip()
                if choice == "1":
                    matched_bookmark_obj = get_bookmark_info(cli_bookmark_obj)
                    break
                elif choice == "2":
                    matched_bookmark_obj = cli_bookmark_obj
                    process_flags_obj["is_overwrite_redis_before"] = True
                    break
                elif choice == "3":
                    matched_bookmark_obj = cli_bookmark_obj
                    process_flags_obj["is_overwrite_redis_after"] = True
                    break
                elif choice == "4":
                    matched_bookmark_obj = cli_bookmark_obj
                    process_flags_obj["is_overwrite_redis_after"] = True
                    process_flags_obj["is_overwrite_redis_before"] = True
                    break
                elif choice == "5":
                    print("❌ Cancelled.")
                    return 1
                else:
                    print("❌ Invalid choice. Please enter 1–5.")

    # Handle exact bookmark path match or navigation match
    if matched_bookmark_obj:
        print_color('---- navigation/matched_bookmark_obj:', 'magenta')
        pprint(matched_bookmark_obj)

        # TODO(MFB): create a matched_bookmark_obj, only pass that and the process_flags_obj into the function. Allow the function to unpack as necessary.
        result = handle_matched_bookmark(
            matched_bookmark_obj,
            process_flags_obj["is_show_image"],
            process_flags_obj["is_no_obs"],
            process_flags_obj["is_super_dry_run"],
            process_flags_obj["is_blank_slate"],
            process_flags_obj["is_use_preceding_bookmark"],
            process_flags_obj["is_save_updates"],
            process_flags_obj["is_overwrite_redis_after"],
            process_flags_obj["tags"],
            process_flags_obj["cli_args_list"]
        )
        if isinstance(result, int):
            print("❌ Error in handle_matched_bookmark")
            return result  # an error code like 1 was returned
        folder_dir, bookmark_name = result

        print('+++++ handle_matched_bookmark folder_dir:')
        pprint(folder_dir)

        # ✅ Final confirmation for matched bookmarks
        relative_path = os.path.relpath(os.path.join(
            folder_dir, bookmark_name), folder_dir)
        normalized_path = relative_path.replace('/', ':')
        folder_name = os.path.basename(folder_dir)
        print(f"✅ Match found: {folder_name}:{normalized_path}")

    else:
        print_color('---- no matched_bookmark_obj ----', 'magenta')


        # Bookmark does not exist, and user intends to create it
        folder_dir = handle_bookmark_not_found(
            cli_bookmark_obj,
            process_flags_obj["is_super_dry_run"],
            process_flags_obj["is_blank_slate"],
            process_flags_obj["is_use_preceding_bookmark"],
            process_flags_obj["is_save_updates"],
            process_flags_obj["is_no_obs"],
            process_flags_obj["tags"],
            process_flags_obj["cli_args_list"]
        )

        print('+++++ handle_bookmark_not_found folder_dir:')
        pprint(folder_dir)

        if folder_dir == 1 or folder_dir == 0:
            print(f"❌ Error in handle_bookmark_not_found")
            return folder_dir

    # Run the main process (unless dry run modes)
    if not process_flags_obj["is_dry_run"] and not process_flags_obj["is_super_dry_run"]:
        print("🚀 Running main process...")
        result = handle_main_process()
        if result != 0:
            print("❌ Main process failed")
            return result

    # Check if redis_after.json already exists before saving final state (skip in dry run modes)
    should_save_redis_after = False
    if not process_flags_obj["is_dry_run"] and not process_flags_obj["is_super_dry_run"]:
        should_save_redis_after = handle_redis_operations(
            folder_dir, bookmark_tail_name, process_flags_obj["is_save_updates"]
        )
    else:
        if process_flags_obj["is_super_dry_run"]:
            print(f"💾 Super dry run mode: Skipping final Redis state save")
        else:
            print(f"📖 Load-only mode: Skipping final Redis state save")

    # Save the last used bookmark at the end of successful operations
    if folder_dir:
        print_color('---- folder_dir:', 'red')
        pprint(folder_dir)
        folder_name = os.path.basename(folder_dir)
        save_last_used_bookmark(folder_name, bookmark_name, bookmark_info)
        if IS_DEBUG:
            print(
                f"📋 Saved last used bookmark: '{folder_name}:{bookmark_name}'")

        # Handle --preview flag
    if '--preview' in args or '-pv' in args:
        import platform

        screenshot_path = os.path.join(
            folder_dir, bookmark_name, "screenshot.jpg")
        if os.path.exists(screenshot_path):
            print(f"🖼️ Previewing screenshot: {screenshot_path}")
            if platform.system() == "Darwin":
                subprocess.run(["open", screenshot_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", screenshot_path])
            # elif platform.system() == "Windows":
            #     os.startfile(screenshot_path)
            else:
                print(f"⚠️ Preview not supported on this platform.")
            return 0
        else:
            print(f"❌ No screenshot.jpg found for bookmark '{bookmark_name}'")
            return 1

    # Don't update folder metadata at the end - only update when actually creating new folders
    if IS_DEBUG and folder_dir:
        folder_name = os.path.basename(folder_dir)
        print(f"📋 Skipping final folder metadata update for '{folder_name}'")

    if process_flags_obj["is_super_dry_run"]:
        print(f"✅ Super dry run workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_name}'")
            print(f"   OBS bookmark loaded")
            print(f"   No Redis operations performed")
    elif process_flags_obj["is_dry_run"]:
        print(f"✅ Load-only workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_name}'")
            print(f"   OBS bookmark loaded")
            print(f"   Redis before: {bookmark_name}/redis_before.json")
    elif process_flags_obj["is_no_obs"]:
        print(f"✅ No-OBS workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_name}'")
            print(f"   No OBS operations performed")
            print(f"   No Redis operations performed")
    else:
        if IS_DEBUG:
            print(f"✅ Integrated workflow completed successfully!")
            print(f"   Bookmark: '{bookmark_name}'")
            print(f"   OBS screenshot: {bookmark_name}/screenshot.jpg")
            print(f"   Redis before: {bookmark_name}/redis_before.json")
            if should_save_redis_after:
                print(
                    f"   Redis after: {bookmark_name}/redis_after.json (new)")
            else:
                print(
                    f"   Redis after: {bookmark_name}/redis_after.json (existing)")
    print('=' * 60)
    print('')

    # Print all folders and bookmarks with current one highlighted
    if folder_dir:
        print_all_folders_and_bookmarks(
            current_folder_abs_path=folder_dir,
            current_bookmark_name=bookmark_name,
            current_bookmark_info=bookmark_info,
            is_print_just_current_folder_bookmarks=IS_PRINT_JUST_CURRENT_FOLDER_BOOKMARKS
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
