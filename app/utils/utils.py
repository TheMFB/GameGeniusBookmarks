from typing import TypedDict
import os
from pathlib import Path
from app.bookmarks_consts import ABS_OBS_BOOKMARKS_DIR
from app.utils.decorators import print_def_name, memoize

IS_PRINT_DEF_NAME = True

def abs_to_rel_path(abs_path, base_dir):
    """Convert an absolute path to a relative path."""
    return os.path.relpath(abs_path, base_dir)

class BookmarkPathDictionary(TypedDict):
    bookmark_tail_name: str

    # Colon-separated
    bookmark_dir_colon_abs: str
    bookmark_dir_colon_rel: str

    bookmark_path_colon_abs: str
    bookmark_path_colon_rel: str

    # Slash-separated
    bookmark_dir_slash_abs: str
    bookmark_dir_slash_rel: str

    bookmark_path_slash_abs: str
    bookmark_path_slash_rel: str


# TODO(KERCH): Instead of sending out a large tuple, let's return a dictionary with all the values abs, rel, colon, slash, path, dir -- mix and match all that make sense). Make a class like we did for the process_flags.py, and then return that object. Anything that uses convert_bookmark_path should then be updated to accept the object, and pull out the values that they want. (you'll be removing the is_absolute_path and is_colon_separated optional params as they'll always be in the return.)
@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def convert_bookmark_path(
    *args
) -> BookmarkPathDictionary:
    """
    Flexible conversion utility for bookmark paths.

    # TODO(KERCH): Update this documentation.
    # One-argument: full bookmark_dir
    print(convert_bookmark_path("mfb3/MFB/TEST/01"))
    # ('mfb3/MFB/TEST', '01', 'mfb3/MFB/TEST/01')
    
    # Two-argument: tail and bookmark_dir
    print(convert_bookmark_path("01", "mfb3/MFB/TEST"))
    # ('mfb3/MFB/TEST', '01', 'mfb3/MFB/TEST/01')

    # Two-argument: full bookmark_dir and full bookmark_dir
    print(convert_bookmark_path("mfb3/MFB/TEST/01", "mfb3/MFB/TEST/01"))
    # ('mfb3/MFB/TEST', '01', 'mfb3/MFB/TEST/01')

    # Colon-separated
    print(convert_bookmark_path("01", "mfb3:MFB:TEST", is_colon_separated=True))
    # ('mfb3:MFB:TEST', '01', 'mfb3:MFB:TEST:01')

    # Absolute bookmark_dir output
    print(convert_bookmark_path("01", "mfb3/MFB/TEST", is_absolute_path=True, bookmark_dir=BOOKMARK_DIR))
    # ('/.../obs_bookmark_saves/mfb3/MFB/TEST', '01', '/.../obs_bookmark_saves/mfb3/MFB/TEST/01')
    """
    # Parse input
    if len(args) == 2:
        # If both are the same, treat as a single full bookmark_dir+name
        if args[0] == args[1]:
            value = args[0]
            if ':' in value:
                parts = value.split(':')
            elif '/' in value or value.startswith(ABS_OBS_BOOKMARKS_DIR):
                parts = ABS_OBS_BOOKMARKS_DIR(value).parts
            else:
                parts = [value]
        else:
            # (bookmark_tail_name, bookmark_dir)
            bookmark_tail_name, bookmark_dir = args
            if ':' in bookmark_dir:
                path_parts = bookmark_dir.split(':')
            else:
                path_parts = Path(bookmark_dir).parts
            parts = list(path_parts) + [bookmark_tail_name]
    elif len(args) == 1:
        # (bookmark_path was provided)
        value = args[0]
        if ':' in value:
            parts = value.split(':')
        elif '/' in value or (bookmark_dir and value.startswith(bookmark_dir)):
            parts = Path(value).parts
        else:
            parts = [value]
    else:
        raise ValueError("Must provide either (bookmark_tail_name, bookmark_dir) or (full_path)")

    if not parts:
        raise ValueError("Could not parse bookmark bookmark_dir.")

    bookmark_tail_name = parts[-1]
    path_parts = parts[:-1]


    # Relative
    bookmark_dir_colon_rel = ':'.join(path_parts)
    bookmark_path_colon_rel = ':'.join(parts)
    bookmark_dir_slash_rel = '/'.join(path_parts)
    bookmark_path_slash_rel = '/'.join(parts)

    # Absolute
    if not bookmark_dir:
        bookmark_dir_colon_abs = None
        bookmark_path_colon_abs = None
        bookmark_dir_slash_abs = None
        bookmark_path_slash_abs = None
    else:
        bookmark_dir_colon_abs = str(
            Path(ABS_OBS_BOOKMARKS_DIR) / bookmark_dir_slash_rel)
        bookmark_path_colon_abs = str(
            Path(ABS_OBS_BOOKMARKS_DIR) / bookmark_path_slash_rel)
        bookmark_dir_slash_abs = str(
            Path(ABS_OBS_BOOKMARKS_DIR) / bookmark_dir_slash_rel)
        bookmark_path_slash_abs = str(
            Path(ABS_OBS_BOOKMARKS_DIR) / bookmark_dir_slash_rel)


    return {
        "bookmark_tail_name": bookmark_tail_name,
        "bookmark_dir_colon_abs": bookmark_dir_colon_abs,
        "bookmark_dir_colon_rel": bookmark_dir_colon_rel,
        "bookmark_path_colon_abs": bookmark_path_colon_abs,
        "bookmark_path_colon_rel": bookmark_path_colon_rel,
        "bookmark_dir_slash_abs": bookmark_dir_slash_abs,
        "bookmark_dir_slash_rel": bookmark_dir_slash_rel,
        "bookmark_path_slash_abs": bookmark_path_slash_abs,
        "bookmark_path_slash_rel": bookmark_path_slash_rel,
    }


def split_path_into_array(path):
    """Normalize a bookmark path into components using both ':' and '/' as separators."""
    # Replace both ':' and '/' with a single consistent delimiter (e.g., '/')
    path = path.replace(':', '/')
    return [part.lower() for part in path.strip('/').split('/')]
