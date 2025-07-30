from app.bookmarks import get_last_used_bookmark_display
from app.bookmarks_print import print_all_live_directories_and_bookmarks
from app.consts.bookmarks_consts import IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS
from app.consts.cli_consts import OPTIONS_HELP
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def handle_help(args=None):  # ← allow optional args
    print(OPTIONS_HELP)


    # Show last used bookmark if available
    last_used_display = get_last_used_bookmark_display()
    if last_used_display:
        print(f"\n Last used bookmark: {last_used_display}")

    print_all_live_directories_and_bookmarks(
        is_print_just_current_directory_bookmarks=IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS
    )