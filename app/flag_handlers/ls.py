import os
import json
from app.bookmarks_folders import find_folder_by_name
from app.bookmarks_print import print_all_folders_and_bookmarks
from app.bookmarks import token_match_bookmarks


def ls(args):
    # Remove -ls so we can check what came before it
    args_copy = args.copy()
    args_copy.remove('-ls') if '-ls' in args_copy else args_copy.remove('--ls')

    # Detect --json flag
    is_json = False
    if '--json' in args_copy:
        is_json = True
        args_copy.remove('--json')

    # If no folder path is provided: list everything
    if not args_copy:
        print_all_folders_and_bookmarks()
        return 0

    # If a folder path is provided, list only that folder
    folder_arg = ' '.join(args_copy).strip()
    print(f"🔍 Searching for tokens: {folder_arg}")

    folder_path = find_folder_by_name(folder_arg)

    if folder_path:
        from app.bookmarks_print import print_bookmarks_in_folder
        print_bookmarks_in_folder(folder_path)
        return 0
    else:
        # Fall back to which-style logic
        from app.bookmarks import find_matching_bookmark
        from app.bookmarks_folders import get_all_active_folders
        from app.utils import print_color

        all_folders = get_all_active_folders()
        all_matches = []

        for folder in all_folders:
            matched_paths = token_match_bookmarks(folder_arg, folder)
            print(f"📎 Matched in {folder}: {matched_paths}")
            for matched_path in matched_paths:
                folder_name = os.path.basename(folder)
                full_path = f"{folder_name}:{matched_path.replace('/', ':')}"
                all_matches.append(full_path)

        if is_json:
            print(json.dumps(all_matches, indent=2))
            return 0 if all_matches else 1
        else:
            if not all_matches:
                print(f"❌ No bookmarks matched '{folder_arg}'")
                return 1

            if len(all_matches) == 1:
                print("✅ Match found:")
                print(f"  • {all_matches[0]}")
                return 0

            print(f"⚠️  Multiple bookmarks matched '{folder_arg}':")
            for m in all_matches:
                print(f"  • {m}")
            print("Please be more specific.")
            return 1
