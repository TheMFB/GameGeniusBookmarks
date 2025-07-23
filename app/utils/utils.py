# type: ignore
from pprint import pprint
from typing import Literal, Tuple, Optional
import obsws_python as obs
import os
import base64
from pathlib import Path
from functools import wraps

from app.bookmarks_consts import BOOKMARKS_DIR

def abs_to_rel_path(abs_path, base_dir):
    """Convert an absolute path to a relative path."""
    return os.path.relpath(abs_path, base_dir)


def convert_bookmark_path(
    *args,
    bookmark_dir: Optional[str] = None,
    is_absolute_path: bool = False,
    is_colon_separated: bool = False
) -> Tuple[str, str, str]: # (bookmark_dir, bookmark_tail_name, bookmark_path)
    """
    Flexible conversion utility for bookmark paths.

    # One-argument: full bookmark_dir∂
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
    print(convert_bookmark_path("01", "mfb3/MFB/TEST", is_absolute_path=True, bookmarks_dir=BOOKMARKS_DIR))
    # ('/.../obs_bookmark_saves/mfb3/MFB/TEST', '01', '/.../obs_bookmark_saves/mfb3/MFB/TEST/01')
    """
    # Parse input
    if len(args) == 2:
        # If both are the same, treat as a single full bookmark_dir+name
        if args[0] == args[1]:
            value = args[0]
            if ':' in value:
                parts = value.split(':')
            elif '/' in value or (bookmarks_dir and value.startswith(bookmarks_dir)):
                parts = bookmark_dir(value).parts
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
        # (full_path)
        value = args[0]
        if ':' in value:
            parts = value.split(':')
        elif '/' in value or (bookmarks_dir and value.startswith(bookmarks_dir)):
            parts = Path(value).parts
        else:
            parts = [value]
    else:
        raise ValueError("Must provide either (bookmark_tail_name, bookmark_dir) or (full_path)")

    if not parts:
        raise ValueError("Could not parse bookmark bookmark_dir.")

    bookmark_tail_name = parts[-1]
    path_parts = parts[:-1]

    # Build bookmark_dir string
    if is_colon_separated:
        bookmark_dir = ':'.join(path_parts)
        bookmark_path = ':'.join(parts)
    else:
        bookmark_dir = '/'.join(path_parts)
        bookmark_path = '/'.join(parts)

    # Add absolute if requested
    if is_absolute_path:
        if not bookmarks_dir:
            raise ValueError("bookmarks_dir is required for absolute bookmark_dir output")
        if bookmark_dir:
            bookmark_dir = str(Path(bookmarks_dir) / bookmark_dir)
            bookmark_path = str(Path(bookmarks_dir) / bookmark_path)
        else:
            bookmark_dir = str(Path(bookmarks_dir))
            bookmark_path = str(Path(bookmarks_dir) / bookmark_tail_name)

    return (bookmark_dir, bookmark_tail_name, bookmark_path)


def split_path_into_array(path):
    """Normalize a bookmark path into components using both ':' and '/' as separators."""
    # Replace both ':' and '/' with a single consistent delimiter (e.g., '/')
    path = path.replace(':', '/')
    return [part.lower() for part in path.strip('/').split('/')]


def memoize_in_memory(func):
    """
    Decorator to cache function results in memory for the duration of the process,
    keyed by the function's arguments and keyword arguments.
    """
    cache = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a key from args and kwargs (must be hashable)
        key = (args, tuple(sorted(kwargs.items())))
        if key in cache:
            return cache[key]
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    return wrapper
# TODO(MFB): Fix the print_def_name decorator. It's not working as expected.
# IS_PRINT_FILE_LINK= True
# IS_ADJUST_TO_STACK = True
