"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
import sys
import subprocess
from pprint import pprint
# from networkx import to_dict_of_dicts

from app.utils.printing_utils import print_color
from app.bookmarks_consts import IS_DEBUG, IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS
from app.bookmarks_print import print_all_live_directories_and_bookmarks
from app.flag_handlers import handle_matched_bookmark, handle_bookmark_not_found, handle_main_process, handle_save_redis_after_json, process_flags, CurrentRunSettings
from app.types import MatchedBookmarkObj
from app.bookmarks.matching.bookmark_matching import find_best_bookmark_match
from app.bookmarks.last_used import save_last_used_bookmark

def main():
    matched_bookmark_obj: MatchedBookmarkObj | None = None

    args = sys.argv[1:]

    # Process Flags
    current_run_settings_obj: CurrentRunSettings | int = process_flags(args)
    if current_run_settings_obj == 0 or current_run_settings_obj == 1:
        # See if the user sent a "routed flag" that terminates the program after use
        return current_run_settings_obj

    # # Process CLI bookmark Input
    # cli_bookmark_dir, cli_bookmark_tail_name = parse_cli_bookmark_args(
    #     args_for_run_bookmarks)

    # Pull out the first string of the CLI args (the bookmark or reserved command string)
    cli_bookmark_string = args[0]
    matched_bookmark_obj = find_best_bookmark_match(cli_bookmark_string)

    print_color('===== matched_bookmark_obj:', 'green')
    pprint(matched_bookmark_obj)

    if matched_bookmark_obj == 1 or matched_bookmark_obj == 0:
        print(f"❌ Error in find_best_bookmark_match")
        return matched_bookmark_obj

    # TODO(MFB): +++ main.py +++ ?


    # Handle exact bookmark path match or navigation match
    if matched_bookmark_obj:
        print_color('---- navigation/matched_bookmark_obj:', 'magenta')
        pprint(matched_bookmark_obj)

        # TODO(MFB): create a matched_bookmark_obj, only pass that and the current_run_settings_obj into the function. Allow the function to unpack as necessary.
        result = handle_matched_bookmark(
            matched_bookmark_obj,
            current_run_settings_obj
        )
        if isinstance(result, int):
            print("❌ Error in handle_matched_bookmark")
            return result  # an error code like 1 was returned
    else:
        print_color('==== no matched_bookmark_obj ====', 'magenta')

        # Bookmark does not exist, and user intends to create it
        matched_bookmark_obj = handle_bookmark_not_found(
            cli_bookmark_dir,
            cli_bookmark_tail_name,
            current_run_settings_obj
        )

        print('+++++ handle_bookmark_not_found but created matched_bookmark_obj:')
        pprint(matched_bookmark_obj)

        if matched_bookmark_obj == 1 or matched_bookmark_obj == 0:
            print(f"❌ Error in handle_bookmark_not_found")
            return matched_bookmark_obj

    # Run the main process (unless dry run modes)
    if not current_run_settings_obj["is_dry_run"] and not current_run_settings_obj["is_super_dry_run"]:
        print("🚀 Running main process...")
        result = handle_main_process(current_run_settings=current_run_settings_obj)
        if result != 0:
            print("❌ Main process failed")
            return result

    # Check if redis_after.json already exists before saving final state (skip in dry run modes)
    if not current_run_settings_obj["is_dry_run"] and not current_run_settings_obj["is_super_dry_run"]:
        should_save_redis_after = handle_save_redis_after_json(
            matched_bookmark_obj, current_run_settings_obj
        )
    else:
        # TODO(KERCH): If we are in just dry run mode, we need to be saving the redis state. If we are in super dry run mode, we should not save the redis state.
        if current_run_settings_obj["is_super_dry_run"]:
            print(f"💾 Super dry run mode: Skipping final Redis state save")
        else:
            print(f"📖 Load-only mode: Skipping final Redis state save")

    # Save the last used bookmark at the end of successful operations
    if matched_bookmark_obj["bookmark_dir_slash_abs"]:
        print_color('saving last used bookmark', 'red')
        folder_name = os.path.basename(matched_bookmark_obj["bookmark_dir_slash_abs"])
        save_last_used_bookmark(matched_bookmark_obj)

    # Handle --preview flag
    if '--preview' in args or '-pv' in args:
        import platform

        screenshot_path = os.path.join(
            matched_bookmark_obj["bookmark_dir_slash_abs"], matched_bookmark_obj["bookmark_tail_name"], "screenshot.jpg")
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
            print(f"❌ No screenshot.jpg found for bookmark '{matched_bookmark_obj['bookmark_tail_name']}'")
            return 1

    # Don't update folder metadata at the end - only update when actually creating new folders
    if IS_DEBUG and matched_bookmark_obj["bookmark_dir_slash_abs"]:
        folder_name = os.path.basename(matched_bookmark_obj["bookmark_dir_slash_abs"])
        print(f"📋 Skipping final folder metadata update for '{folder_name}'")

    print(f"✅ Integrated workflow completed successfully!")
    print('=' * 60)
    print('')

    # Print all folders and bookmarks with current one highlighted
    if matched_bookmark_obj["bookmark_dir_slash_abs"]:
        print_all_live_directories_and_bookmarks(
            bookmark_obj=matched_bookmark_obj,
            is_print_just_current_directory_bookmarks=IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
