"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
from math import log
import os
import re
from pprint import pprint
import json
import obsws_python as obs
from datetime import datetime

from app.bookmarks_consts import IS_DEBUG
from app.bookmarks_folders import get_all_valid_root_dir_names
from app.utils import print_color, split_path_into_array, print_def_name, memoize
from app.videos import construct_full_video_file_path
from app.bookmarks_meta import load_bookmark_meta_from_rel, load_bookmark_meta_from_abs

IS_AGGREGATE_TAGS = False
IS_PRINT_DEF_NAME = True


# TODO(KERCH): Cache results of this function.


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
                            print(f"⚠️  Could not load bookmark metadata from {item_path}")
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


def load_folder_meta(folder_path):
    """Load folder metadata from folder_meta.json"""
    folder_meta_path = os.path.join(folder_path, "folder_meta.json")
    if os.path.exists(folder_meta_path):
        with open(folder_meta_path, 'r') as f:
            return json.load(f)
    return None



@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def get_all_bookmarks_in_json_format():
    """Recursively scan all active folders and build a nested JSON structure with folder and bookmark tags/descriptions, including aggregated tags as 'tags'."""
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
            grouped_tags = set.intersection(*all_descendant_tags) if all_descendant_tags else set()

            # Remove grouped_tags from children (so they are not repeated)
            for subfolder_node in subfolders.values():
                if 'tags' in subfolder_node:
                    subfolder_node['tags'] = list(set(subfolder_node['tags']) - grouped_tags)

            # Combine folder's own tags and grouped tags, and uniquify
            all_tags = folder_tags.union(grouped_tags)
            node['tags'] = list(sorted(all_tags))

        return node

    all_bookmarks = {}
    for folder_path in get_all_valid_root_dir_names():
        folder_name = os.path.basename(folder_path)
        all_bookmarks[folder_name] = scan_folder(folder_path)
    return all_bookmarks


def is_strict_equal(path1, path2):
    """Check if two bookmark paths are strictly equal after normalization."""
    normalized1 = '/'.join(split_path_into_array(path1))
    normalized2 = '/'.join(split_path_into_array(path2))
    return normalized1 == normalized2


@print_def_name(IS_PRINT_DEF_NAME)
def find_matching_bookmark(bookmark_path_rel, root_dir_name):
    """
    Find all matching bookmarks using step-through logic and fallback fuzzy matching.
    Returns a list of (bookmark_path, bookmark_info) tuples.
    """
    all_bookmark_objects = load_bookmarks_from_folder(root_dir_name)
    if not all_bookmark_objects:
        return []

    all_saved_bookmark_paths = list(all_bookmark_objects.keys())
    matches = []

    # First try exact match
    if bookmark_path_rel in all_saved_bookmark_paths:
        if IS_DEBUG:
            print(f"🎯 Found exact bookmark_path_rel match: '{bookmark_path_rel}'")
        return [(bookmark_path_rel, all_bookmark_objects[bookmark_path_rel])]

    # Normalize user input
    user_input_parts = split_path_into_array(bookmark_path_rel)
    if IS_DEBUG:
        print(f"🔎 Normalized user input: {user_input_parts}")

    # Try stepwise matching
    stepwise_matches = stepwise_match(user_input_parts, all_saved_bookmark_paths)
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
        input_tokens = set(normalized_input.replace('/', ' ').replace('-', ' ').split())
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
    return []


def find_matching_bookmark_strict(bookmark_query, folder_dir):
    """
    Return exact match path if the normalized bookmark path matches query.
    Used during creation to avoid fuzzy fallbacks.
    """
    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return None

    query_norm = bookmark_query.strip().replace(':', '/')
    return query_norm if query_norm in all_bookmark_objects else None



@print_def_name(IS_PRINT_DEF_NAME)
def get_bookmark_info(bookmark_tail_name):
    """
    Get information about a bookmark if it exists, with fuzzy matching across all folders.
    """
    valid_root_dir_names = get_all_valid_root_dir_names()
    print_color('---- valid_root_dir_names ----', 'magenta')
    pprint(valid_root_dir_names)
    print('')
    if not valid_root_dir_names:
        return None, None

    all_matches = []
    # Search for bookmark across all folders, collect all matches
    for root_dir_name in valid_root_dir_names:
        matches = []
        matched_name, bookmark_info = find_matching_bookmark(bookmark_tail_name, root_dir_name)
        if matched_name and bookmark_info:
            # If find_matching_bookmark returns a single match, add it
            matches.append((matched_name, bookmark_info))
        elif matched_name and bookmark_info is None:
            # If user chose to create a new bookmark, skip
            continue
        # If find_matching_bookmark returns multiple matches, add them all
        # (You may need to refactor find_matching_bookmark to return all matches instead of prompting)
        # For now, let's assume it only returns one or zero

        all_matches.extend(matches)

    # If only one match, return it
    if len(all_matches) == 1:
        return all_matches[0]

    # If multiple, prompt the user
    if all_matches:
        print(f"\n🤔 Multiple bookmarks matched '{bookmark_tail_name}':\n")
        for i, (match, info) in enumerate(all_matches, 1):
            time_str = info.get("timestamp_formatted", "unknown time")
            tags_str = ", ".join(info.get("tags", [])) if info.get("tags") else "none"
            path_parts = match.split("/")
            bookmark_label = path_parts[-1]
            folder_path = " / ".join(path_parts[:-1]) if len(path_parts) > 1 else "(root)"
            print(f"  [{i}] {bookmark_label}")
            print(f"      • Time: {time_str}")
            print(f"      • Path: {folder_path}")
            print(f"      • Tags: {tags_str}")
        print(f"  [{len(all_matches) + 1}] ➕ Create new bookmark '{bookmark_tail_name}'\n")

        while True:
            choice = input(f"Enter choice (1-{len(all_matches) + 1}): ")
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(all_matches):
                    selected_match, selected_info = all_matches[choice_num - 1]
                    print(f"✅ Selected bookmark: '{selected_match}'")
                    return selected_match, selected_info
                elif choice_num == len(all_matches) + 1:
                    print(f"✅ Creating new bookmark: '{bookmark_tail_name}'")
                    return None, None
                else:
                    print("❌ Invalid choice. Please try again.")
            except ValueError:
                print("❌ Please enter a number.")

    print(f"❌ No bookmarks found matching '{bookmark_tail_name}'")
    return None, None

def load_obs_bookmark_directly(bookmark_path_rel, bookmark_info):
    # TODO(MFB): Look into me and see if this is the bookmark name or the whole bookmark (path+name)
    """Load OBS bookmark directly without using the bookmark manager script"""

    try:
        if IS_DEBUG:
            print(f"🔍 Debug - Loading bookmark_path_rel: {bookmark_path_rel}")
            print(f"🔍 Debug - Bookmark info keys: {list(bookmark_info.keys())}")
            print(f"🔍 Debug - video_filename: {bookmark_info.get('video_filename', 'NOT_FOUND')}")
            print(f"🔍 Debug - timestamp: {bookmark_info.get('timestamp', 'NOT_FOUND')}")
            print(f"🔍 Debug - timestamp_formatted: {bookmark_info.get('timestamp_formatted', 'NOT_FOUND')}")

        if not bookmark_info:
            print(f"❌ No file path found in bookmark_path_rel metadata")
            if IS_DEBUG:
                print(f"🔍 Debug - Available keys in bookmark_info: {list(bookmark_info.keys())}")
            return False

        cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)

        # Load the media file if different
        current_settings = cl.send(
            "GetInputSettings", {"inputName": "Media Source"})
        current_file = current_settings.input_settings.get("local_file", "")

        if IS_DEBUG:
            pprint(current_settings)
            print(f"🔍 Debug - Current OBS file: {current_file}")

        # Construct the full video file path from env variable
        video_filename = bookmark_info.get('video_filename', '')
        video_file_path = construct_full_video_file_path(video_filename)

        if not video_filename:
            print(f"❌ No file path found in bookmark_path_rel metadata")
            if IS_DEBUG:
                print(f"🔍 Debug - Available keys in bookmark_info: {list(bookmark_info.keys())}")
            return False

        if current_file != video_file_path:
            print(f"📁 Loading video file: {video_file_path}")
            cl.send("SetInputSettings", {
                "inputName": "Media Source",
                "inputSettings": {
                    "local_file": video_file_path
                }
            })
            # Wait longer for the media to load before trying to set cursor
            import time
            time.sleep(2)  # Increased from 1 to 2 seconds

        # Start playing the media first
        cl.send("TriggerMediaInputAction", {
            "inputName": "Media Source",
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY"
        })

        # Wait a moment for playback to start
        import time
        time.sleep(0.5)

        # Set the timestamp
        cl.send("SetMediaInputCursor", {
            "inputName": "Media Source",
            "mediaCursor": int(bookmark_info['timestamp'] * 1000)  # Convert seconds to milliseconds
        })

        # Pause the media
        cl.send("TriggerMediaInputAction", {
            "inputName": "Media Source",
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE"
        })

        print(f"✅ Loaded OBS to timestamp from bookmark: {bookmark_info['timestamp_formatted']}")
        return True

    except Exception as e:
        print(f"❌ Failed to load OBS bookmark directly: {e}")
        return False


def find_preceding_bookmark(bookmark_name, folder_dir):
    # TODO(MFB): Look into me and see if this is the bookmark name or the whole bookmark (path+name)
    """Find the bookmark that comes alphabetically/numerically before the given bookmark"""
    print_color('??? ---- find_preceding_bookmark bookmark_name:', 'red')
    pprint(bookmark_name)

    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return None

    # Get all bookmark names and sort them
    bookmark_names = sorted(all_bookmark_objects.keys())

    # Find the index of the current bookmark
    try:
        current_index = bookmark_names.index(bookmark_name)
        if current_index > 0:
            return bookmark_names[current_index - 1]
    except ValueError:
        # If bookmark not found, find the last one alphabetically before it
        for name in reversed(bookmark_names):
            if name < bookmark_name:
                return name

    return None


def stepwise_match(user_parts, all_saved_bookmark_paths):
    """Perform reverse stepwise matching of user_parts against bookmark paths."""
    candidate_paths = []

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

# TODO(KERCH): save_last_used_bookmark
def save_last_used_bookmark(rel_bookmark_dir, bookmark_name, bookmark_info):
    """Save the last used bookmark to a global state file."""
    print('Saving last used bookmark:')

    print_color('??? ---- save_last_used_bookmark rel_bookmark_dir:', 'red')
    pprint(rel_bookmark_dir)
    print_color('??? ---- save_last_used_bookmark bookmark_name:', 'red')
    pprint(bookmark_name)





    state_file = os.path.join(os.path.dirname(__file__), "../obs_bookmark_saves", "last_bookmark_state.json")
    if not bookmark_info:
        bookmark_info = {}

    # Convert slashes to colons in bookmark name for consistency
    bookmark_dir_colons = rel_bookmark_dir.replace('/', ':')

    state_data = {
        "bookmark_name": bookmark_name,
        "description": bookmark_info.get('description', ''),
        "rel_bookmark_dir": bookmark_dir_colons,
        "tags": bookmark_info.get('tags', []),
        "timestamp": bookmark_info.get('timestamp', 0),
        "timestamp_formatted": bookmark_info.get('timestamp_formatted', ''),
        "video_filename": bookmark_info.get('video_filename', ''),
    }

    with open(state_file, 'w') as f:
        json.dump(state_data, f, indent=2)

    # Create symlinks in shortcuts directory
    create_bookmark_symlinks(bookmark_dir_colons, bookmark_name)


def create_bookmark_symlinks(folder_name, bookmark_name):
    """Create symlinks for the last used bookmark and its folder."""
    import os
    import shutil

    print_color('??? ---- create_bookmark_symlinks folder_name:', 'red')
    pprint(folder_name)
    print_color('??? ---- create_bookmark_symlinks bookmark_name:', 'red')
    pprint(bookmark_name)

    folder_name = folder_name.replace(':', '/')

    # Get the root directory of the bookmark manager
    root_dir = os.path.dirname(os.path.dirname(__file__))
    shortcuts_dir = os.path.join(root_dir, "shortcuts")

    # Create shortcuts directory if it doesn't exist
    if not os.path.exists(shortcuts_dir):
        os.makedirs(shortcuts_dir)

    # Create last_used_bookmark directory if it doesn't exist
    last_used_bookmark_dir = os.path.join(shortcuts_dir, "last_used_bookmark")
    if not os.path.exists(last_used_bookmark_dir):
        os.makedirs(last_used_bookmark_dir)

    # Create last_used_bookmark_folder directory if it doesn't exist
    last_used_bookmark_folder_dir = os.path.join(shortcuts_dir, "last_used_bookmark_folder")
    if not os.path.exists(last_used_bookmark_folder_dir):
        os.makedirs(last_used_bookmark_folder_dir)

    # Clear the last_used_bookmark directory - remove everything first
    if os.path.exists(last_used_bookmark_dir):
        for item in os.listdir(last_used_bookmark_dir):
            item_path = os.path.join(last_used_bookmark_dir, item)
            try:
                if os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"⚠️  Warning: Could not remove {item_path}: {e}")

    # Clear the last_used_bookmark_folder directory - remove everything first
    if os.path.exists(last_used_bookmark_folder_dir):
        for item in os.listdir(last_used_bookmark_folder_dir):
            item_path = os.path.join(last_used_bookmark_folder_dir, item)
            try:
                if os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"⚠️  Warning: Could not remove {item_path}: {e}")

    # Construct the target paths
    obs_bookmarks_dir = os.path.join(root_dir, "obs_bookmark_saves")
    bookmark_full_path = os.path.join(obs_bookmarks_dir, folder_name, bookmark_name)
    bookmark_folder_path = os.path.join(obs_bookmarks_dir, folder_name, os.path.dirname(bookmark_name))

    # Get the bookmark name and folder name (last parts of the paths)
    bookmark_basename = os.path.basename(bookmark_name)
    folder_basename = os.path.basename(os.path.dirname(bookmark_name))

    # Define symlink paths
    bookmark_symlink_path = os.path.join(last_used_bookmark_dir, bookmark_basename)
    folder_symlink_path = os.path.join(last_used_bookmark_folder_dir, folder_basename)

    try:
        # Create symlink for the specific bookmark (named after the bookmark)
        if os.path.exists(bookmark_symlink_path):
            if os.path.islink(bookmark_symlink_path):
                os.unlink(bookmark_symlink_path)
            else:
                os.remove(bookmark_symlink_path)
        os.symlink(bookmark_full_path, bookmark_symlink_path)

        # Create symlink for the bookmark's folder (named after the folder)
        if os.path.exists(folder_symlink_path):
            if os.path.islink(folder_symlink_path):
                os.unlink(folder_symlink_path)
            else:
                os.remove(folder_symlink_path)
        os.symlink(bookmark_folder_path, folder_symlink_path)

    except Exception as e:
        print(f"⚠️  Could not create symlinks: {e}")

# TODO(KERCH): get_last_used_bookmark
@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def get_last_used_bookmark():
    """Get the last used bookmark from the global state file."""
    state_file = os.path.join(os.path.dirname(__file__), "../obs_bookmark_saves", "last_bookmark_state.json")

    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    return None


@print_def_name(IS_PRINT_DEF_NAME)
def get_last_used_bookmark_display():
    """Get a formatted string for displaying the last used bookmark."""
    last_used = get_last_used_bookmark()
    if last_used:
        folder_name = last_used.get("folder_name", "unknown")
        bookmark_name = last_used.get("bookmark_name", "unknown")
        timestamp = last_used.get("timestamp", "")

        print_color('??? ---- get_last_used_bookmark_display folder_name:', 'red')
        pprint(folder_name)
        print_color('??? ---- get_last_used_bookmark_display bookmark_name:', 'red')
        pprint(bookmark_name)


        # Format timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp

        return f"{folder_name}:{bookmark_name} (last used: {formatted_time})"
    return None


def find_next_bookmark_in_folder(current_bookmark_name, bookmark_dir):
    """Find the next bookmark in the same directory as the current bookmark."""
    print_color('??? ---- find_next_bookmark_in_folder current_bookmark_name:', 'red')
    pprint(current_bookmark_name)
    print_color('??? ---- find_next_bookmark_in_folder bookmark_dir:', 'red')
    pprint(bookmark_dir)

    all_bookmark_objects = load_bookmarks_from_folder(bookmark_dir)
    if not all_bookmark_objects:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(current_path_parts) > 1 else 'root'
    current_bookmark_basename = current_path_parts[-1]

    # Get all bookmarks in the same folder
    sibling_bookmark_paths = []
    for bookmark_object_path in all_bookmark_objects.keys():
        path_parts = bookmark_object_path.split('/')
        if len(path_parts) == 1:
            bookmark_obj_dir = 'root'
        else:
            bookmark_obj_dir = '/'.join(path_parts[:-1])

        if bookmark_obj_dir == current_folder_path:
            sibling_bookmark_paths.append(path_parts[-1])

    if not sibling_bookmark_paths:
        return None

    # Sort bookmarks to get proper order
    sibling_bookmark_paths.sort()

    # Find current bookmark index
    try:
        current_index = sibling_bookmark_paths.index(current_bookmark_basename)
        if current_index < len(sibling_bookmark_paths) - 1:
            next_bookmark_basename = sibling_bookmark_paths[current_index + 1]
            # Construct full path
            if current_folder_path == 'root':
                return next_bookmark_basename
            else:
                return f"{current_folder_path}/{next_bookmark_basename}"
    except ValueError:
        return None

    return None


def find_previous_bookmark_in_folder(current_bookmark_name, folder_dir):
    """Find the previous bookmark in the same directory as the current bookmark."""
    print_color('??? ---- find_previous_bookmark_in_folder current_bookmark_name:', 'red')
    pprint(current_bookmark_name)
    print_color('??? ---- find_previous_bookmark_in_folder folder_dir:', 'red')
    pprint(folder_dir)

    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(current_path_parts) > 1 else 'root'
    current_bookmark_basename = current_path_parts[-1]

    # Get all bookmarks in the same folder
    folder_bookmarks = []
    for bookmark_path in all_bookmark_objects.keys():
        path_parts = bookmark_path.split('/')
        if len(path_parts) == 1:
            folder_path = 'root'
        else:
            folder_path = '/'.join(path_parts[:-1])

        if folder_path == current_folder_path:
            folder_bookmarks.append(path_parts[-1])

    if not folder_bookmarks:
        return None

    # Sort bookmarks to get proper order
    folder_bookmarks.sort()

    # Find current bookmark index
    try:
        current_index = folder_bookmarks.index(current_bookmark_basename)
        if current_index > 0:
            prev_bookmark_basename = folder_bookmarks[current_index - 1]
            # Construct full path
            if current_folder_path == 'root':
                return prev_bookmark_basename
            else:
                return f"{current_folder_path}/{prev_bookmark_basename}"
    except ValueError:
        return None

    return None


def find_first_bookmark_in_folder(current_bookmark_name, folder_dir):
    """Find the first bookmark in the same directory as the current bookmark."""
    print_color('??? ---- find_first_bookmark_in_folder current_bookmark_name:', 'red')
    pprint(current_bookmark_name)
    print_color('??? ---- find_first_bookmark_in_folder folder_dir:', 'red')
    pprint(folder_dir)

    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(current_path_parts) > 1 else 'root'

    # Get all bookmarks in the same folder
    folder_bookmarks = []
    for bookmark_path in all_bookmark_objects.keys():
        path_parts = bookmark_path.split('/')
        if len(path_parts) == 1:
            folder_path = 'root'
        else:
            folder_path = '/'.join(path_parts[:-1])

        if folder_path == current_folder_path:
            folder_bookmarks.append(path_parts[-1])

    if not folder_bookmarks:
        return None

    # Sort bookmarks to get proper order
    folder_bookmarks.sort()

    # Return first bookmark
    first_bookmark_basename = folder_bookmarks[0]
    if current_folder_path == 'root':
        return first_bookmark_basename
    else:
        return f"{current_folder_path}/{first_bookmark_basename}"


def find_last_bookmark_in_folder(current_bookmark_name, folder_dir):
    """Find the last bookmark in the same directory as the current bookmark."""
    print_color('??? ---- find_last_bookmark_in_folder current_bookmark_name:', 'red')
    pprint(current_bookmark_name)
    print_color('??? ---- find_last_bookmark_in_folder folder_dir:', 'red')
    pprint(folder_dir)

    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(current_path_parts) > 1 else 'root'

    # Get all bookmarks in the same folder
    folder_bookmarks = []
    for bookmark_path in all_bookmark_objects.keys():
        path_parts = bookmark_path.split('/')
        if len(path_parts) == 1:
            folder_path = 'root'
        else:
            folder_path = '/'.join(path_parts[:-1])

        if folder_path == current_folder_path:
            folder_bookmarks.append(path_parts[-1])

    if not folder_bookmarks:
        return None

    # Sort bookmarks to get proper order
    folder_bookmarks.sort()

    # Return last bookmark
    last_bookmark_basename = folder_bookmarks[-1]
    if current_folder_path == 'root':
        return last_bookmark_basename
    else:
        return f"{current_folder_path}/{last_bookmark_basename}"


def resolve_navigation_bookmark(navigation_command, folder_dir):
    """Resolve navigation commands (next, previous, first, last) to actual bookmark names."""
    # Get the last used bookmark to determine the current position
    last_used_info = get_last_used_bookmark()
    if not last_used_info:
        print(f"❌ No last used bookmark found. Cannot navigate with '{navigation_command}'")
        return None, None

    folder_name = last_used_info.get("folder_name")
    bookmark_name = last_used_info.get("bookmark_name")

    # Convert colons back to slashes for internal processing
    bookmark_name_slashes = bookmark_name.replace(':', '/')

    # Verify the folder matches
    folder_basename = os.path.basename(folder_dir)
    if folder_basename != folder_name:
        print(f"❌ Folder mismatch. Last used bookmark is in '{folder_name}', but current folder is '{folder_basename}'")
        return None, None

    # Resolve the navigation command
    if navigation_command == "next":
        target_bookmark = find_next_bookmark_in_folder(bookmark_name_slashes, folder_dir)
        if not target_bookmark:
            print(f"❌ No next bookmark found after '{bookmark_name}'")
            return None, None
    elif navigation_command == "previous":
        target_bookmark = find_previous_bookmark_in_folder(bookmark_name_slashes, folder_dir)
        if not target_bookmark:
            print(f"❌ No previous bookmark found before '{bookmark_name}'")
            return None, None
    elif navigation_command == "first":
        target_bookmark = find_first_bookmark_in_folder(bookmark_name_slashes, folder_dir)
        if not target_bookmark:
            print(f"❌ No bookmarks found in the same directory as '{bookmark_name}'")
            return None, None
    elif navigation_command == "last":
        target_bookmark = find_last_bookmark_in_folder(bookmark_name_slashes, folder_dir)
        if not target_bookmark:
            print(f"❌ No bookmarks found in the same directory as '{bookmark_name}'")
            return None, None
    else:
        print(f"❌ Unknown navigation command: '{navigation_command}'")
        return None, None

    # Load the bookmark info for the target bookmark
    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if target_bookmark not in all_bookmark_objects:
        print(f"❌ Target bookmark '{target_bookmark}' not found in folder")
        return None, None

    bookmark_info = all_bookmark_objects[target_bookmark]
    print(f"🎯 Navigating to: {folder_name}:{target_bookmark.replace('/', ':')}")
    return target_bookmark, bookmark_info


def get_all_bookmark_paths(valid_root_dir_names):
    """
    Return a flat list of all bookmark paths from all active folders.
    """
    bookmark_paths = []

    for folder in valid_root_dir_names:
        all_bookmark_objects = load_bookmarks_from_folder(folder)
        bookmark_paths.extend(all_bookmark_objects.keys())

    return bookmark_paths


def build_bookmark_token_map(include_tags_and_descriptions=True):
    """
    Return a dict mapping each bookmark path to a token set for matching.
    """
    from app.bookmarks_folders import get_all_valid_root_dir_names
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

def token_match_bookmarks(query_string, folder_dir):
    """
    Returns a list of bookmark paths where all query tokens appear in the path.
    """
    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return []

    query_tokens = set(query_string.lower().replace(":", " ").replace("/", " ").split())
    matches = []

    for path in all_bookmark_objects.keys():
        path_tokens = set(re.split(r"[-_/]", path.lower()))
        if query_tokens.issubset(path_tokens):
            matches.append(path)

    return matches

