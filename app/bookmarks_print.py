# type: ignore
"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
from pprint import pprint
import os
import json
from app.bookmarks_consts import IS_DEBUG, HIDDEN_COLOR, RESET_COLOR, USAGE_HELP
from app.bookmarks_folders import get_all_active_folders, find_folder_by_name
from app.bookmarks_meta import load_folder_meta
from app.bookmarks import load_bookmarks_from_folder, get_last_used_bookmark, get_bookmark_info
from app.utils import print_color

IS_PRINT_VIDEO_FILE_NAMES = True

def print_all_folders_and_bookmarks(
        top_level_folder_name=None,
        current_bookmark_name=None,
        current_bookmark_info=None,
        is_print_just_current_folder_bookmarks=False
):
    """Print all folders and their bookmarks, highlighting the current one"""
    active_folders = get_all_active_folders()

    if IS_DEBUG:
        print_color('---- top_level_folder_name:', 'red')
        pprint(top_level_folder_name)
        print_color('---- current_bookmark_name:', 'red')
        pprint(current_bookmark_name)

    if not active_folders:
        print("❌ No active folders found")
        return

    # Get last used bookmark for highlighting if not provided
    if not current_bookmark_name:
        last_used_info = get_last_used_bookmark()
        if last_used_info:
            # Extract the folder name from the full path in the state file
            folder_name_from_state = last_used_info.get("folder_name")
            bookmark_name_from_state = last_used_info.get("bookmark_name")

            # Only proceed if both folder_name and bookmark_name are not None
            if folder_name_from_state and bookmark_name_from_state:
                # Convert colons back to slashes for internal processing
                bookmark_name_slashes = bookmark_name_from_state.replace(':', '/')

                # The folder_name in the state file might be the full path or just the basename
                # Let's try to find the correct folder by matching against all folder paths
                found_folder = None
                for folder_path in active_folders:
                    folder_basename = os.path.basename(folder_path)
                    # Check if the folder name from state matches either the full path or basename
                    if (folder_name_from_state == folder_path or
                        folder_name_from_state == folder_basename or
                        folder_name_from_state in folder_path):
                        found_folder = folder_path
                        break

                if found_folder:
                    top_level_folder_name = found_folder  # use full folder path instead of just basename
                    current_bookmark_name = bookmark_name_slashes  # Use the slash version for internal processing
                    if IS_DEBUG:
                        print(f"📌 Using last used bookmark: {top_level_folder_name}:{bookmark_name_from_state}")
                else:
                    if IS_DEBUG:
                        print(f"⚠️  Could not find folder '{folder_name_from_state}' in active folders")
            else:
                if IS_DEBUG:
                    print(f"⚠️  Last used bookmark info incomplete: folder_name='{folder_name_from_state}', bookmark_name='{bookmark_name_from_state}'")

    # Filter folders if we only want to show current folder
    if is_print_just_current_folder_bookmarks and top_level_folder_name:
        # Find the folder directory for the current folder
        current_folder_dir = None
        for folder_path in active_folders:
            folder_name = os.path.basename(folder_path)
            if folder_name == top_level_folder_name:
                current_folder_dir = folder_path
                break

        if current_folder_dir:
            active_folders = [current_folder_dir]
        else:
            # If we can't find the current folder, show all folders
            if IS_DEBUG:
                print(f"⚠️  Could not find folder '{top_level_folder_name}', showing all folders")

    for folder_path in active_folders:
        folder_name = os.path.basename(folder_path)
        is_current_folder = folder_path == top_level_folder_name

        # Print folder name
        if is_current_folder:
            print_color(f"📁 {folder_name}", 'green')
        else:
            if not is_print_just_current_folder_bookmarks:
                print(f"📁 {folder_name}")

        # Load folder metadata and display description if it exists
        folder_meta = load_folder_meta(folder_path)
        folder_description = folder_meta.get('description', '')
        if folder_description:
            if not is_print_just_current_folder_bookmarks or is_current_folder:
                print_color(f"   {folder_description}", 'cyan')

        # Load folder metadata and display tags if they exist
        folder_meta = load_folder_meta(folder_path)
        folder_tags = folder_meta.get('tags', [])
        if folder_tags and (not is_print_just_current_folder_bookmarks or is_current_folder):
            print_color(
                f"   {' '.join(f'•{tag}' for tag in folder_tags)}", 'cyan')

        # Load and print bookmarks for this folder
        bookmarks = load_bookmarks_from_folder(folder_path)
        if IS_DEBUG:
            print('')
            print('')
            print('')
            print('')
            print('')
            print('')

            print(f"🔍 Debug - All bookmarks in {folder_name}:")
            pprint(bookmarks)

        if bookmarks:
            from collections import defaultdict

            # Step 1: Build folder and bookmark hierarchies
            # full_folder_path -> list of (bookmark_name, bookmark_info)
            folder_hierarchy = defaultdict(list)
            # parent_folder_path -> list of child folder paths
            folder_tree = defaultdict(list)

            if IS_DEBUG:
                print(f"🔍 Debug - All bookmarks in {folder_name}:")
                for path, info in sorted(bookmarks.items()):
                    print(
                        f"   {path} -> {info.get('timestamp_formatted', 'unknown')}")
                print()

            for bookmark_path, bookmark_info in bookmarks.items():
                path_parts = bookmark_path.split('/')

                if len(path_parts) == 1:
                    folder_hierarchy['root'].append(
                        (bookmark_path, bookmark_info))
                    if IS_DEBUG:
                        print(
                            f"🔍 Debug - Added root bookmark: {bookmark_path}")
                else:
                    full_folder_path = '/'.join(path_parts[:-1])
                    bookmark_name = path_parts[-1]
                    folder_hierarchy[full_folder_path].append(
                        (bookmark_name, bookmark_info))
                    if IS_DEBUG:
                        print(
                            f"🔍 Debug - Added bookmark {bookmark_name} to folder {full_folder_path}")

                    # Build the folder tree structure
                    for i in range(1, len(path_parts)):
                        parent = '/'.join(path_parts[:i-1]
                                          ) if i > 1 else 'root'
                        child = '/'.join(path_parts[:i])
                        if child not in folder_tree[parent]:
                            folder_tree[parent].append(child)
                            if IS_DEBUG:
                                print(
                                    f"🔍 Debug - Added folder {child} under {parent}")

            if IS_DEBUG:
                print(f"🔍 Debug - Folder hierarchy for {folder_name}:")
                for folder, bookmarks_in_folder in sorted(folder_hierarchy.items()):
                    print(
                        f"   {folder}: {[b[0] for b in bookmarks_in_folder]}")
                print()

            def print_folder_contents(folder_path, indent_level):
                indent = "   " * indent_level

                # Print folder (skip for 'root')
                folder_name = folder_path.split('/')[-1] if folder_path != 'root' else 'root'

                # Highlight if this folder contains current bookmark
                folder_contains_current = False
                if current_bookmark_name and is_current_folder:
                    current_path_parts = current_bookmark_name.split('/')
                    current_folder_path = '/'.join(current_path_parts[:-1])
                    folder_contains_current = folder_path == current_folder_path or current_folder_path.startswith(
                        folder_path + '/')

                # Don't print the "root" folder name - just show bookmarks directly under the main folder
                if folder_path != 'root':
                    if folder_contains_current:
                        print_color(f"{indent}📁 {folder_name}", 'green')
                    else:
                        if not is_print_just_current_folder_bookmarks:
                            print(f"{indent}📁 {folder_name}")

                # Load and display folder metadata
                folder_meta = load_folder_meta(
                    os.path.join(folder_path, folder_path))
                folder_description = folder_meta.get('description', '')
                folder_tags = folder_meta.get('tags', [])

                if folder_description:
                    print_color(f"{indent}   {folder_description}", 'cyan')

                if folder_tags:
                    print_color(
                        f"{indent}   {' '.join(f'•{tag}' for tag in folder_tags)}", 'cyan')

                # Print bookmarks directly in this folder
                bookmarks_in_folder = folder_hierarchy.get(folder_path, [])

                # Filter bookmarks if we're in just-current mode and this is the current folder
                if is_print_just_current_folder_bookmarks and is_current_folder and current_bookmark_name:
                    current_path_parts = current_bookmark_name.split('/')
                    current_folder_path = '/'.join(current_path_parts[:-1])

                    # For root-level bookmarks (no slashes), show all root bookmarks
                    if len(current_path_parts) == 1:
                        # Current bookmark is at root level, show all root bookmarks
                        if folder_path == 'root':
                            filtered_bookmarks = bookmarks_in_folder
                        else:
                            # Don't show bookmarks from other folders
                            filtered_bookmarks = []
                    else:
                        # Current bookmark is in a subfolder, only show bookmarks in that folder
                        if folder_path == current_folder_path:
                            # Show all bookmarks in the current folder (neighbors)
                            filtered_bookmarks = bookmarks_in_folder
                        else:
                            # Don't show bookmarks from other folders
                            filtered_bookmarks = []
                else:
                    # Show all bookmarks (normal mode)
                    filtered_bookmarks = bookmarks_in_folder

                if IS_PRINT_VIDEO_FILE_NAMES:
                    # Collect unique video file names from bookmarks in this folder
                    video_file_names = set()
                    for bookmark_name, bookmark_info in filtered_bookmarks:
                        bookmark_video_name = bookmark_info.get('video_filename', '')
                        if bookmark_video_name:
                            # Handle both single string and list of strings
                            if isinstance(bookmark_video_name, str):
                                video_file_names.add(bookmark_video_name)
                            elif isinstance(bookmark_video_name, list):
                                video_file_names.update(bookmark_video_name)

                # Display video file names if any exist
                if video_file_names and (not is_print_just_current_folder_bookmarks or is_current_folder):
                    print_color(f"{indent}    {', '.join(sorted(video_file_names))}", 'magenta')

                for bookmark_name, bookmark_info in sorted(filtered_bookmarks):
                    timestamp = bookmark_info.get(
                        'timestamp_formatted', 'unknown time')
                    if len(timestamp) < 5:
                        timestamp = '0' + timestamp

                    # Construct full path - treat all bookmarks the same way
                    full_path = f"{folder_path}/{bookmark_name}" if folder_path != 'root' else bookmark_name
                    is_current = (
                        folder_name == top_level_folder_name and full_path == current_bookmark_name)

                    # Check if this is the last used bookmark
                    is_last_used = False
                    if current_bookmark_name and is_current_folder:
                        is_last_used = full_path == current_bookmark_name

                    # Construct ref_path including the top-level folder name - treat all bookmarks consistently
                    # Use the current folder_name (which is the basename of the folder_path)
                    ref_path = f"{folder_name}:{full_path}" if folder_name else full_path
                    ref_path = ref_path.replace('/', ':')
                    hidden_ref_text = f" {HIDDEN_COLOR} {ref_path}{RESET_COLOR}"

                    if is_current:
                        # print_color(
                        #     f"{indent}   • {timestamp} 📖 {bookmark_name} (current)", 'green')
                        print(
                            f"\033[32m{indent}   • {timestamp} 📖 {bookmark_name} (current)\033[0m" + hidden_ref_text)
                    elif is_last_used:
                        # print_color(
                        #     f"{indent}   • {timestamp} 📌 {bookmark_name} (last used)", 'yellow')
                        print(
                            f"\033[32m{indent}   • {timestamp} 📖 {bookmark_name} (last used)\033[0m" + hidden_ref_text)
                    else:
                        print(
                            f"{indent}   • {timestamp} 📖 {bookmark_name} {hidden_ref_text}")

                    # Bookmark description
                    bookmark_description = bookmark_info.get('description', '')
                    if bookmark_description:
                        print_color(
                            f"{indent}      {bookmark_description}", 'cyan')

                    # Bookmark tags
                    bookmark_tags = bookmark_info.get('tags', [])
                    if bookmark_tags:
                        print_color(
                            f"{indent}      {' '.join(f'•{tag}' for tag in bookmark_tags)}", 'cyan')

                # Recurse into subfolders only if we're not in just-current mode or if this folder contains the current bookmark
                if not is_print_just_current_folder_bookmarks or (is_current_folder and current_bookmark_name):
                    current_path_parts = current_bookmark_name.split('/') if current_bookmark_name else []
                    current_folder_path = '/'.join(current_path_parts[:-1]) if current_path_parts else ""

                    # Only recurse if this folder is on the path to the current bookmark
                    should_recurse = (not is_print_just_current_folder_bookmarks or
                                    folder_path == 'root' or
                                    current_folder_path.startswith(folder_path + '/'))

                    if should_recurse:
                        for child_folder in sorted(folder_tree.get(folder_path, [])):
                            print_folder_contents(child_folder, indent_level + 1)

            # Start the recursive display from root
            print_folder_contents('root', indent_level=0)
        else:
            print("   (no bookmarks)")

        print()  # Empty line between folders

    print('')
    # Convert slashes to colons for display
    # Convert slashes to colons for display
    display_bookmark_name = current_bookmark_name.replace('/', ':') if current_bookmark_name else ''
    folder_display_name = os.path.basename(top_level_folder_name) if top_level_folder_name else ''

    print(f"runonce-redis \033[34m{folder_display_name}:{display_bookmark_name}\033[0m")
    if not current_bookmark_info:
        _matched_bookmark_name, current_bookmark_info = get_bookmark_info(
            f"{folder_display_name}:{display_bookmark_name}")

    if current_bookmark_info:
        print_color(
            f"   {current_bookmark_info.get('video_filename', '')} - ({current_bookmark_info.get('timestamp_formatted', '')})", 'magenta')
        if current_bookmark_info.get('description', ''):
            print(f"   {current_bookmark_info.get('description', '')}")
        if current_bookmark_info.get('tags', []):
            print(f"   {current_bookmark_info.get('tags', [])}")
    print(f"   {USAGE_HELP}")


    print("=" * 50)
    return


def print_bookmarks_in_folder(folder_path):
    """Helper for -ls <folder>: Print bookmarks in the given folder only."""
    from app.bookmarks_consts import BOOKMARKS_DIR

    # Normalize input: convert relative folder to absolute
    full_folder_path = os.path.join(BOOKMARKS_DIR, folder_path)
    full_folder_path = os.path.normpath(full_folder_path)

    # DEBUG: Show the folder we're trying to match
    print("🔍 Checking for exact match:")
    print(f"   full_folder_path: {full_folder_path}")

    active_folders = get_all_active_folders()

    print("📂 Active folders:")
    for f in active_folders:
        print(f"   {f}")

    # Now test for match
    if full_folder_path not in active_folders:
        print(f"❌ Folder '{folder_path}' not found (no fuzzy matching allowed with -ls)")
        return

    print_all_folders_and_bookmarks(
        top_level_folder_name=full_folder_path,
        current_bookmark_name=None,
        is_print_just_current_folder_bookmarks=True
    )



