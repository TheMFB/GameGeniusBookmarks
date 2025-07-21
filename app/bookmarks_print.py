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
        current_folder_path=None,
        current_bookmark_name=None,
        current_bookmark_info=None,
        is_print_just_current_folder_bookmarks=False
):
    """Print all folders and their bookmarks, highlighting the current one"""

    # Get last used bookmark for highlighting if not provided
    if not current_bookmark_name:
        last_used_info = get_last_used_bookmark()
        if last_used_info:
            current_bookmark_name = last_used_info.get('bookmark_name', '')
            current_folder_path = last_used_info.get('folder_name', '')

    all_bookmarks = get_all_bookmarks_in_json_format()

    def print_tree_recursive(
        node,
        folder_name=None,
        indent_level=0,
        parent_path="",
        current_bookmark_name=None
    ):
        indent = "   " * indent_level

        # Only print folder name if it's not the root
        if folder_name is not None:
            # Build the full path for this folder
            this_folder_path = parent_path
            is_current_folder = (
                current_bookmark_name and
                (current_bookmark_name == this_folder_path or current_bookmark_name.startswith(this_folder_path + ":"))
            )
            if is_current_folder:
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

        # Print bookmarks at this level (do NOT treat as folders)
        for bookmark_name, bookmark_info in sorted(bookmarks):
            bookmark_tags = set(bookmark_info.get('tags', []))
            timestamp = bookmark_info.get('timestamp', 'unknown time')
            if len(timestamp) < 5:
                timestamp = '0' + timestamp
            full_path = f"{parent_path}:{bookmark_name}" if parent_path else bookmark_name
            is_current = (
                current_bookmark_name and
                (current_bookmark_name == full_path or current_bookmark_name.endswith(":" + bookmark_name))
            )
            hidden_ref_text = f" {HIDDEN_COLOR} {full_path}{RESET_COLOR}"
            if is_current:
                print(f"\033[32m{indent}   • {timestamp} 📖 {bookmark_name} (current)\033[0m" + hidden_ref_text)
            else:
                print(f"{indent}   • {timestamp} 📖 {bookmark_name} {hidden_ref_text}")
            bookmark_description = bookmark_info.get('description', '')
            if bookmark_description:
                print_color(f"{indent}      {bookmark_description}", 'cyan')
            if bookmark_tags:
                print_color(f"{indent}      🏷️ {' '.join(f'•{tag}' for tag in sorted(bookmark_tags))}", 'cyan')

        # Recurse into subfolders
        for subfolder_name, subfolder_node in sorted(subfolders):
            next_path = f"{parent_path}:{subfolder_name}" if parent_path else subfolder_name
            print_tree_recursive(
                subfolder_node,
                subfolder_name,
                indent_level + 1,
                next_path,
                current_bookmark_name=current_bookmark_name
            )

    # Start printing from the root level
    for folder_name, folder_node in all_bookmarks.items():
        print_tree_recursive(
            node=all_bookmarks[folder_name],
            folder_name=folder_name,
            indent_level=0,
            parent_path=folder_name,
            current_bookmark_name=current_bookmark_name
        )

    print('')
    print("=" * 50)
    # TODO(MFB): Print the last used/current bookmark quick reference

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
        current_folder_path=full_folder_path,
        current_bookmark_name=None,
        is_print_just_current_folder_bookmarks=True
    )



