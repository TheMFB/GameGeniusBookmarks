import sys
import traceback

from app.bookmarks.bookmarks_print import print_all_live_directories_and_bookmarks
from app.bookmarks.matching.bookmark_matching import find_best_bookmark_match_or_create
from app.bookmarks.matching.handle_matched_bookmark_post_processing import (
    handle_matched_bookmark_post_processing,
)
from app.bookmarks.matching.handle_matched_bookmark_pre_processing import (
    handle_matched_bookmark_pre_processing,
)
from app.flag_handlers.process_flags import process_flags
from app.run_main_process import handle_main_process
from app.types.bookmark_types import CurrentRunSettings
from app.utils.printing_utils import print_color


# TODO(MFB): There's got to be a better way to handle the return errors and exit codes.
def main():
    """
    This is the main entry point for the bookmark CLI. See --help for more information. README.md has more information.
    """

    # ARGS

    if not sys.argv or len(sys.argv) == 1:
        args = ["-h"]
    else:
        args = sys.argv[1:]

    # FLAGS

    current_run_settings_obj: CurrentRunSettings | int = process_flags(args)
    if isinstance(current_run_settings_obj, int):
        # If the user sent a "routed flag" that terminates the program after use
        return current_run_settings_obj

    # FIND/CREATE BOOKMARK

    matched_bookmark_obj = find_best_bookmark_match_or_create(
        args[0], # cli_bookmark_string
        current_run_settings_obj=current_run_settings_obj,
        is_prompt_user_for_selection=True
    )
    if isinstance(matched_bookmark_obj, int) or not matched_bookmark_obj:
        print_color("❌ Bookmark not found and user did not create a new bookmark", 'red')
        return matched_bookmark_obj
    if isinstance(matched_bookmark_obj, list):
        print_color("❌ Multiple bookmarks matched", 'red')
        return matched_bookmark_obj

    # HANDLE MATCHED BOOKMARK PRE-PROCESSING

    result = handle_matched_bookmark_pre_processing(
        matched_bookmark_obj,
        current_run_settings_obj
    )
    if isinstance(result, int):
        print_color("❌ Error in handle_matched_bookmark_pre_processing", 'red')
        return result


    # MAIN PROCESS

    result = handle_main_process(current_run_settings=current_run_settings_obj)
    if result == 1:
        print_color("❌ Main process failed", 'red')
        return result

    # HANDLE BOOKMARK POST-PROCESSING

    result = handle_matched_bookmark_post_processing(
        matched_bookmark_obj, current_run_settings_obj)
    if result == 1:
        print_color("❌ Error in handle_matched_bookmark_post_processing", 'red')
        return result

    # SUCCESS!

    print("✅ Integrated workflow completed successfully!")
    return 0


if __name__ == "__main__":
    exit_code = 0 # pylint: disable=C0103
    try:
        exit_code = main()
    except Exception:
        print_color('==== Exception: ====', 'red')
        traceback.print_exc()
        exit_code = 1 # pylint: disable=C0103
    finally:
        # Print all folders and bookmarks with current one highlighted
        print_all_live_directories_and_bookmarks()
        sys.exit(exit_code if isinstance(exit_code, (int, type(None))) else 1)
