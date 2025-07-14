
from app.bookmarks_folders import find_folder_by_name
from app.bookmarks_print import print_all_folders_and_bookmarks


def ls(args):
    # Remove -ls so we can check what came before it
    args_copy = args.copy()
    args_copy.remove('-ls') if '-ls' in args_copy else args_copy.remove('--ls')

    # If no folder path is provided: list everything
    if not args_copy:
        print_all_folders_and_bookmarks()
        return 0

    # If a folder path is provided, list only that folder
    folder_arg = args_copy[0]

    folder_path = find_folder_by_name(folder_arg), folder_arg

    if folder_path:
        from app.bookmarks_print import print_bookmarks_in_folder
        print_bookmarks_in_folder(folder_path)
        return 0
    else:
        print(f"❌ Folder '{folder_arg}' not found (no fuzzy matching allowed with -ls)")
        return 1
