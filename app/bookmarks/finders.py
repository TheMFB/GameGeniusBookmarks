from pprint import pprint
import os

from app.bookmarks_consts import IS_DEBUG
from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.utils import print_color, split_path_into_array, print_def_name, memoize
from app.bookmarks_meta import load_bookmark_meta_from_rel, load_bookmark_meta_from_abs, load_folder_meta

IS_AGGREGATE_TAGS = False
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
@memoize
def load_bookmarks_from_folder(folder_dir_abs):
    matched_bookmarks = {}
    print_color('Loading bookmarks from folder: ' + folder_dir_abs, 'cyan')

    if not os.path.exists(folder_dir_abs):
        return matched_bookmarks

    root_name = os.path.basename(folder_dir_abs)

    def scan_for_bookmarks(directory, current_path=""):
        """Recursively scan directory for bookmark_meta.json files"""
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                # Check if this directory contains a bookmark_meta.json
                meta_file = os.path.join(item_path, "bookmark_meta.json")
                if os.path.exists(meta_file):
                    # This is a bookmark directory
                    # Use forward slashes for consistency across platforms
                    if current_path:
                        bookmark_key = f"{root_name}/{current_path}/{item}"
                    else:
                        bookmark_key = f"{root_name}/{item}"

                    # Use the new load_bookmark_meta function
                    bookmark_meta = load_bookmark_meta_from_rel(item_path)
                    if bookmark_meta:
                        matched_bookmarks[bookmark_key] = bookmark_meta
                    else:
                        if IS_DEBUG:
                            print(
                                f"⚠️  Could not load bookmark metadata from {item_path}")
                else:
                    # This is a regular directory, scan recursively
                    # Use forward slashes for consistency across platforms
                    if current_path:
                        new_path = f"{current_path}/{item}"
                    else:
                        new_path = item
                    scan_for_bookmarks(item_path, new_path)

    scan_for_bookmarks(folder_dir_abs)
    return matched_bookmarks


@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def get_all_valid_bookmarks_in_json_format():
    """Recursively scan all live folders and build a nested JSON structure with folder and bookmark tags/descriptions, including aggregated tags as 'tags'."""
    # TODO(MFB): Look into this, as this is likely a (relatively) VERY heavy operation.

    def scan_folder(folder_path):
        node = {}
        # Add folder meta if present
        folder_meta = load_folder_meta(folder_path)
        folder_tags = set()
        if folder_meta:
            folder_tags = set(folder_meta.get('tags', []))
            node['description'] = folder_meta.get('description', '')
            node['video_filename'] = folder_meta.get('video_filename', '')

        # List all items in this folder
        try:
            items = os.listdir(folder_path)
        except Exception:
            return node

        subfolders = {}

        for item in items:
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                # Recurse into subfolder
                subfolders[item] = scan_folder(item_path)
            elif item == "bookmark_meta.json":
                # This folder is a bookmark (leaf)
                bookmark_meta = load_bookmark_meta_from_abs(folder_path)
                node.update({
                    'tags': bookmark_meta.get('tags', []),
                    'description': bookmark_meta.get('description', ''),
                    'timestamp': bookmark_meta.get('timestamp_formatted', ''),
                    'video_filename': bookmark_meta.get('video_filename', ''),
                    'type': 'bookmark'
                })
                return node  # Do not process further, this is a bookmark

        # Attach subfolders to node
        for subfolder_name, subfolder_node in subfolders.items():
            node[subfolder_name] = subfolder_node

        # print('subfolders:')
        # pprint(subfolders)
        # print("")

        if IS_AGGREGATE_TAGS:
            # --- Tag aggregation logic ---
            # Collect all descendant bookmark tags
            all_descendant_tags = []
            for subfolder_node in subfolders.values():
                child_tags = set(subfolder_node.get('tags', []))
                if child_tags:
                    all_descendant_tags.append(child_tags)

            # Compute intersection for grouped tags
            grouped_tags = set.intersection(
                *all_descendant_tags) if all_descendant_tags else set()

            # Remove grouped_tags from children (so they are not repeated)
            for subfolder_node in subfolders.values():
                if 'tags' in subfolder_node:
                    subfolder_node['tags'] = list(
                        set(subfolder_node['tags']) - grouped_tags)

            # Combine folder's own tags and grouped tags, and uniquify
            all_tags = folder_tags.union(grouped_tags)
            node['tags'] = list(sorted(all_tags))

        return node

    all_bookmarks = {}
    for folder_path in get_all_valid_root_dir_names():
        folder_name = os.path.basename(folder_path)
        all_bookmarks[folder_name] = scan_folder(folder_path)
    return all_bookmarks


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
def is_bookmark_path_in_live_bookmarks_strict(cli_bookmark_path_rel):
    """
    Return exact match path if the normalized bookmark path matches query.
    Used during creation to avoid fuzzy fallbacks.
    """
    all_bookmarks_object = get_all_valid_bookmarks_in_json_format()
    pprint(all_bookmarks_object)

    if not all_bookmarks_object:
        return None

    return cli_bookmark_path_rel in all_bookmarks_object
