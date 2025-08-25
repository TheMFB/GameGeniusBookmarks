from app.consts.bookmarks_consts import IS_DEBUG

IS_PRINT_DEF_NAME = True
DEFAULT_ALT_SOURCE_CLI_NAV_STRING = "previous"


def get_alt_source_cli_nav_string_from_args(args: list[str]) -> str | None:
    """
    This function is used to get the alt source cli nav string from the args.
    """
    # Find the index of the use_preceding_bookmark flag
    alt_source_cli_nav_string = DEFAULT_ALT_SOURCE_CLI_NAV_STRING
    preceding_flags = ["--use-preceding-bookmark", "-p", "--bookmark-alt-source", "-bs"]
    for flag in preceding_flags:
        if flag in args:
            flag_index = args.index(flag)
            # Check if there's an argument after the flag that's not another flag
            if flag_index + 1 < len(args) and not args[flag_index + 1].startswith("-"):
                alt_source_cli_nav_string = args[flag_index + 1]
                if IS_DEBUG:
                    print(
                        f"🔍 Found alt source bookmark argument: '{alt_source_cli_nav_string}'"
                    )
            break

    if IS_DEBUG:
        print(f"🔍 Debug - is_use_alt_source_bookmark: {alt_source_cli_nav_string}")

    return alt_source_cli_nav_string
