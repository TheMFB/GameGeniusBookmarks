from typing import List
from app.utils.printing_utils import *
from app.bookmarks.matching.matching_utils import find_bookmarks_by_substring_with_all_live_bm_path_parts, find_bookmarks_by_exact_trailing_live_bm_path_parts, handle_bookmark_matches, find_bookmarks_by_substring_with_trailing_live_bm_path_parts, find_exact_matches_by_bookmark_tokens, find_partial_substring_matches_by_bookmark_tokens
from app.bookmarks_consts import NAVIGATION_COMMANDS
from app.bookmarks.navigation.process_navigation import process_main_cli_arg_navigation
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.decorators import print_def_name
from app.utils.bookmark_utils import convert_exact_bookmark_path_to_dict
from app.bookmarks.bookmarks import get_all_live_bookmark_path_slash_rels



IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def find_best_bookmark_match(cli_bookmark_string, is_prompt_user_for_selection: bool = True) -> MatchedBookmarkObj | List[MatchedBookmarkObj] | int | None:
    """
    Example Target: `GRANDPARENT:PARENT:BOOKMARK -t comp domination`

    """
    print('---- find_best_bookmark_match - 0 : Reserved Command ----')
    # 0. Does the string match a reserved command?
    if cli_bookmark_string in NAVIGATION_COMMANDS:
        # TODO(MFB): Other than return bookmark, is there anything else with this one?
        return process_main_cli_arg_navigation(cli_bookmark_string)

    # Convert to slash-separated format for matching
    cli_bookmark_string_slash = cli_bookmark_string.replace(":", "/")

    # Get all valid bookmark paths in slash-separated format (relative)
    all_live_bookmark_path_slash_rels = get_all_live_bookmark_path_slash_rels()

    # TODO(MFB): For anything other than an exact match, even if there is a single match, we should prompt the user for selection (create new bookmark/cancel). We should also tell the user which stage the match got to.

    print('---- find_best_bookmark_match - 1 : Exact Match (full path) ----')
    # 1. Exact match (full path)
    # Match: `GRANDPARENT:PARENT:BOOKMARK`
    if cli_bookmark_string_slash in all_live_bookmark_path_slash_rels:
        print_color(f'Found exact match! {cli_bookmark_string_slash}', 'green')
        return handle_bookmark_matches([cli_bookmark_string], is_prompt_user_for_selection)

    print('---- find_best_bookmark_match - 2 : Exact Match (without some parents) ----')
    # 2. Exact match (without some parents)
    # Match: `PARENT:BOOKMARK`
    matches = find_bookmarks_by_exact_trailing_live_bm_path_parts(cli_bookmark_string, all_live_bookmark_path_slash_rels)
    if matches:
        return handle_bookmark_matches(matches, is_prompt_user_for_selection)

    print('---- find_best_bookmark_match - 3 : Substring Match (with full path) ----')
    # 3. Substring match (with full path)
    # Match: `GRAND:PAR:MARK`
    matches = find_bookmarks_by_substring_with_all_live_bm_path_parts(
        cli_bookmark_string, all_live_bookmark_path_slash_rels)
    if matches:
        return handle_bookmark_matches(matches, is_prompt_user_for_selection)

    print('---- find_best_bookmark_match - 4 : Substring Match (without some parents) ----')
    # 4. Substring match (without some parents)
    # Match: `PAR:MARK`
    matches = find_bookmarks_by_substring_with_trailing_live_bm_path_parts(
        cli_bookmark_string, all_live_bookmark_path_slash_rels)
    if matches:
        return handle_bookmark_matches(matches, is_prompt_user_for_selection)

    # TODO(MFB): DONE UP TO HERE
    print('---- find_best_bookmark_match - 5 : Tag/description match ----')
    # 5. Tag/description match
    # Searches through all names, directories, tags and descriptions -- and does not take order into consideration. Looks for exact matches.
    matches = find_exact_matches_by_bookmark_tokens(
        cli_bookmark_string, all_live_bookmark_path_slash_rels)
    if matches:
        return handle_bookmark_matches(matches, is_prompt_user_for_selection)

    print('---- find_best_bookmark_match - 6 : Tag/description match ----')
    # 6. Tag/description partial matches
    # Searches through all names, directories, tags and descriptions -- and does not take order into consideration. Looks for exact matches.
    matches = find_partial_substring_matches_by_bookmark_tokens(
        cli_bookmark_string, True )
    if matches:
        return handle_bookmark_matches(matches, is_prompt_user_for_selection)

    # TODO(MFB): Implement fuzzy matching
    # print('---- find_best_bookmark_match - 6 : Fuzzy Match ----')
    # # 6. Fuzzy match across names, directories, tags and descriptions
    # # Match: `GPARENT:DARENT:BOKKMARK`
    # fuzzy_matches = fuzzy_match_bookmark_tokens(cli_bookmark_string)
    # if fuzzy_matches:
    #     return fuzzy_matches


    return []


