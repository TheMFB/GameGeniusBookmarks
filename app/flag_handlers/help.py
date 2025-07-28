
from app.bookmarks_consts import OPTIONS_HELP
from app.bookmarks import get_last_used_bookmark_display
from app.bookmarks_print import print_all_live_directories_and_bookmarks
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def handle_help(args=None):  # ← allow optional args
    print(OPTIONS_HELP)

    from app.bookmarks import get_last_used_bookmark_display
    from app.bookmarks_print import print_all_live_directories_and_bookmarks

    # Show last used bookmark if available
    last_used_display = get_last_used_bookmark_display()
    if last_used_display:
        print(f"\n Last used bookmark: {last_used_display}")

    print_all_live_directories_and_bookmarks()