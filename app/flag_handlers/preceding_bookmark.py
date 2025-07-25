from app.bookmarks_consts import IS_DEBUG
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def find_preceding_bookmark_args(args):
    # Find the index of the use_preceding_bookmark flag
    cli_args_list = None
    preceding_flags = ["--use-preceding-bookmark", "-p"]
    for flag in preceding_flags:
        if flag in args:
            flag_index = args.index(flag)
            # Check if there's an argument after the flag that's not another flag
            if flag_index + 1 < len(args) and not args[flag_index + 1].startswith("-"):
                cli_args_list = args[flag_index + 1]
                if IS_DEBUG:
                    print(f"🔍 Found source bookmark argument: '{cli_args_list}'")
            break

    if IS_DEBUG:
        print(f"🔍 Debug - is_use_preceding_bookmark: {cli_args_list}")

    return cli_args_list