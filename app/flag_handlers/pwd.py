from app.bookmarks.bookmarks_print import print_all_live_directories_and_bookmarks

# from app.types.bookmark_types import CurrentRunSettings
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_pwd(_args: list[str]):
    # We'll grab the last-used bookmark as the "current" one
    # This keeps us aligned with how print_all_live_directories_and_bookmarks behaves
    print_all_live_directories_and_bookmarks(
        is_print_just_current_directory_bookmarks=True,
        current_run_settings_obj=None,
    )
    return 0
