
from app.bookmarks_consts import OPTIONS_HELP
from app.bookmarks import get_last_used_bookmark_display
from app.bookmarks_print import print_all_folders_and_bookmarks


def help():
    print(OPTIONS_HELP)

    # Show last used bookmark if available
    last_used_display = get_last_used_bookmark_display()
    if last_used_display:
        print(f"\n Last used bookmark: {last_used_display}")

    print_all_folders_and_bookmarks()