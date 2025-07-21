import os
from app.bookmarks import find_matching_bookmark
from app.bookmarks_folders import parse_folder_bookmark_arg

def which(args):
    which_flag = '--which' if '--which' in args else '-w'
    args_copy = args.copy()
    if which_flag in args_copy:
        args_copy.remove(which_flag)

    if not args_copy:
        print(f"❌ No bookmark name provided before {which_flag}")
        print("Usage: bm <bookmark_path> --which")
        return 1

    print("📛 [DEBUG] Running inside which.py")
    specified_folder_path, fuzzy_input = parse_folder_bookmark_arg(args_copy[0])

    # Only print once for clarity
    print(f"🎯 Specified folder: '{specified_folder_path}', bookmark path: '{fuzzy_input}'")


    matches = []

    if specified_folder_path:
        folder_path = os.path.join("obs_bookmark_saves", specified_folder_path.replace(":", "/"))
        folder_matches = find_matching_bookmark(fuzzy_input, folder_path)
        if folder_matches:
            matches = [m for m in folder_matches if isinstance(m, str)]

    # Fallback to search entire tree
    if not matches:
        folder_matches = find_matching_bookmark(fuzzy_input, "obs_bookmark_saves")

        print(f"🔍 Fallback matching in entire tree for: '{fuzzy_input}'")
        for match in folder_matches:
            print(f"   → Match candidate: {match}")

        matches = [m for m in folder_matches if isinstance(m, str)]

        print(f"🔍 Final string matches:")
        for m in matches:
            print(f"   • {m}")


    if not matches:
        print(f"❌ No bookmarks matched '{fuzzy_input}'")
        return 1

    if len(matches) == 1:
        match_path = matches[0]

        # Strip prefix to get relative path
        if match_path.startswith("obs_bookmark_saves/"):
            relative_path = match_path[len("obs_bookmark_saves/"):]
        else:
            relative_path = match_path

        # Reconstruct full colon path by combining specified folder and bookmark
        if specified_folder_path:
            folder_parts = specified_folder_path.strip(":").split(":")
        else:
            folder_parts = []

        bookmark_parts = relative_path.split(os.sep)

        full_colon_path = ":".join(folder_parts + bookmark_parts[-1:])

        print("✅ Match found:")
        print(f"  • {full_colon_path}")
        return 0


    print(f"⚠️  Multiple bookmarks matched '{fuzzy_input}':")
    for m in matches:
        print(f"  • {m}")
    print("Please be more specific.")
    return 1
