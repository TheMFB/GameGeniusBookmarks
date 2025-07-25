from app.bookmarks_consts import IS_DEBUG, OPTIONS_HELP
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def find_tags(args):
    tags = []

    # Find the index of the tags flag
    tags_flags = ["--tags", "-t"]
    for flag in tags_flags:
        if flag in args:
            flag_index = args.index(flag)
            # Collect all arguments after the flag until we hit another flag
            i = flag_index + 1
            while i < len(args) and not args[i].startswith("-"):
                tags.append(args[i])
                i += 1
            break

    if IS_DEBUG:
        print(f"🔍 tags: {tags}")

    return tags