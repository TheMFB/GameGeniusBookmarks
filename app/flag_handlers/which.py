from pprint import pprint
from app.bookmarks.matching.bookmark_matching import find_best_bookmark_match_or_create
from app.bookmark_dir_processes import parse_cli_bookmark_args
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def handle_which(args):
    which_flag = '--which' if '--which' in args else '-w'
    args_copy = args.copy()

    # Detect --json flag
    is_json = False
    if '--json' in args_copy:
        is_json = True
        args_copy.remove('--json')

    if which_flag in args_copy:
        args_copy.remove(which_flag)

    if not args_copy:
        print(f"❌ No bookmark name provided before {which_flag}")
        print("Usage: bm <bookmark_path> --which")
        return 1

    cli_bookmark_string = parse_cli_bookmark_args(args_copy[0])
    if not cli_bookmark_string:
        print(f"❌ No bookmark name provided before {which_flag}")
        print("Usage: bm <bookmark_path> --which")
        return 1

    bookmark_obj_matches = find_best_bookmark_match_or_create(
        cli_bookmark_string, is_prompt_user_for_selection=False)

    if not bookmark_obj_matches:
        print(f"❌ No bookmarks matched for '{cli_bookmark_string}'")
        return 1

    if len(bookmark_obj_matches) == 1:
        bookmark_obj_match = bookmark_obj_matches[0]
        if is_json:
            pprint(bookmark_obj_match)
        else:
            print("✅ Match found:")
            print(f"  • {bookmark_obj_match['bookmark_path_colon_rel']}")
        return 0

    print(f"⚠️  Multiple bookmarks matched for '{cli_bookmark_string}':")
    if is_json:
        pprint(bookmark_obj_matches)
    else:
        for bookmark_obj_match in bookmark_obj_matches:
            print(f"  • {bookmark_obj_match['bookmark_path_colon_rel']}")
    return 1
