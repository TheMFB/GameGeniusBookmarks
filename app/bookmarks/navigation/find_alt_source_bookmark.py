from typing import cast

from app.bookmarks.matching.bookmark_matching import find_best_bookmark_match_or_create
from app.bookmarks.navigation.get_alt_source_cli_nav_string_from_args import (
    DEFAULT_ALT_SOURCE_CLI_NAV_STRING,
)
from app.bookmarks.navigation.navigation import (
    resolve_navigation_bookmark_from_current_matched_bookmark,
)
from app.consts.bookmarks_consts import IS_DEBUG
from app.types.bookmark_types import (
    NAVIGATION_COMMANDS,
    CurrentRunSettings,
    MatchedBookmarkObj,
    NavigationCommand,
)
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def find_alt_source_bookmark_match(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings
) -> MatchedBookmarkObj | int | None:
    """
    This function is used to find the alt source bookmark name match.
    """
    alt_source_cli_nav_string = current_run_settings_obj.get(
        "alt_source_cli_nav_string", None) or DEFAULT_ALT_SOURCE_CLI_NAV_STRING

    if IS_DEBUG:
        print(f"🔍 Debug - is_use_alt_source_bookmark: {alt_source_cli_nav_string}")

    if alt_source_cli_nav_string in NAVIGATION_COMMANDS:
        # Find the alt source bookmark object from the cli nav string
        alt_source_bookmark_obj = resolve_navigation_bookmark_from_current_matched_bookmark(
            matched_bookmark_obj,
            cast(NavigationCommand, alt_source_cli_nav_string)
        )
    else:
        # Handle if the user has input a bookmark name as the nav arg
        alt_source_bookmark_obj = find_best_bookmark_match_or_create(
                                    alt_source_cli_nav_string,
                                    current_run_settings_obj,
                                    is_prompt_user_for_selection=True,
                                    is_prompt_user_for_create_bm_option=False,
                                    context="bookmark_template"
                                )
        if IS_DEBUG:
            print(
                f"🔍 Debug - find_alt_source_bookmark_match matching_bookmark_obj: {alt_source_bookmark_obj}")
        if not alt_source_bookmark_obj:
            print(f"❌ No bookmark found for '{alt_source_cli_nav_string}'")
            return 1
        if isinstance(alt_source_bookmark_obj, int):
            print(f"❌ No bookmark found for '{alt_source_cli_nav_string}'")
            return 1
        if isinstance(alt_source_bookmark_obj, list):
            if len(alt_source_bookmark_obj) > 1:
                print(f"❌ Multiple bookmarks found for '{alt_source_cli_nav_string}'")
                return 1
            alt_source_bookmark_obj = alt_source_bookmark_obj[0]


    return alt_source_bookmark_obj
