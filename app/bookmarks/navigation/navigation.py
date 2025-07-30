from typing import Literal

from app.bookmarks.bookmarks import get_all_shallow_bookmark_abs_paths_in_dir
from app.bookmarks.last_used import get_last_used_bookmark
from app.consts.bookmarks_consts import IS_DEBUG
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.bookmark_utils import convert_exact_bookmark_path_to_bm_obj
from app.utils.decorators import print_def_name

IS_AGGREGATE_TAGS = False
IS_PRINT_DEF_NAME = True

# Likely not used:
# @print_def_name(IS_PRINT_DEF_NAME)
# def find_preceding_bookmark_args(bookmark_obj: MatchedBookmarkObj):
#     # TODO(MFB): Look into me and see if this is the bookmark name or the whole bookmark (path+name)
#     """Find the bookmark that comes alphabetically/numerically before the given bookmark"""

#     bookmark_obj_dir_slash_abs = bookmark_obj.get("bookmark_dir_slash_abs")

#     bookmarks_abs_paths_in_parent_dir = get_all_shallow_bookmark_abs_paths_in_dir(
#         bookmark_obj_dir_slash_abs)
#     bookmarks_abs_paths_in_parent_dir = sorted(bookmarks_abs_paths_in_parent_dir) # Likely unnecessary, but just in case.

#     if not bookmarks_abs_paths_in_parent_dir:
#         print(f"❌ No bookmarks found in parent directory: {bookmark_obj_dir_slash_abs}")
#         return None

#     # Find the index of the current bookmark
#     try:
#         current_index = bookmark_names.index(bookmark_name)
#         if current_index > 0:
#             return bookmark_names[current_index - 1]
#     except ValueError:
#         # If bookmark not found, find the last one alphabetically before it
#         for name in reversed(bookmark_names):
#             if name < bookmark_name:
#                 return name

#     return None

@print_def_name(IS_PRINT_DEF_NAME)
def find_sibling_bookmark_in_folder(bookmark_obj: MatchedBookmarkObj, mode: str = "previous") -> MatchedBookmarkObj | None:
    """
    Find a sibling bookmark relative to the given one, in the same folder.
    Mode can be: 'first', 'previous', 'next', 'last', 'last_used'.
    """
    bookmark_obj_dir_slash_abs = bookmark_obj.get("bookmark_dir_slash_abs")
    if not bookmark_obj_dir_slash_abs:
        return None

    sibling_paths = get_all_shallow_bookmark_abs_paths_in_dir(
        bookmark_obj_dir_slash_abs)
    if not sibling_paths:
        return None

    try:
        index = sibling_paths.index(bookmark_obj_dir_slash_abs)
    except ValueError:
        if IS_DEBUG:
            print(
                f"⚠️ Current bookmark not found in sibling list: {bookmark_obj_dir_slash_abs}")
        return None

    selected_index = None

    if mode == "first":
        selected_index = 0
    elif mode == "last":
        selected_index = len(sibling_paths) - 1
    elif mode == "previous":
        if index > 0:
            selected_index = index - 1
    elif mode == "next":
        if index < len(sibling_paths) - 1:
            selected_index = index + 1
    elif mode == "last_used":
        return get_last_used_bookmark()
    else:
        if IS_DEBUG:
            print(f"⚠️ Unsupported mode: {mode}")
        return None

    if selected_index is not None:
        selected_path = sibling_paths[selected_index]
        return convert_exact_bookmark_path_to_bm_obj(selected_path)

    return None



@print_def_name(IS_PRINT_DEF_NAME)
def resolve_navigation_bookmark_from_last_used(
    navigation_command: Literal["next", "previous", "first", "last", "last_used"],
)-> MatchedBookmarkObj | int | None:
    """Resolve navigation commands (next, previous, first, last) to actual bookmark names."""
    # Get the last used bookmark to determine the current position
    last_used_bookmark_obj = get_last_used_bookmark()
    if not last_used_bookmark_obj:
        print(
            f"❌ No last used bookmark found. Cannot navigate with '{navigation_command}'")
        return None

    last_used_bm_dir_slash_abs = last_used_bookmark_obj.get("bookmark_dir_slash_abs")
    last_used_bm_dir_colon_rel = last_used_bookmark_obj.get("bookmark_dir_colon_rel")

    if not last_used_bm_dir_slash_abs:
        print(
            f"❌ Could not find folder directory for '{last_used_bm_dir_slash_abs}'")
        return 1

    target_bookmark = None

    target_bookmark = find_sibling_bookmark_in_folder(last_used_bookmark_obj, navigation_command)
    if not target_bookmark:
        print(
            f"❌ No next bookmark found after '{last_used_bm_dir_colon_rel}'")
        return None


    target_bookmark_obj = convert_exact_bookmark_path_to_bm_obj(target_bookmark)
    print(
        f"🎯 Navigating to: {target_bookmark_obj['bookmark_path_colon_rel']}")
    return target_bookmark_obj
