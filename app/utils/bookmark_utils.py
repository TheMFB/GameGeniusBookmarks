import os
from pathlib import Path
from app.bookmarks_consts import ABS_OBS_BOOKMARKS_DIR
from app.utils.decorators import print_def_name, memoize
from app.types.bookmark_types import MatchedBookmarkObj
from app.bookmarks.bookmarks import get_bookmark_info

IS_PRINT_DEF_NAME = True

# TODO(KERCH): These are no longer just "utilities" -- we should put some of these into their own folders. (I couldn't find abs_to_rel_path earlier lol)

def abs_to_rel_path(abs_path, base_dir):
    """Convert an absolute path to a relative path."""
    return os.path.relpath(abs_path, base_dir)

@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def convert_exact_bookmark_path_to_dict(
    *args
) -> MatchedBookmarkObj:
    """
    Flexible conversion utility for bookmark paths.

    # TODO(KERCH): Update this documentation.
    # One-argument: full bookmark_dir
    print(convert_exact_bookmark_path_to_dict("mfb3/MFB/TEST/01"))
    # ('mfb3/MFB/TEST', '01', 'mfb3/MFB/TEST/01')
    
    # Two-argument: tail and bookmark_dir
    print(convert_exact_bookmark_path_to_dict("01", "mfb3/MFB/TEST"))
    # ('mfb3/MFB/TEST', '01', 'mfb3/MFB/TEST/01')

    # Two-argument: full bookmark_dir and full bookmark_dir
    print(convert_exact_bookmark_path_to_dict("mfb3/MFB/TEST/01", "mfb3/MFB/TEST/01"))
    # ('mfb3/MFB/TEST', '01', 'mfb3/MFB/TEST/01')

    # Colon-separated
    print(convert_exact_bookmark_path_to_dict("01", "mfb3:MFB:TEST", is_colon_separated=True))
    # ('mfb3:MFB:TEST', '01', 'mfb3:MFB:TEST:01')

    # Absolute bookmark_dir output
    print(convert_exact_bookmark_path_to_dict("01", "mfb3/MFB/TEST", is_absolute_path=True, bookmark_dir=BOOKMARK_DIR))
    # ('/.../obs_bookmark_saves/mfb3/MFB/TEST', '01', '/.../obs_bookmark_saves/mfb3/MFB/TEST/01')
    """
    # TODO(MFB): We may want this to be even more flexible - if both args are a single string, then we may want to look for bookmark names/dir names before we even convert.
    print('++++ convert_exact_bookmark_path_to_dict')
    print('++++ args:', args)

    bookmark_dir = None
    bookmark_tail_name = None

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
            # bookmark_tail_name, bookmark_dir = args
            arg2, arg1 = args
            if ':' in arg1 or '/' in arg1:
                bookmark_dir = arg1
                bookmark_tail_name = arg2
            else:
                bookmark_dir = arg2
                bookmark_tail_name = arg1

            if ':' in bookmark_dir:
                path_parts = bookmark_dir.split(':')
            else:
                path_parts = Path(bookmark_dir).parts
            parts = list(path_parts) + [bookmark_tail_name]
    elif len(args) == 1:
        # (bookmark_path was provided)
        value = args[0]
        print('++++ value:', value)
        if ':' in value:
            parts = value.split(':')
        elif '/' in value:
            parts = Path(value).parts
        else:
            parts = [value]
    else:
        raise ValueError("Must provide either (bookmark_tail_name, bookmark_dir) or (full_path)")

    print('++++ parts:', parts)

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
    # if not bookmark_dir:
    #     bookmark_dir_slash_abs = None
    #     bookmark_path_slash_abs = None
    # else:
    bookmark_dir_slash_abs = str(
        Path(ABS_OBS_BOOKMARKS_DIR) / bookmark_dir_slash_rel)
    bookmark_path_slash_abs = str(
        Path(ABS_OBS_BOOKMARKS_DIR) / bookmark_path_slash_rel)

    bookmark_path_dict = {
        "bookmark_tail_name": bookmark_tail_name,
        "bookmark_dir_colon_rel": bookmark_dir_colon_rel,
        "bookmark_path_colon_rel": bookmark_path_colon_rel,
        "bookmark_dir_slash_abs": bookmark_dir_slash_abs,
        "bookmark_dir_slash_rel": bookmark_dir_slash_rel,
        "bookmark_path_slash_abs": bookmark_path_slash_abs,
        "bookmark_path_slash_rel": bookmark_path_slash_rel,
        "bookmark_info": {},

    }

    bookmark_info = get_bookmark_info(bookmark_path_dict)


    if not bookmark_info:
        return bookmark_path_dict

    return bookmark_info


def split_path_into_array(path):
    """Normalize a bookmark path into components using both ':' and '/' as separators."""
    # Replace both ':' and '/' with a single consistent delimiter (e.g., '/')
    path = path.replace(':', '/')
    return [part.lower() for part in path.strip('/').split('/')]

def does_path_exist_in_bookmarks(all_bookmarks_obj, path, separator=':'):
    """
    Given a colon-separated path (e.g., 'grand-parent:parent:bm1'), 
    return True if that path exists in the nested bookmarks object.
    """
    parts = path.split(separator)
    node = all_bookmarks_obj
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return False
    return True
