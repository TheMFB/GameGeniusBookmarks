# type: ignore
"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
import json
import obsws_python as obs

from app.bookmarks_consts import IS_DEBUG
from app.bookmarks_sessions import get_all_active_sessions

import re


def load_bookmarks_from_session(session_dir):
    """Load bookmarks from session directory by scanning for bookmark directories recursively"""
    bookmarks = {}

    if not os.path.exists(session_dir):
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
                    try:
                        with open(meta_file, 'r') as f:
                            bookmark_meta = json.load(f)
                            bookmarks[bookmark_key] = bookmark_meta
                    except json.JSONDecodeError:
                        if IS_DEBUG:
                            print(
                                f"⚠️  Could not parse bookmark_meta.json in {item_path}")
                        continue
                else:
                    # This is a regular directory, scan recursively
                    # Use forward slashes for consistency across platforms
                    if current_path:
                        new_path = f"{current_path}/{item}"
                    else:
                        new_path = item
                    scan_for_bookmarks(item_path, new_path)

    scan_for_bookmarks(session_dir)
    return bookmarks


# def find_matching_bookmark(bookmark_name, session_dir):
#     """Find matching bookmark using fuzzy matching logic with support for nested folders"""
#     bookmarks = load_bookmarks_from_session(session_dir)

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


def find_matching_bookmark(bookmark_name, session_dir):
    """Find matching bookmark using step-through logic and fallback fuzzy matching."""

    bookmarks = load_bookmarks_from_session(session_dir)
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
        if path.lower().startswith(bookmark_name.lower()):
            matches.append(path)
        elif bookmark_name.lower() in path.lower():
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
    """Get information about a bookmark if it exists, with fuzzy matching across all sessions"""
    # Get all active sessions
    active_sessions = get_all_active_sessions()
    if not active_sessions:
        return None, None

    # Search for bookmark across all sessions
    for session_dir in active_sessions:
        matched_name, bookmark_info = find_matching_bookmark(
            bookmark_name, session_dir)
        if matched_name:
            session_name = os.path.basename(session_dir)
            if IS_DEBUG:
                print(
                    f"🎯 Found bookmark '{matched_name}' in session '{session_name}'")
            return matched_name, bookmark_info

    print(f"❌ No bookmarks found matching '{bookmark_name}'")
    # Bookmark not found in any session
    return None, None


def load_obs_bookmark_directly(bookmark_name, bookmark_info):
    """Load OBS bookmark directly without using the bookmark manager script"""
    try:
        cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)

        # Load the media file if different
        current_settings = cl.send(
            "GetInputSettings", {"inputName": "Media Source"})
        current_file = current_settings.input_settings.get("local_file", "")
        bookmarked_file = bookmark_info['file_path']

        if current_file != bookmarked_file:
            print(f"📁 Loading video file: {os.path.basename(bookmarked_file)}")
            cl.send("SetInputSettings", {
                "inputName": "Media Source",
                "inputSettings": {
                    "local_file": bookmarked_file
                }
            })
            import time
            time.sleep(1)

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


def find_preceding_bookmark(bookmark_name, session_dir):
    """Find the bookmark that comes alphabetically/numerically before the given bookmark"""
    bookmarks = load_bookmarks_from_session(session_dir)
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
