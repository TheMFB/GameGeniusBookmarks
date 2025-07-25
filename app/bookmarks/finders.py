from pprint import pprint
import os

from app.bookmarks_consts import IS_DEBUG, IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON
from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.utils import print_color, split_path_into_array, print_def_name, memoize
from app.bookmarks_meta import load_bookmark_meta_from_rel, load_bookmark_meta_from_abs, load_folder_meta

IS_AGGREGATE_TAGS = True
IS_PRINT_DEF_NAME = True

# Add this at the top-level of the file
HAS_PRINTED_ALL_BOOKMARKS_JSON = False

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

    def scan_for_bookmarks(dir, current_path=""):
        """Recursively scan dir for bookmark_meta.json files"""
        for item in os.listdir(dir):
            item_path = os.path.join(dir, item)
            if os.path.isdir(item_path):
                # Check if this dir contains a bookmark_meta.json
                meta_file = os.path.join(item_path, "bookmark_meta.json")
                if os.path.exists(meta_file):
                    # This is a bookmark dir
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
                    # This is a regular dir, scan recursively
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

        sub_dirs = {}

        for item in items:
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                # Recurse into subfolder
                sub_dirs[item] = scan_folder(item_path)
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

        # Attach sub_dirs to node
        for sub_dir_name, sub_dir_node in sub_dirs.items():
            node[sub_dir_name] = sub_dir_node

        if IS_AGGREGATE_TAGS:
            # --- Tag aggregation logic ---
            # Gather tags from all children (sub_dirs and bookmarks)
            child_tag_sets = []
            for sub_dir_node in sub_dirs.values():
                child_tags = set(sub_dir_node.get('tags', []))
                if child_tags:
                    child_tag_sets.append(child_tags)

            # Only hoist if there are children
            if child_tag_sets:
                grouped_tags = set.intersection(*child_tag_sets) if child_tag_sets else set()
            else:
                grouped_tags = set()

            # Remove grouped_tags from all children
            for sub_dir_node in sub_dirs.values():
                if 'tags' in sub_dir_node:
                    sub_dir_node['tags'] = list(set(sub_dir_node['tags']) - grouped_tags)

            # Combine folder's own tags and grouped tags, and uniquify
            all_tags = folder_tags.union(grouped_tags)
            if all_tags:
                node['tags'] = list(sorted(all_tags))
            elif 'tags' in node:
                # Remove empty tags list if present
                del node['tags']

        return node

    all_bookmarks = {}
    for folder_path in get_all_valid_root_dir_names():
        folder_name = os.path.basename(folder_path)
        all_bookmarks[folder_name] = scan_folder(folder_path)

    if IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON:
        global HAS_PRINTED_ALL_BOOKMARKS_JSON
        if not HAS_PRINTED_ALL_BOOKMARKS_JSON:
            print('++++ all_bookmarks json:')
            pprint(all_bookmarks)
            print('')
            HAS_PRINTED_ALL_BOOKMARKS_JSON = True

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
    print('++++ is_bookmark_path_in_live_bookmarks_strict all_bookmarks_object:')
    pprint(all_bookmarks_object)

    if not all_bookmarks_object:
        return None

    return cli_bookmark_path_rel in all_bookmarks_object
