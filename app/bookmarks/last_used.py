import os
from pprint import pprint
import json
from datetime import datetime

from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.printing_utils import *
from app.utils.decorators import print_def_name, memoize
from app.consts.bookmarks_consts import ABS_OBS_BOOKMARKS_DIR
from app.bookmarks.bookmarks import create_bookmark_symlinks

IS_AGGREGATE_TAGS = False
IS_PRINT_DEF_NAME = True


# TODO(KERCH): save_last_used_bookmark
@print_def_name(IS_PRINT_DEF_NAME)
def save_last_used_bookmark(matched_bookmark_obj):
    """Save the last used bookmark to a global state file."""
    print('Saving last used bookmark:')
    state_file = os.path.join(ABS_OBS_BOOKMARKS_DIR, "last_bookmark_state.json")

    with open(state_file, 'w') as f:
        json.dump(matched_bookmark_obj, f, indent=2)

    # Create symlinks in shortcuts directory
    create_bookmark_symlinks(matched_bookmark_obj)


# TODO(KERCH): get_last_used_bookmark
@print_def_name(False)
@memoize
def get_last_used_bookmark() -> MatchedBookmarkObj | None:
    """Get the last used bookmark from the global state file."""
    state_file = os.path.join(ABS_OBS_BOOKMARKS_DIR, "last_bookmark_state.json")

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
        bookmark_tail_name = last_used.get("bookmark_tail_name", "unknown")
        timestamp = last_used.get("timestamp", "")

        print_color(
            '??? ---- get_last_used_bookmark_display folder_name:', 'red')
        pprint(folder_name)
        print_color(
            '??? ---- get_last_used_bookmark_display bookmark_tail_name:', 'red')
        pprint(bookmark_tail_name)

        # Format timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp

        return f"{folder_name}:{bookmark_tail_name} (last used: {formatted_time})"
    return None
