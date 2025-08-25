import sys
import traceback

from app.bookmarks.bookmarks_print import print_all_live_directories_and_bookmarks
from app.bookmarks.last_used import save_last_used_bookmark
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
def main() -> tuple[int, CurrentRunSettings | None]:
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
        return current_run_settings_obj, None

    # FIND/CREATE BOOKMARK

    find_best_results = find_best_bookmark_match_or_create(
        args[0],  # cli_bookmark_string
        current_run_settings_obj=current_run_settings_obj,
        is_prompt_user_for_selection=True,
    )
    if isinstance(find_best_results, int) or not find_best_results:
        print_color(
            "❌ Bookmark not found and user did not create a new bookmark", "red"
        )
        return find_best_results, current_run_settings_obj  # type: ignore
    elif isinstance(find_best_results, list):
        print_color("❌ Multiple bookmarks matched", "red")
        return find_best_results, current_run_settings_obj  # type: ignore
    else:
        matched_bookmark_obj = find_best_results

    save_last_used_bookmark(matched_bookmark_obj)

    current_run_settings_obj["current_bookmark_obj"] = matched_bookmark_obj

    # HANDLE MATCHED BOOKMARK PRE-PROCESSING

    results = handle_matched_bookmark_pre_processing(
        matched_bookmark_obj, current_run_settings_obj
    )
    if results != 0:
        print_color("❌ Error in handle_matched_bookmark_pre_processing", "red")
        return results, current_run_settings_obj

    # MAIN PROCESS

    results = handle_main_process(
        matched_bookmark_obj,
        current_run_settings_obj,
    )
    if results == 1:
        print_color("❌ Main process failed", "red")
        return results, current_run_settings_obj

    # HANDLE BOOKMARK POST-PROCESSING

    results = handle_matched_bookmark_post_processing(
        matched_bookmark_obj, current_run_settings_obj
    )
    if results == 1:
        print_color("❌ Error in handle_matched_bookmark_post_processing", "red")
        return results, current_run_settings_obj

    # SUCCESS!

    print("✅ Integrated workflow completed successfully!")
    return (
        0,
        current_run_settings_obj,
    )


if __name__ == "__main__":
    exit_code = 0  # pylint: disable=C0103
    current_run_settings_obj = None
    try:
        (
            exit_code,
            current_run_settings_obj,
        ) = main()
    except Exception:
        print_color("==== Exception: ====", "red")
        traceback.print_exc()
        exit_code = 1  # pylint: disable=C0103
    finally:
        is_print_just_current_directory_bookmarks = bool(
            current_run_settings_obj.get("current_bookmark_obj", False)
            if current_run_settings_obj
            else False
        )

        # Print all folders and bookmarks with current one highlighted
        print_all_live_directories_and_bookmarks(
            is_print_just_current_directory_bookmarks=is_print_just_current_directory_bookmarks,
            current_run_settings_obj=current_run_settings_obj,
        )

    sys.exit(exit_code if isinstance(exit_code, (int, type(None))) else 1)  # type: ignore
