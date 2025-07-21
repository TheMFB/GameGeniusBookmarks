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
from app.bookmarks import load_bookmarks_from_folder, get_last_used_bookmark, get_bookmark_info, get_all_bookmarks_in_json_format
from app.utils import print_color

IS_PRINT_VIDEO_FILE_NAMES = True
IS_PULL_TAGS_WHEN_SINGLE_CHILD = True
# IS_PULL_TAGS_WHEN_SINGLE_CHILD = False

IS_DEBUG = True

def print_all_folders_and_bookmarks(
        folder_path=None,
        current_bookmark_name=None,
        current_bookmark_info=None,
        is_print_just_current_folder_bookmarks=False
):
    """Print all folders and their bookmarks, highlighting the current one"""

    if IS_DEBUG:
        print_color('---- folder_path:', 'red')
        pprint(folder_path)
        print_color('---- current_bookmark_name:', 'red')
        pprint(current_bookmark_name)

    # Get last used bookmark for highlighting if not provided
    if not current_bookmark_name:
        last_used_info = get_last_used_bookmark()
        if last_used_info:
            current_bookmark_name = last_used_info.get('bookmark_name', '')
            folder_path = last_used_info.get('folder_name', '')


    # # Filter folders if we only want to show current folder
    # if is_print_just_current_folder_bookmarks and folder_path:
    #     # Find the folder directory for the current folder
    #     current_folder_dir = None
    #     for folder_path in active_folders:
    #         folder_name = os.path.basename(folder_path)
    #         if folder_name == folder_path:
    #             current_folder_dir = folder_path
    #             break

    #     if current_folder_dir:
    #         active_folders = [current_folder_dir]
    #     else:
    #         # If we can't find the current folder, show all folders
    #         if IS_DEBUG:
    #             print(f"⚠️  Could not find folder '{folder_path}', showing all folders")

    all_bookmarks = get_all_bookmarks_in_json_format()

    pprint(all_bookmarks)

    def print_tree_recursive(node, folder_name=None, indent_level=0, parent_common_tags=None, parent_path=""):
        indent = "   " * indent_level

        # Only print folder name if it's not the root
        if folder_name is not None:
            print_color(f"{indent}📁 {folder_name}", 'green')

        # Print folder meta tags (if any)
        if 'tags' in node and node['tags']:
            print_color(f"{indent}🏷️ {' '.join(f'•{tag}' for tag in node['tags'])}", 'cyan')

        # Print folder description
        if 'description' in node and node['description']:
            print_color(f"{indent}   {node['description']}", 'cyan')

        # Gather bookmarks and subfolders
        bookmarks = []
        subfolders = []

        for key, value in node.items():
            if isinstance(value, dict):
                if value.get('type') == 'bookmark':
                    bookmarks.append((key, value))
                elif key not in ['tags', 'description', 'video_filename', 'timestamp', 'type']:
                    subfolders.append((key, value))

        # Calculate common tags among all bookmarks in this folder
        if bookmarks:
            all_bookmark_tags = [set(b[1].get('tags', [])) for b in bookmarks]
            common_tags = set.intersection(*all_bookmark_tags) if all_bookmark_tags else set()
        else:
            common_tags = set()

        # Only print tags that are not already printed by parent
        tags_to_print = common_tags - (parent_common_tags or set())

        # Check if we should pull tags up (more than one child or IS_PULL_TAGS_WHEN_SINGLE_CHILD is True)
        child_count = len(bookmarks) + len(subfolders)
        if child_count == 1 and not IS_PULL_TAGS_WHEN_SINGLE_CHILD:
            tags_to_print = set()

        # Print aggregated tags
        if tags_to_print:
            print_color(f"{indent}🏷️ {' '.join(f'•{tag}' for tag in sorted(tags_to_print))}", 'cyan')

        # Print bookmarks
        for bookmark_name, bookmark_info in sorted(bookmarks):
            bookmark_tags = set(bookmark_info.get('tags', []))
            unique_tags = bookmark_tags - tags_to_print

            timestamp = bookmark_info.get('timestamp', 'unknown time')
            if len(timestamp) < 5:
                timestamp = '0' + timestamp

            # Build full path for ref
            full_path = f"{parent_path}:{bookmark_name}" if parent_path else bookmark_name
            hidden_ref_text = f" {HIDDEN_COLOR} {full_path}{RESET_COLOR}"

            print(f"{indent}   • {timestamp} 📖 {bookmark_name} {hidden_ref_text}")

            bookmark_description = bookmark_info.get('description', '')
            if bookmark_description:
                print_color(f"{indent}      {bookmark_description}", 'cyan')
            if unique_tags:
                print_color(f"{indent}      🏷️ {' '.join(f'•{tag}' for tag in sorted(unique_tags))}", 'cyan')

        # Recurse into subfolders
        for subfolder_name, subfolder_node in sorted(subfolders):
            next_path = f"{parent_path}:{subfolder_name}" if parent_path else subfolder_name
            print_tree_recursive(subfolder_node, subfolder_name, indent_level + 1, tags_to_print, next_path)

    # Start printing from the root level
    for folder_name, folder_node in all_bookmarks.items():
        print_tree_recursive(folder_node, folder_name, indent_level=0, parent_common_tags=None, parent_path=folder_name)

    print('')
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
        folder_path=full_folder_path,
        current_bookmark_name=None,
        is_print_just_current_folder_bookmarks=True
    )



