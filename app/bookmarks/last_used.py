import json
import os

from app.bookmarks.bookmarks import create_bookmark_symlinks
from app.consts.bookmarks_consts import ABS_OBS_BOOKMARKS_DIR
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.decorators import memoize, print_def_name

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
