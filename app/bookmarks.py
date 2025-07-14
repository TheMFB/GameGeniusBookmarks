# type: ignore
"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
import json
import obsws_python as obs
from datetime import datetime

from app.bookmarks_consts import IS_DEBUG
from app.bookmarks_folders import get_all_active_folders
from app.utils import print_color

import re


def load_bookmarks_from_folder(folder_dir):
    """Load bookmarks from folder directory by scanning for bookmark directories recursively"""
    bookmarks = {}
    # print_color('Loading bookmarks from folder: ' + folder_dir, 'cyan')

    if not os.path.exists(folder_dir):
        return bookmarks

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
                        bookmark_key = f"{current_path}/{item}"
                    else:
                        bookmark_key = item

                    # Use the new load_bookmark_meta function
                    from app.bookmarks_meta import load_bookmark_meta
                    bookmark_meta = load_bookmark_meta(item_path)
                    if bookmark_meta:
                        bookmarks[bookmark_key] = bookmark_meta
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

    scan_for_bookmarks(folder_dir)
    return bookmarks


# def find_matching_bookmark(bookmark_name, folder_dir):
#     """Find matching bookmark using fuzzy matching logic with support for nested folders"""
#     bookmarks = load_bookmarks_from_folder(folder_dir)

#     if not bookmarks:
#         return None, None

#     # First try exact match
#     if bookmark_name in bookmarks:
#         if IS_DEBUG:
#             print(f"🎯 Found exact bookmark match: '{bookmark_name}'")
#         return bookmark_name, bookmarks[bookmark_name]

#     # Try fuzzy matching - find bookmarks that start with the given name
#     # Also check if the bookmark name appears anywhere in the path
#     matches = []
#     for path in bookmarks.keys():
#         # Check if the path starts with the bookmark name
#         if path.lower().startswith(bookmark_name.lower()):
#             matches.append(path)
#         # Check if the bookmark name appears in any part of the path
#         elif bookmark_name.lower() in path.lower():
#             matches.append(path)

#     if len(matches) == 0:
#         return None, None
#     elif len(matches) == 1:
#         target_bookmark_name = matches[0]
#         if IS_DEBUG:
#             print(f"🎯 Found fuzzy bookmark match: '{target_bookmark_name}'")
#         return target_bookmark_name, bookmarks[target_bookmark_name]
#     else:
#         print(f"🤔 Multiple bookmarks found matching '{bookmark_name}':")
#         print(f"   Please be more specific. Found {len(matches)} matches:")
#         for i, match in enumerate(sorted(matches), 1):
#             bookmark = bookmarks[match]
#             # Convert slashes to colons with spaces for display
#             display_match = match.replace('/', ' : ')
#             print(
#                 f"   {i}. {bookmark.get('timestamp_formatted', 'unknown time')} - {display_match}")
#         print(f"   {len(matches) + 1}. Create new bookmark '{bookmark_name}'")

#         while True:
#             try:
#                 choice = input(
#                     f"Enter choice (1-{len(matches) + 1}): ").strip()
#                 choice_num = int(choice)

#                 if 1 <= choice_num <= len(matches):
#                     selected_match = sorted(matches)[choice_num - 1]
#                     print(f"✅ Selected bookmark: '{selected_match}'")
#                     return selected_match, bookmarks[selected_match]
#                 elif choice_num == len(matches) + 1:
#                     print(f"✅ Creating new bookmark: '{bookmark_name}'")
#                     return None, None  # Signal to create new bookmark
#                 else:
#                     print(
#                         f"❌ Invalid choice. Please enter 1-{len(matches) + 1}")
#             except ValueError:
#                 print("❌ Please enter a valid number")
#             except KeyboardInterrupt:
#                 print("\n❌ Cancelled")
#                 return None, None


def is_strict_equal(path1, path2):
    """Check if two bookmark paths are strictly equal after normalization."""
    normalized1 = '/'.join(normalize_path(path1))
    normalized2 = '/'.join(normalize_path(path2))
    return normalized1 == normalized2


def find_matching_bookmark(bookmark_name, folder_dir):
    """Find matching bookmark using step-through logic and fallback fuzzy matching."""

    bookmarks = load_bookmarks_from_folder(folder_dir)
    if not bookmarks:
        return None, None

    all_paths = list(bookmarks.keys())

    # First try exact match
    if bookmark_name in bookmarks:
        if IS_DEBUG:
            print(f"🎯 Found exact bookmark match: '{bookmark_name}'")
        return bookmark_name, bookmarks[bookmark_name]

    # Normalize user input
    user_input_parts = normalize_path(bookmark_name)

    if IS_DEBUG:
        print(f"🔎 Normalized user input: {user_input_parts}")

    # Try stepwise matching
    stepwise_matches = stepwise_match(user_input_parts, all_paths)

    if stepwise_matches:
        if len(stepwise_matches) == 1:
            target = stepwise_matches[0]
            if IS_DEBUG:
                print(f"🎯 Stepwise match resolved to: '{target}'")
            return target, bookmarks[target]
        else:
            print(f"🤔 Multiple bookmarks found matching '{bookmark_name}':")
            print(
                f"   Please be more specific. Found {len(stepwise_matches)} matches:")
            for i, match in enumerate(sorted(stepwise_matches), 1):
                bookmark = bookmarks[match]
                display_match = match.replace('/', ' : ')
                print(
                    f"   {i}. {bookmark.get('timestamp_formatted', 'unknown time')} - {display_match}")
            print(
                f"   {len(stepwise_matches) + 1}. Create new bookmark '{bookmark_name}'")

            while True:
                try:
                    choice = input(
                        f"Enter choice (1-{len(stepwise_matches) + 1}): ").strip()
                    choice_num = int(choice)

                    if 1 <= choice_num <= len(stepwise_matches):
                        selected_match = sorted(stepwise_matches)[
                            choice_num - 1]
                        print(f"✅ Selected bookmark: '{selected_match}'")
                        return selected_match, bookmarks[selected_match]
                    elif choice_num == len(stepwise_matches) + 1:
                        print(f"✅ Creating new bookmark: '{bookmark_name}'")
                        return None, None
                    else:
                        print(
                            f"❌ Invalid choice. Please enter 1-{len(stepwise_matches) + 1}")
                except ValueError:
                    print("❌ Please enter a valid number")
                except KeyboardInterrupt:
                    print("\n❌ Cancelled")
                    return None, None

    # Fallback fuzzy match
    matches = []
    for path in bookmarks.keys():
        # Check for exact prefix match first
        if path.lower().startswith(bookmark_name.lower()):
            matches.append(path)
        # Check if the bookmark name appears anywhere in the path
        elif bookmark_name.lower() in path.lower():
            matches.append(path)
        # Check for partial matches (e.g., 'ra-00' should match 'ra-00-main-screen')
        elif any(part.lower().startswith(bookmark_name.lower()) for part in path.split('/')):
            matches.append(path)
        # Check for wildcard-like matching (e.g., 'ra-00*' should match 'ra-00-main-screen')
        elif bookmark_name.lower().replace('*', '') in path.lower():
            matches.append(path)

    if len(matches) == 0:
        return None, None
    elif len(matches) == 1:
        target = matches[0]
        if IS_DEBUG:
            print(f"🎯 Fuzzy fallback match: '{target}'")
        return target, bookmarks[target]
    else:
        print(
            f"🤔 Fuzzy fallback: Multiple bookmarks found matching '{bookmark_name}':")
        print(f"   Please be more specific. Found {len(matches)} matches:")
        for i, match in enumerate(sorted(matches), 1):
            bookmark = bookmarks[match]
            display_match = match.replace('/', ' : ')
            print(
                f"   {i}. {bookmark.get('timestamp_formatted', 'unknown time')} - {display_match}")
        print(f"   {len(matches) + 1}. Create new bookmark '{bookmark_name}'")

        while True:
            try:
                choice = input(
                    f"Enter choice (1-{len(matches) + 1}): ").strip()
                choice_num = int(choice)

                if 1 <= choice_num <= len(matches):
                    selected_match = sorted(matches)[choice_num - 1]
                    print(f"✅ Selected bookmark: '{selected_match}'")
                    return selected_match, bookmarks[selected_match]
                elif choice_num == len(matches) + 1:
                    print(f"✅ Creating new bookmark: '{bookmark_name}'")
                    return None, None
                else:
                    print(
                        f"❌ Invalid choice. Please enter 1-{len(matches) + 1}")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n❌ Cancelled")
                return None, None


def get_bookmark_info(bookmark_name):
    """Get information about a bookmark if it exists, with fuzzy matching across all folders"""
    # Get all active folders
    active_folders = get_all_active_folders()
    if not active_folders:
        return None, None

    # Search for bookmark across all folders
    for folder_dir in active_folders:
        matched_name, bookmark_info = find_matching_bookmark(
            bookmark_name, folder_dir)
        if matched_name:
            folder_name = os.path.basename(folder_dir)
            if IS_DEBUG:
                print(
                    f"🎯 Found bookmark '{matched_name}' in folder '{folder_name}'")
            return matched_name, bookmark_info

    print(f"❌ No bookmarks found matching '{bookmark_name}'")
    # Bookmark not found in any folder
    return None, None


def load_obs_bookmark_directly(bookmark_name, bookmark_info):
    """Load OBS bookmark directly without using the bookmark manager script"""
    try:
        cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)

        # Load the media file if different
        current_settings = cl.send(
            "GetInputSettings", {"inputName": "Media Source"})
        current_file = current_settings.input_settings.get("local_file", "")

        # Use the full_file_path from bookmark_info (constructed by load_bookmark_meta)
        bookmarked_file = bookmark_info.get('full_file_path', '')

        if not bookmarked_file:
            print(f"❌ No file path found in bookmark metadata")
            return False

        if current_file != bookmarked_file:
            print(f"📁 Loading video file: {os.path.basename(bookmarked_file)}")
            cl.send("SetInputSettings", {
                "inputName": "Media Source",
                "inputSettings": {
                    "local_file": bookmarked_file
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
            "mediaCursor": bookmark_info['timestamp']
        })

        # Pause the media
        cl.send("TriggerMediaInputAction", {
            "inputName": "Media Source",
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE"
        })

        print(f"✅ Loaded bookmark to {bookmark_info['timestamp_formatted']}")
        return True

    except Exception as e:
        print(f"❌ Failed to load OBS bookmark directly: {e}")
        return False


def find_preceding_bookmark(bookmark_name, folder_dir):
    """Find the bookmark that comes alphabetically/numerically before the given bookmark"""
    bookmarks = load_bookmarks_from_folder(folder_dir)
    if not bookmarks:
        return None

    # Get all bookmark names and sort them
    bookmark_names = sorted(bookmarks.keys())

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


def normalize_path(path):
    """Normalize a bookmark path into components using both ':' and '/' as separators."""
    # Replace both ':' and '/' with a single consistent delimiter (e.g., '/')
    path = path.replace(':', '/')
    return [part.lower() for part in path.strip('/').split('/')]


def stepwise_match(user_parts, all_bookmarks):
    """Perform reverse stepwise matching of user_parts against bookmark paths."""
    candidate_paths = []

    # Preprocess all bookmarks into tokenized forms
    tokenized_bookmarks = [
        (path, normalize_path(path)) for path in all_bookmarks
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


def save_last_used_bookmark(folder_name, bookmark_name):
    """Save the last used bookmark to a global state file."""
    state_file = os.path.join(os.path.dirname(__file__), "..", "last_bookmark_state.json")

    # Ensure we're saving the folder basename, not the full path
    folder_basename = os.path.basename(folder_name) if '/' in folder_name else folder_name

    # Convert slashes to colons in bookmark name for consistency
    bookmark_name_colons = bookmark_name.replace('/', ':')

    state_data = {
        "folder_name": folder_basename,  # Save just the basename
        "bookmark_name": bookmark_name_colons,  # Use colons instead of slashes
        "timestamp": datetime.now().isoformat()
    }

    with open(state_file, 'w') as f:
        json.dump(state_data, f, indent=2)


def get_last_used_bookmark():
    """Get the last used bookmark from the global state file."""
    state_file = os.path.join(os.path.dirname(__file__), "..", "last_bookmark_state.json")

    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    return None

def get_last_used_bookmark_display():
    """Get a formatted string for displaying the last used bookmark."""
    last_used = get_last_used_bookmark()
    if last_used:
        folder_name = last_used.get("folder_name", "unknown")
        bookmark_name = last_used.get("bookmark_name", "unknown")
        timestamp = last_used.get("timestamp", "")

        # Format timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp

        return f"{folder_name}:{bookmark_name} (last used: {formatted_time})"
    return None


def find_next_bookmark_in_folder(current_bookmark_name, folder_dir):
    """Find the next bookmark in the same directory as the current bookmark."""
    bookmarks = load_bookmarks_from_folder(folder_dir)
    if not bookmarks:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(current_path_parts) > 1 else 'root'
    current_bookmark_basename = current_path_parts[-1]

    # Get all bookmarks in the same folder
    folder_bookmarks = []
    for bookmark_path in bookmarks.keys():
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
        if current_index < len(folder_bookmarks) - 1:
            next_bookmark_basename = folder_bookmarks[current_index + 1]
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
    bookmarks = load_bookmarks_from_folder(folder_dir)
    if not bookmarks:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(current_path_parts) > 1 else 'root'
    current_bookmark_basename = current_path_parts[-1]

    # Get all bookmarks in the same folder
    folder_bookmarks = []
    for bookmark_path in bookmarks.keys():
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
    bookmarks = load_bookmarks_from_folder(folder_dir)
    if not bookmarks:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(current_path_parts) > 1 else 'root'

    # Get all bookmarks in the same folder
    folder_bookmarks = []
    for bookmark_path in bookmarks.keys():
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
    bookmarks = load_bookmarks_from_folder(folder_dir)
    if not bookmarks:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(current_path_parts) > 1 else 'root'

    # Get all bookmarks in the same folder
    folder_bookmarks = []
    for bookmark_path in bookmarks.keys():
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
    bookmarks = load_bookmarks_from_folder(folder_dir)
    if target_bookmark not in bookmarks:
        print(f"❌ Target bookmark '{target_bookmark}' not found in folder")
        return None, None

    bookmark_info = bookmarks[target_bookmark]
    print(f"🎯 Navigating to: {folder_name}:{target_bookmark.replace('/', ':')}")
    return target_bookmark, bookmark_info
