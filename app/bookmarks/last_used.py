"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
from pprint import pprint
import json
from datetime import datetime

from app.utils import print_color, print_def_name, memoize
from app.bookmarks.bookmarks import create_bookmark_symlinks

IS_AGGREGATE_TAGS = False
IS_PRINT_DEF_NAME = True


# TODO(KERCH): save_last_used_bookmark
def save_last_used_bookmark(rel_bookmark_dir, bookmark_name, bookmark_info):
    """Save the last used bookmark to a global state file."""
    print('Saving last used bookmark:')

    print_color('??? ---- save_last_used_bookmark rel_bookmark_dir:', 'red')
    pprint(rel_bookmark_dir)
    print_color('??? ---- save_last_used_bookmark bookmark_name:', 'red')
    pprint(bookmark_name)

    state_file = os.path.join(os.path.dirname(
        __file__), "../obs_bookmark_saves", "last_bookmark_state.json")
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



# TODO(KERCH): get_last_used_bookmark
@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def get_last_used_bookmark():
    """Get the last used bookmark from the global state file."""
    state_file = os.path.join(os.path.dirname(
        __file__), "../obs_bookmark_saves", "last_bookmark_state.json")

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

        print_color(
            '??? ---- get_last_used_bookmark_display folder_name:', 'red')
        pprint(folder_name)
        print_color(
            '??? ---- get_last_used_bookmark_display bookmark_name:', 'red')
        pprint(bookmark_name)

        # Format timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp

        return f"{folder_name}:{bookmark_name} (last used: {formatted_time})"
    return None
