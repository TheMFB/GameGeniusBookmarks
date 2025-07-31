from app.bookmarks.bookmarks_print import print_all_live_directories_and_bookmarks
from app.consts.bookmarks_consts import IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS
from app.consts.cli_consts import OPTIONS_HELP
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = False

@print_def_name(IS_PRINT_DEF_NAME)
def handle_help(_args=None):  # ← allow optional args
    print(OPTIONS_HELP)

    print_all_live_directories_and_bookmarks(
        is_print_just_current_directory_bookmarks=IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS
    )
