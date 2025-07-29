import os
from pprint import pprint
from app.utils.printing_utils import *
from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.bookmarks import get_last_used_bookmark
from app.bookmarks.navigation import resolve_navigation_bookmark_from_last_used
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.bookmark_utils import convert_exact_bookmark_path_to_bm_obj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def process_main_cli_arg_navigation(navigation_command) -> MatchedBookmarkObj | int | None:
    # Handle navigation commands

    # TODO(MFB): Need to check Navigation commands here.
    print_color('---- is_navigation ----', 'magenta')
    # Get the last used bookmark to determine the folder
    last_used_info = get_last_used_bookmark()
    if not last_used_info:
        print(
            f"❌ No last used bookmark found. Cannot navigate with '{navigation_command}'")
        return 1

    # Resolve the navigation command
    matched_bookmark_path_rel, bookmark_info = resolve_navigation_bookmark_from_last_used(
        navigation_command)

    print('+++++ resolve_navigation_bookmark_from_last_used matched_bookmark_path_rel:')
    pprint(matched_bookmark_path_rel)

    if not matched_bookmark_path_rel:
        print(
            f"❌ No bookmark name found for'{matched_bookmark_path_rel}' '{navigation_command}'")
        return 1

    matched_bookmark_obj = convert_exact_bookmark_path_to_bm_obj(matched_bookmark_path_rel)

    return {
        **matched_bookmark_obj,
        "bookmark_info": bookmark_info,
    }

