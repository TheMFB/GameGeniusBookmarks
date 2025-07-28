import os
from pprint import pprint

from app.utils.printing_utils import *
from app.bookmarks.bookmarks import load_bookmarks_from_folder
from app.bookmarks.last_used import get_last_used_bookmark
from app.utils.decorators import print_def_name

IS_AGGREGATE_TAGS = False
IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def find_preceding_bookmark_args(bookmark_name, folder_dir):
    # TODO(MFB): Look into me and see if this is the bookmark name or the whole bookmark (path+name)
    """Find the bookmark that comes alphabetically/numerically before the given bookmark"""
    print_color('??? ---- find_preceding_bookmark_args bookmark_name:', 'red')
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


@print_def_name(IS_PRINT_DEF_NAME)
def find_next_bookmark_in_folder(current_bookmark_name, bookmark_dir):
    """Find the next bookmark in the same directory as the current bookmark."""
    print_color(
        '??? ---- find_next_bookmark_in_folder current_bookmark_name:', 'red')
    pprint(current_bookmark_name)
    print_color('??? ---- find_next_bookmark_in_folder bookmark_dir:', 'red')
    pprint(bookmark_dir)

    all_bookmark_objects = load_bookmarks_from_folder(bookmark_dir)
    if not all_bookmark_objects:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(
        current_path_parts) > 1 else 'root'
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


@print_def_name(IS_PRINT_DEF_NAME)
def find_previous_bookmark_in_folder(current_bookmark_name, folder_dir):
    """Find the previous bookmark in the same directory as the current bookmark."""
    print_color(
        '??? ---- find_previous_bookmark_in_folder current_bookmark_name:', 'red')
    pprint(current_bookmark_name)
    print_color('??? ---- find_previous_bookmark_in_folder folder_dir:', 'red')
    pprint(folder_dir)

    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(
        current_path_parts) > 1 else 'root'
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


@print_def_name(IS_PRINT_DEF_NAME)
def find_first_bookmark_in_folder(current_bookmark_name, folder_dir):
    """Find the first bookmark in the same directory as the current bookmark."""
    print_color(
        '??? ---- find_first_bookmark_in_folder current_bookmark_name:', 'red')
    pprint(current_bookmark_name)
    print_color('??? ---- find_first_bookmark_in_folder folder_dir:', 'red')
    pprint(folder_dir)

    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(
        current_path_parts) > 1 else 'root'

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


@print_def_name(IS_PRINT_DEF_NAME)
def find_last_bookmark_in_folder(current_bookmark_name, folder_dir):
    """Find the last bookmark in the same directory as the current bookmark."""
    print_color(
        '??? ---- find_last_bookmark_in_folder current_bookmark_name:', 'red')
    pprint(current_bookmark_name)
    print_color('??? ---- find_last_bookmark_in_folder folder_dir:', 'red')
    pprint(folder_dir)

    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return None

    # Get all bookmarks in the same directory as the current bookmark
    current_path_parts = current_bookmark_name.split('/')
    current_folder_path = '/'.join(current_path_parts[:-1]) if len(
        current_path_parts) > 1 else 'root'

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


@print_def_name(IS_PRINT_DEF_NAME)
def resolve_navigation_bookmark(navigation_command, folder_dir):
    """Resolve navigation commands (next, previous, first, last) to actual bookmark names."""
    # Get the last used bookmark to determine the current position
    last_used_info = get_last_used_bookmark()
    if not last_used_info:
        print(
            f"❌ No last used bookmark found. Cannot navigate with '{navigation_command}'")
        return None, None

    folder_name = last_used_info.get("folder_name")
    bookmark_name = last_used_info.get("bookmark_name")

    # Convert colons back to slashes for internal processing
    bookmark_name_slashes = bookmark_name.replace(':', '/')

    # Verify the folder matches
    folder_basename = os.path.basename(folder_dir)
    if folder_basename != folder_name:
        print(
            f"❌ Folder mismatch. Last used bookmark is in '{folder_name}', but current folder is '{folder_basename}'")
        return None, None

    # Resolve the navigation command
    if navigation_command == "next":
        target_bookmark = find_next_bookmark_in_folder(
            bookmark_name_slashes, folder_dir)
        if not target_bookmark:
            print(f"❌ No next bookmark found after '{bookmark_name}'")
            return None, None
    elif navigation_command == "previous":
        target_bookmark = find_previous_bookmark_in_folder(
            bookmark_name_slashes, folder_dir)
        if not target_bookmark:
            print(f"❌ No previous bookmark found before '{bookmark_name}'")
            return None, None
    elif navigation_command == "first":
        target_bookmark = find_first_bookmark_in_folder(
            bookmark_name_slashes, folder_dir)
        if not target_bookmark:
            print(
                f"❌ No bookmarks found in the same directory as '{bookmark_name}'")
            return None, None
    elif navigation_command == "last":
        target_bookmark = find_last_bookmark_in_folder(
            bookmark_name_slashes, folder_dir)
        if not target_bookmark:
            print(
                f"❌ No bookmarks found in the same directory as '{bookmark_name}'")
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
    print(
        f"🎯 Navigating to: {folder_name}:{target_bookmark.replace('/', ':')}")
    return target_bookmark, bookmark_info
