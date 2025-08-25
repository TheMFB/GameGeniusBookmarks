from typing import List

from app.bookmarks.bookmarks import get_all_live_bookmark_path_slash_rels
from app.bookmarks.matching.matching_utils import (
    find_bookmarks_by_exact_trailing_live_bm_path_parts,
    find_bookmarks_by_substring_with_all_live_bm_path_parts,
    find_bookmarks_by_substring_with_trailing_live_bm_path_parts,
    find_exact_matches_by_bookmark_tokens,
    find_partial_substring_matches_by_bookmark_tokens,
    handle_bookmark_matches,
)
from app.bookmarks.navigation.process_navigation import process_main_cli_arg_navigation
from app.consts.bookmarks_consts import IS_DEBUG
from app.types.bookmark_types import (
    NAVIGATION_COMMANDS,
    CurrentRunSettings,
    MatchedBookmarkObj,
)
from app.utils.decorators import print_def_name
from app.utils.printing_utils import print_color

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def find_best_bookmark_match_or_create(
    cli_bookmark_string: str,
    current_run_settings_obj: CurrentRunSettings | None = None,
    is_prompt_user_for_selection: bool = True,
    is_prompt_user_for_create_bm_option: bool = True,
    context: str | None = None,
) -> MatchedBookmarkObj | List[MatchedBookmarkObj] | int | None:
    """
    Example Target: `GRANDPARENT:PARENT:BOOKMARK -t comp domination`

    """
    if IS_DEBUG:
        print("🧪 DEBUG: Entered find_best_bookmark_match_or_create")
        print("🧪 DEBUG: Incoming cli_bookmark_string =", cli_bookmark_string)
        print("🧪 DEBUG: NAVIGATION_COMMANDS =", NAVIGATION_COMMANDS)
        print("🧪 DEBUG: Incoming cli_bookmark_string =", cli_bookmark_string)
    # 1. Does the string match a reserved command?
    if cli_bookmark_string in NAVIGATION_COMMANDS:
        # TODO(MFB): Other than return bookmark, is there anything else with this one?
        return process_main_cli_arg_navigation(cli_bookmark_string)

    # Convert to slash-separated format for matching
    cli_bookmark_string_slash = cli_bookmark_string.replace(":", "/")

    # Get all valid bookmark paths in slash-separated format (relative)
    all_live_bookmark_path_slash_rels = get_all_live_bookmark_path_slash_rels()

    # TODO(KERCH): For anything other than an exact match, even if there is a single match, we should prompt the user for selection (create new bookmark/cancel). We should also tell the user which stage the match got to.

    # TODO(): Pull all of these into their own functions to clean up the code and be able to more easily show documentation for each.

    # 2. Exact match (full path)
    # Match: `GRANDPARENT:PARENT:BOOKMARK`
    if cli_bookmark_string_slash in all_live_bookmark_path_slash_rels:
        print_color(f"Found exact match! {cli_bookmark_string_slash}", "green")
        return handle_bookmark_matches(
            cli_bookmark_string,
            [cli_bookmark_string],
            current_run_settings_obj,
            is_prompt_user_for_selection=False,
            is_prompt_user_for_create_bm_option=False,
            context=context,
        )

    # 3. Exact match (without some parents)
    # Match: `PARENT:BOOKMARK`
    matches: list[str] = find_bookmarks_by_exact_trailing_live_bm_path_parts(
        cli_bookmark_string, all_live_bookmark_path_slash_rels
    )
    if matches:
        return handle_bookmark_matches(
            cli_bookmark_string,
            matches,
            current_run_settings_obj,
            is_prompt_user_for_selection,
            is_prompt_user_for_create_bm_option=is_prompt_user_for_create_bm_option,
            context=context,
        )

    # 4. Substring match (with full path)
    # Match: `GRAND:PAR:MARK`
    matches: list[str] = find_bookmarks_by_substring_with_all_live_bm_path_parts(
        cli_bookmark_string, all_live_bookmark_path_slash_rels
    )
    if matches:
        return handle_bookmark_matches(
            cli_bookmark_string,
            matches,
            current_run_settings_obj,
            is_prompt_user_for_selection,
            is_prompt_user_for_create_bm_option=is_prompt_user_for_create_bm_option,
            context=context,
        )

    # 5. Substring match (without some parents)
    # Match: `PAR:MARK`
    matches: list[str] = find_bookmarks_by_substring_with_trailing_live_bm_path_parts(
        cli_bookmark_string, all_live_bookmark_path_slash_rels
    )
    if matches:
        return handle_bookmark_matches(
            cli_bookmark_string,
            matches,
            current_run_settings_obj,
            is_prompt_user_for_selection,
            is_prompt_user_for_create_bm_option=is_prompt_user_for_create_bm_option,
            context=context,
        )

    # 6. Tag/description match
    # Searches through all names, directories, tags and descriptions -- and does not take order into consideration. Looks for exact matches.
    matches: list[str] = find_exact_matches_by_bookmark_tokens(
        cli_bookmark_string, include_tags_and_descriptions=True
    )
    if matches:
        return handle_bookmark_matches(
            cli_bookmark_string,
            matches,
            current_run_settings_obj,
            is_prompt_user_for_selection,
            is_prompt_user_for_create_bm_option=is_prompt_user_for_create_bm_option,
            context=context,
        )

    # 7. Tag/description partial matches
    # Searches through all names, directories, tags and descriptions -- and does not take order into consideration. Looks for exact matches.
    matches: list[str] = find_partial_substring_matches_by_bookmark_tokens(
        cli_bookmark_string, True
    )
    if matches:
        return handle_bookmark_matches(
            cli_bookmark_string,
            matches,
            current_run_settings_obj,
            is_prompt_user_for_selection,
            is_prompt_user_for_create_bm_option=is_prompt_user_for_create_bm_option,
            context=context,
        )

    # TODO(MFB): Implement fuzzy matching
    # # 8. Fuzzy match across names, directories, tags and descriptions

    # X. Handle no matches - prompt to create new bookmark
    if is_prompt_user_for_selection:
        return handle_bookmark_matches(
            cli_bookmark_string,
            [],
            current_run_settings_obj,
            is_prompt_user_for_selection,
            is_prompt_user_for_create_bm_option=is_prompt_user_for_create_bm_option,
            context=context,
        )
    if IS_DEBUG:
        print("🧪 DEBUG: Returning None — no match found.")

    return 1
