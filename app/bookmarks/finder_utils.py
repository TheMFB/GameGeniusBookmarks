from pprint import pprint
import os
import re

from app.bookmarks_consts import IS_DEBUG, IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON
from app.bookmarks.bookmarks import load_bookmarks_from_folder, get_all_valid_bookmarks_in_json_format
from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.utils import print_color, split_path_into_array, print_def_name, memoize, does_path_exist_in_bookmarks
from app.bookmarks_meta import load_bookmark_meta_from_rel, load_bookmark_meta_from_abs, load_folder_meta
from app.utils.printing_utils import gg_print

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def stepwise_match(user_parts, all_saved_bookmark_paths):
    """Perform reverse stepwise matching of user_parts against bookmark paths."""
    # Preprocess all bookmarks into tokenized forms
    tokenized_bookmarks = [
        (path, split_path_into_array(path)) for path in all_saved_bookmark_paths
    ]

    # Start by finding matches on the last user input part
    depth = 1  # start from end of user input
    while True:
        matching = []
        for orig_path, tokens in tokenized_bookmarks:
            if len(tokens) < depth:
                continue
            if tokens[-depth].startswith(user_parts[-depth]):
                matching.append((orig_path, tokens))

        if not matching:
            return []  # no matches at this depth — fail
        if depth == len(user_parts):
            return [m[0] for m in matching]  # all user parts matched
        if len(matching) == 1:
            return [matching[0][0]]  # only one left — use it

        # More than one match, keep going deeper
        tokenized_bookmarks = matching
        depth += 1

@print_def_name(IS_PRINT_DEF_NAME)
def find_matching_bookmarks(bookmark_path_rel, root_dir_name):
    """
    Find all matching bookmarks using step-through logic and fallback fuzzy matching.
    Returns a list of (bookmark_path, bookmark_info) tuples.
    """
    all_bookmark_objects = load_bookmarks_from_folder(root_dir_name)
    if not all_bookmark_objects:
        return [(None, None)]

    all_saved_bookmark_paths = list(all_bookmark_objects.keys())
    matches = []

    # First try exact match
    if bookmark_path_rel in all_saved_bookmark_paths:
        if IS_DEBUG:
            print(f"🎯 Found exact bookmark_path_rel match: '{bookmark_path_rel}'")
        return (bookmark_path_rel, all_bookmark_objects[bookmark_path_rel])

    # Normalize user input
    user_input_parts = split_path_into_array(bookmark_path_rel)
    if IS_DEBUG:
        print(f"🔎 Normalized user input: {user_input_parts}")

    # Try stepwise matching
    stepwise_matches = stepwise_match(
        user_input_parts, all_saved_bookmark_paths)
    if stepwise_matches:
        for match in stepwise_matches:
            matches.append((match, all_bookmark_objects[match]))
        return matches

    # Fallback fuzzy match (with scoring)
    normalized_input = bookmark_path_rel.lower()
    scored_matches = []
    for path, info in all_bookmark_objects.items():
        path_lower = path.lower()
        tokens = set(path_lower.replace('/', ' ').replace('-', ' ').split())
        input_tokens = set(normalized_input.replace(
            '/', ' ').replace('-', ' ').split())
        score = len(tokens & input_tokens)
        if score > 0:
            scored_matches.append((score, path, info))
    if scored_matches:
        # Sort by score descending, then path
        scored_matches.sort(key=lambda x: (-x[0], x[1]))
        for _, path, info in scored_matches:
            matches.append((path, info))
        return matches

    # No matches found
    return [(None, None)]


@print_def_name(IS_PRINT_DEF_NAME)
def is_exact_bookmark_path_in_live_bookmarks(bookmark_obj):
    """
    Return exact match path if the normalized bookmark path matches query.
    Used during creation to avoid fuzzy fallbacks.
    """
    cli_bookmark_path_rel = bookmark_obj["bookmark_dir_colon_rel"]
    all_bookmarks_object = get_all_valid_bookmarks_in_json_format()

    if not all_bookmarks_object:
        return False

    return does_path_exist_in_bookmarks(all_bookmarks_object, cli_bookmark_path_rel)

# TODO(MFB): Bugfix

@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def token_match_bookmarks(query_string, folder_dir):
    """
    Returns a list of bookmark paths where all query tokens appear in the path.
    """
    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return []

    query_tokens = set(query_string.lower().replace(
        ":", " ").replace("/", " ").split())
    matches = []

    for path in all_bookmark_objects.keys():
        path_tokens = set(re.split(r"[-_/]", path.lower()))
        if query_tokens.issubset(path_tokens):
            matches.append(path)

    return matches

# TODO(MFB): Bugfix


# TODO(MFB): Not used.
@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def build_bookmark_token_map(include_tags_and_descriptions=True):
    """
    Return a dict mapping each bookmark path to a token set for matching.
    """
    from app.bookmark_dir_processes import get_all_valid_root_dir_names
    from app.bookmarks_meta import load_bookmark_meta_from_rel, load_folder_meta

    bookmark_token_map = {}
    valid_root_dir_names = get_all_valid_root_dir_names()

    for folder_path in valid_root_dir_names:
        folder_name = os.path.basename(folder_path)

        # Load folder-level metadata
        folder_meta = load_folder_meta(folder_path)
        folder_tags = folder_meta.get("tags", []) if include_tags_and_descriptions else []
        folder_description = folder_meta.get("description", "") if include_tags_and_descriptions else ""

        # Load bookmarks
        all_bookmark_objects = load_bookmarks_from_folder(folder_path)

        for bookmark_path, bookmark_data in all_bookmark_objects.items():
            full_key = f"{folder_name}:{bookmark_path}".replace("/", ":")  # normalized key

            tokens = set()

            # Split bookmark path into parts
            parts = bookmark_path.split('/')
            for part in parts:
                tokens.update(part.lower().split('-'))  # split kebab-case parts

            tokens.add(folder_name.lower())

            if include_tags_and_descriptions:
                # Add bookmark-level meta
                full_path = os.path.join(folder_path, bookmark_path)
                # TODO(MFB): I'm not sure this is rel...
                meta = load_bookmark_meta_from_rel(full_path)

                tokens.update([tag.lower() for tag in meta.get("tags", [])])

                if desc := meta.get("description"):
                    if folder_description:
                        tokens.update(folder_description.lower().split())


                # Also add folder-level tags/descriptions
                tokens.update([tag.lower() for tag in folder_tags])
                if folder_description:
                    tokens.update(folder_description.lower().split())


            bookmark_token_map[full_key] = {
                "tokens": tokens,
                "bookmark_name": os.path.basename(bookmark_path),
                "folder_name": folder_name,
            }

    return bookmark_token_map


@print_def_name(IS_PRINT_DEF_NAME)
def fuzzy_match_bookmark_tokens(query: str, include_tags_and_descriptions: bool = True, top_n: int = 5):
    token_map = build_bookmark_token_map(include_tags_and_descriptions)
    query_tokens = set(query.lower().split())

    scored_matches = []

    for key, data in token_map.items():
        overlap = data["tokens"].intersection(query_tokens)
        score = len(overlap)
        query_lower = query.lower()

    # Boost if bookmark name starts with query
    if data["bookmark_name"].lower().startswith(query_lower):
        score += 10  # strong boost

    # Boost if folder name starts with query
    if data["folder_name"].lower().startswith(query_lower):
        score += 5  # moderate boost

    if score > 0:
        print(f"{key} -> match score: {score}, overlap: {overlap}")
        scored_matches.append((score, key))

    # Sort by score descending, then alphabetically by key
    scored_matches.sort(key=lambda x: (-x[0], x[1]))

    top_matches = [match[1] for match in scored_matches[:top_n]]
    return top_matches

# TODO(MFB): Not used.
@print_def_name(IS_PRINT_DEF_NAME)
def interactive_fuzzy_lookup(query: str, top_n: int = 5):
    """
    Perform fuzzy matching and ask user to choose a bookmark from the top N matches.
    Returns the selected bookmark path, or None if cancelled.
    """
    matches = fuzzy_match_bookmark_tokens(query, top_n=top_n)

    if not matches:
        print("❌ No matches found.")
        return None

    print(f"🤔 Fuzzy matches for '{query}':")
    for idx, match in enumerate(matches, 1):
        print(f"  {idx}. {match}")
    print("  0. Cancel")

    while True:
        try:
            choice = input(f"Enter your choice (1-{len(matches)} or 0 to cancel): ").strip()
            if choice == "0":
                print("❌ Cancelled.")
                return None
            choice_num = int(choice)
            if 1 <= choice_num <= len(matches):
                selected = matches[choice_num - 1]
                print(f"✅ Selected: {selected}")
                return selected
            else:
                print(f"❌ Invalid input. Choose between 0 and {len(matches)}.")
        except ValueError:
            print("❌ Please enter a number.")
