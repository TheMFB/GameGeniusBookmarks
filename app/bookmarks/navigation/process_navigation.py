from app.bookmarks.last_used import get_last_used_bookmark
from app.bookmarks.navigation.navigation import (
    resolve_navigation_bookmark_from_last_used,
)
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.decorators import print_def_name
from app.utils.printing_utils import print_color

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
    matched_bookmark_obj = resolve_navigation_bookmark_from_last_used(
        navigation_command)

    # TODO(MFB): Does this return with the bookmark_info? (resolve_navigation_bookmark_from_last_used used to return the bookmark_info)

    return matched_bookmark_obj
