import os
import sys
import subprocess
import traceback
from pprint import pprint
from app.utils.printing_utils import *
from app.consts.bookmarks_consts import IS_DEBUG, IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS
from app.bookmarks_print import print_all_live_directories_and_bookmarks
from app.flag_handlers import handle_matched_bookmark, handle_main_process, handle_save_redis_after_json, process_flags, CurrentRunSettings
from app.bookmarks.handle_create_bookmark import handle_create_bookmark_and_parent_dirs
from app.types import MatchedBookmarkObj
from app.bookmarks.matching.bookmark_matching import find_best_bookmark_match_or_create
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

    # Find the bookmark requested (either by name or reserved navigation command)
    matched_bookmark_obj = find_best_bookmark_match_or_create(
        cli_bookmark_string,
        current_run_settings_obj=current_run_settings_obj,
        is_prompt_user_for_selection=True
    )

    print_dev('===== matched_bookmark_obj:', 'green')
    pprint_dev(matched_bookmark_obj)

    if matched_bookmark_obj == 1 or matched_bookmark_obj == 0:
        print_color("❌ Error in find_best_bookmark_match_or_create - No matches found nor created", 'red')
        return matched_bookmark_obj


    # Handle matched bookmark
    if matched_bookmark_obj and not matched_bookmark_obj in ["create_new_bookmark", 1, 0]:
        print_dev('---- navigation/matched_bookmark_obj:', 'magenta')
        pprint_dev(matched_bookmark_obj)

        result = handle_matched_bookmark(
            matched_bookmark_obj,
            current_run_settings_obj
        )
        if isinstance(result, int):
            print_color("❌ Error in handle_matched_bookmark", 'red')
            return result  # an error code like 1 was returned

    elif not matched_bookmark_obj or matched_bookmark_obj in [1, 0]:
        print_color("❌ Bookmark not found and user did not create a new bookmark", 'red')
        return matched_bookmark_obj
    else:
        print_dev(
            '+++++ handle create bookmark but created matched_bookmark_obj:')
        print_dev(matched_bookmark_obj)

        # Creating Bookmark
        matched_bookmark_obj = handle_create_bookmark_and_parent_dirs(
            cli_bookmark_string,
            current_run_settings_obj
        )
        if isinstance(matched_bookmark_obj, int):
            print_color("❌ Error in handle_create_bookmark_and_parent_dirs", 'red')
            return matched_bookmark_obj




    # TODO(MFB): Move the handle_matched_bookmark to after create bookmark.

    # Run the main process (unless dry run modes)
    if not current_run_settings_obj["is_dry_run"] and not current_run_settings_obj["is_super_dry_run"]:
        print("🚀 Running main process...")
        result = handle_main_process(current_run_settings=current_run_settings_obj)
        if result != 0:
            print_color("❌ Main process failed", 'red')
            return result

    # Check if redis_after.json already exists before saving final state (skip in dry run modes)
    if not current_run_settings_obj["is_dry_run"] and not current_run_settings_obj["is_super_dry_run"]:
        should_save_redis_after = handle_save_redis_after_json(
            matched_bookmark_obj, current_run_settings_obj
        )
    else:
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
            print_color(f"❌ No screenshot.jpg found for bookmark '{matched_bookmark_obj['bookmark_tail_name']}'", 'red')
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
    exit_code = 0
    try:
        exit_code = main()
    except Exception:
        print_color('==== Exception: ====', 'red')
        traceback.print_exc()
        exit_code = 1
    finally:
        print_all_live_directories_and_bookmarks()
        sys.exit(exit_code)
