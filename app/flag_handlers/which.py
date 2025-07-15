from app.bookmarks import find_matching_bookmark

def which(args):
    which_flag = '--which' if '--which' in args else '-w'
    args_copy = args.copy()
    if which_flag in args_copy:
        args_copy.remove(which_flag)

    # If no bookmark search term is given, show error
    if not args_copy:
        print(f"❌ No bookmark name provided before {which_flag}")
        print("Usage: bm <bookmark_path> --which")
        return 1

    fuzzy_input = args_copy[0]

    # Perform fuzzy matching
    matches = find_matching_bookmark(fuzzy_input, "obs_bookmark_saves")

    # Filter out non-string matches (like metadata dicts)
    matches = [m for m in matches if isinstance(m, str)]

    if not matches:
        print(f"❌ No bookmarks matched '{fuzzy_input}'")
        return 1

    if len(matches) == 1:
        print("✅ Match found:")
        print(f"  • {matches[0]}")
        return 0

    # If multiple matches found
    print(f"⚠️  Multiple bookmarks matched '{fuzzy_input}':")
    for m in matches:
        print(f"  • {m}")
    print("Please be more specific.")
    return 1