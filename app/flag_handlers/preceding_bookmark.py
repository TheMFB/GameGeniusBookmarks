from app.bookmarks_consts import IS_DEBUG

def find_preceding_bookmark(args):
    # Find the index of the use_preceding_bookmark flag
    source_bookmark_arg = None
    preceding_flags = ["--use-preceding-bookmark", "-p"]
    for flag in preceding_flags:
        if flag in args:
            flag_index = args.index(flag)
            # Check if there's an argument after the flag that's not another flag
            if flag_index + 1 < len(args) and not args[flag_index + 1].startswith("-"):
                source_bookmark_arg = args[flag_index + 1]
                if IS_DEBUG:
                    print(f"🔍 Found source bookmark argument: '{source_bookmark_arg}'")
            break

    if IS_DEBUG:
        print(f"🔍 Debug - is_use_preceding_bookmark: {source_bookmark_arg}")

    return source_bookmark_arg