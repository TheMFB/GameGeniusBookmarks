from app.utils.printing_utils import *
from app.bookmarks.matching.matching_utils import token_match_bookmarks, fuzzy_match_bookmark_tokens, find_bookmarks_by_exact_trailing_path_parts
from app.bookmarks_consts import NAVIGATION_COMMANDS
from app.bookmarks.navigation.process_navigation import process_main_cli_arg_navigation
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.decorators import print_def_name
from app.utils.bookmark_utils import convert_exact_bookmark_path_to_dict
from app.bookmarks.bookmarks import get_all_live_bookmark_path_slash_rels



IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def find_best_bookmark_match(cli_bookmark_string) -> MatchedBookmarkObj | int | None:
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

    # Print the CLI bookmark string and all valid bookmark paths
    print('')
    print_dev('---- cli_bookmark_string_slash:')
    pprint_dev(cli_bookmark_string_slash)
    print('')
    print('')
    print('')
    print('')
    print('')
    print('')

    print_dev('---- all_live_bookmark_path_slash_rels:', 'cyan')
    pprint_dev(all_live_bookmark_path_slash_rels)
    print('')
    print('')
    print('')
    print('')
    print('')
    print('')

    # TODO(MFB): +++ Bookmark matching hierarchy +++

    print('---- find_best_bookmark_match - 1 : Exact Match (full path) ----')
    # 1. Exact match (full path)
    # Match: `GRANDPARENT:PARENT:BOOKMARK`
    if cli_bookmark_string_slash in all_live_bookmark_path_slash_rels:
        print_color(f'Found exact match! {cli_bookmark_string_slash}', 'green')
        # TODO(MFB): convert to bookmark object
        return convert_exact_bookmark_path_to_dict(
            cli_bookmark_string)

    # TODO(MFB): DONE UP TO HERE

    print('---- find_best_bookmark_match - 2 : Exact Match (without some parents) ----')
    # 2. Exact match (without some parents)
    # Match: `PARENT:BOOKMARK`
    trailing_matches = find_bookmarks_by_exact_trailing_path_parts(cli_bookmark_string, all_live_bookmark_path_slash_rels)
    print_dev('---- trailing_matches:', 'cyan')
    pprint_dev(trailing_matches)
    if trailing_matches:
        return trailing_matches

    print('---- find_best_bookmark_match - 3 : Substring Match (with full path) ----')
    # 3. Substring match (with full path)
    # Match: `GRAND:PAR:MARK`
    substring_matches = [p for p in all_live_bookmark_path_slash_rels if cli_bookmark_string in p]
    if substring_matches:
        return substring_matches

    print('---- find_best_bookmark_match - 4 : Substring Match (without some parents) ----')
    # 4. Substring match (without some parents)
    # Match: `PAR:MARK`
    substring_matches = [p for p in all_live_bookmark_path_slash_rels if ":".join(tail) in p]
    if substring_matches:
        return substring_matches

    print('---- find_best_bookmark_match - 5 : Tag/description match ----')
    # 5. Tag/description match
    # (Searches through all names, directories, tags and descriptions -- and does not take order into consideration)
    # Match: `comp:domination:boo`
    tag_matches = token_match_bookmarks(cli_bookmark_string, folder_dirs)
    if tag_matches:
        return tag_matches

    print('---- find_best_bookmark_match - 6 : Fuzzy Match ----')
    # 6. Fuzzy match across names, directories, tags and descriptions
    # Match: `GPARENT:DARENT:BOKKMARK`
    fuzzy_matches = fuzzy_match_bookmark_tokens(cli_bookmark_string)
    if fuzzy_matches:
        return fuzzy_matches


    return []


