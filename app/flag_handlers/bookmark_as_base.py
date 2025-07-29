from app.consts.bookmarks_consts import IS_DEBUG
from app.utils.decorators import print_def_name
from app.types.bookmark_types import NAVIGATION_COMMANDS
from app.bookmarks.matching.bookmark_matching import find_best_bookmark_match_or_create

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def find_bookmark_as_base_match(args):
    # Find the index of the use_preceding_bookmark flag
    cli_nav_arg_string = None
    preceding_flags = ["--use-preceding-bookmark", "-p", "--bookmark-base", "-bb"]
    for flag in preceding_flags:
        if flag in args:
            flag_index = args.index(flag)
            # Check if there's an argument after the flag that's not another flag
            if flag_index + 1 < len(args) and not args[flag_index + 1].startswith("-"):
                cli_nav_arg_string = args[flag_index + 1]
                if IS_DEBUG:
                    print(f"🔍 Found source bookmark argument: '{cli_nav_arg_string}'")
            break

    if IS_DEBUG:
        print(f"🔍 Debug - is_use_bookmark_as_base: {cli_nav_arg_string}")

    if not cli_nav_arg_string:
        return "previous"

    # Handle if the user has input a bookmark name as the nav arg
    if not cli_nav_arg_string in NAVIGATION_COMMANDS:
        matching_bookmark_obj = find_best_bookmark_match_or_create(
                                    cli_nav_arg_string,
                                    is_prompt_user_for_selection=True,
                                    is_prompt_user_for_create_bm_option=False,
                                    context="bookmark_template"
                                )
        if IS_DEBUG:
            print(
                f"🔍 Debug - find_bookmark_as_base_match matching_bookmark_obj: {matching_bookmark_obj}")
        if not matching_bookmark_obj:
            print(f"❌ No bookmark found for '{cli_nav_arg_string}'")
            return None
    else:
        return cli_nav_arg_string



    return cli_nav_arg_string