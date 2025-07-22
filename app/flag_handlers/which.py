import os
import json
from app.bookmarks import find_matching_bookmark
from app.bookmarks_folders import parse_folder_bookmark_arg

def which(args):
    which_flag = '--which' if '--which' in args else '-w'
    args_copy = args.copy()

    # Detect --json flag
    is_json = False
    if '--json' in args_copy:
        is_json = True
        args_copy.remove('--json')

    if which_flag in args_copy:
        args_copy.remove(which_flag)

    if not args_copy:
        print(f"❌ No bookmark name provided before {which_flag}")
        print("Usage: bm <bookmark_path> --which")
        return 1

    specified_folder_path, fuzzy_input = parse_folder_bookmark_arg(args_copy[0])
    print(f"🎯 Specified folder: '{specified_folder_path}', bookmark path: '{fuzzy_input}'")

    matches = []

    if specified_folder_path:
        folder_path = os.path.join("obs_bookmark_saves", specified_folder_path)
        folder_matches = find_matching_bookmark(fuzzy_input, folder_path)
        if folder_matches:
            matches = [m for m in folder_matches if isinstance(m, str)]

    # Fallback to search entire tree
    if not matches:
        folder_matches = find_matching_bookmark(fuzzy_input, "obs_bookmark_saves")
        matches = [m for m in folder_matches if isinstance(m, str)]

    if not matches:
        print(f"❌ No bookmarks matched '{fuzzy_input}'")
        return 1

    if len(matches) == 1:
        match_path = matches[0]
        if match_path.startswith("obs_bookmark_saves/"):
            relative_match = match_path[len("obs_bookmark_saves/"):]
        else:
            relative_match = match_path

        if is_json:
            folder, *subpath = relative_match.split(os.sep)
            import json
            print(json.dumps({
                "folder": folder,
                "path": '/'.join(subpath)
            }))
        else:
            colon_path = relative_match.replace(os.sep, ":")
            print("✅ Match found:")
            print(f"  • {colon_path}")
        return 0



    print(f"⚠️  Multiple bookmarks matched '{fuzzy_input}':")
    for m in matches:
        print(f"  • {m}")
    print("Please be more specific.")
    return 1
