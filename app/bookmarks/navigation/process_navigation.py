"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
from pprint import pprint
from app.utils.printing_utils import print_color
from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.bookmarks import get_last_used_bookmark
from app.bookmarks.navigation import resolve_navigation_bookmark
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.bookmark_utils import convert_exact_bookmark_path_to_dict
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True



# TODO(MFB): Do we need to update this to say which context to use? I.E a bookmark parent / a user-defined bookmark or the last used bookmark?
@print_def_name(IS_PRINT_DEF_NAME)
def process_main_cli_arg_navigation(cli_bookmark_string) -> MatchedBookmarkObj | int | None:
    # Handle navigation commands

    # TODO(MFB): Need to check Navigation commands here.
    print_color('---- is_navigation ----', 'magenta')
    # Get the last used bookmark to determine the folder
    last_used_info = get_last_used_bookmark()
    if not last_used_info:
        print(
            f"❌ No last used bookmark found. Cannot navigate with '{cli_bookmark_string}'")
        return 1

    folder_name = last_used_info.get("rel_bookmark_dir")

    # Find the folder directory
    folder_dir = None
    valid_root_dir_names = get_all_valid_root_dir_names()
    for folder_path in valid_root_dir_names:
        # TODO(MFB): This is where we need to look for our navigation bugfix.
        if os.path.basename(folder_path) == folder_name:
            folder_dir = folder_path
            break

    if not folder_dir:
        print(f"❌ Could not find folder directory for '{folder_name}'")
        return 1

    # Resolve the navigation command
    matched_bookmark_path_rel, bookmark_info = resolve_navigation_bookmark(
        cli_bookmark_string, folder_dir)

    print('+++++ ? resolve_navigation_bookmark matched_bookmark_path_rel:')
    pprint(matched_bookmark_path_rel)

    if not matched_bookmark_path_rel:
        print(
            f"❌ No bookmark name found for'{matched_bookmark_path_rel}' '{cli_bookmark_string}'")
        return 1

    matched_bookmark_obj = convert_exact_bookmark_path_to_dict(matched_bookmark_path_rel)

    return {
        **matched_bookmark_obj,
        "bookmark_info": bookmark_info,
    }

