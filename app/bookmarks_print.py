# type: ignore
"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
from pprint import pprint
import os
import json
from app.bookmarks_consts import IS_DEBUG, HIDDEN_COLOR, RESET_COLOR, USAGE_HELP
from app.bookmarks_folders import get_all_active_folders, find_folder_by_name
from app.bookmarks_meta import load_folder_meta, compute_hoistable_tags, load_last_used_bookmark_path
from app.bookmarks import load_bookmarks_from_folder, get_last_used_bookmark, get_bookmark_info, get_all_bookmarks_in_json_format
from app.utils import print_color

IS_PRINT_VIDEO_FILE_NAMES = True
IS_PULL_TAGS_WHEN_SINGLE_CHILD = True
# IS_PULL_TAGS_WHEN_SINGLE_CHILD = False

IS_DEBUG = True

def collect_all_bookmark_tags_recursive(node):
    """Recursively gather all tags from bookmarks inside a folder"""
    all_tags = []

    for key, value in node.items():
        if isinstance(value, dict):
            if value.get('type') == 'bookmark':
                all_tags.append(set(value.get('tags', [])))
            else:
                # Recurse into subfolder
                all_tags.extend(collect_all_bookmark_tags_recursive(value))

    return all_tags

def print_all_folders_and_bookmarks(
        current_folder_path=None,
        current_bookmark_name=None,
        current_bookmark_info=None,
        is_print_just_current_folder_bookmarks=False
):
    current_folder_path, current_bookmark_name = load_last_used_bookmark_path()

    """Print all folders and their bookmarks, highlighting the current one"""

    if IS_DEBUG:
        print_color('---- current_folder_path:', 'magenta')
        pprint(current_folder_path)
        print_color('---- current_bookmark_name:', 'magenta')
        pprint(current_bookmark_name)


    # Get last used bookmark for highlighting if not provided
    if not current_bookmark_name:
        last_used_info = get_last_used_bookmark()
        if last_used_info:
            current_bookmark_name = last_used_info.get('bookmark_name', '')
            current_folder_path = last_used_info.get('folder_name', '')

    if IS_DEBUG:
        print_color('---- current_bookmark_name after:', 'magenta')
        pprint(current_bookmark_name)
        print_color('---- current_folder_path after:', 'magenta')
        pprint(current_folder_path)

    all_bookmarks = get_all_bookmarks_in_json_format()

    def print_tree_recursive(
        node,
        folder_name=None,
        indent_level=0,
        parent_path="",
        current_bookmark_name=None,
        inherited_tags=None
    ):
        if inherited_tags is None:
            inherited_tags = set()
        indent = "   " * indent_level

        # Only print folder name if it's not the root
        if folder_name is not None:
            # Build the full path for this folder
            this_folder_path = parent_path
            is_current_folder = (
                current_bookmark_name and
                (current_bookmark_name == this_folder_path or current_bookmark_name.startswith(this_folder_path + ":"))
            )
            clean_folder_name = "" if folder_name == "root" else folder_name
            if clean_folder_name:
                if is_current_folder:
                    print_color(f"{indent}📁 {clean_folder_name}", 'green')
                else:
                    print(f"{indent}📁 {clean_folder_name}")



        # Recursively gather all tags in this folder
        all_tags = collect_all_bookmark_tags_recursive(node)

        # Defensive: filter out any empty or invalid tag sets
        valid_tag_sets = [s for s in all_tags if isinstance(s, set) and s]
        folder_tags = compute_hoistable_tags(all_tags)

        if folder_tags:
            print_color(f"{indent}🏷️ {' '.join(f'•{tag}' for tag in sorted(folder_tags))}", 'cyan')

        effective_inherited_tags = inherited_tags | folder_tags

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
            bookmark_tags = set(bookmark_info.get('tags', [])) - effective_inherited_tags
            timestamp = bookmark_info.get('timestamp', 'unknown time')
            if len(timestamp) < 5:
                timestamp = '0' + timestamp

            path_parts = parent_path.split(':') if parent_path else []
            if path_parts and path_parts[0] == 'root':
                path_parts = path_parts[1:]
            full_path = ":".join(path_parts + [bookmark_name])

            is_last_used = (
                current_folder_path and current_bookmark_name and
                full_path == f"{current_folder_path}:{bookmark_name}"
            )
            star_prefix = "★ " if is_last_used else "  "

            is_current = (
                current_bookmark_name and full_path == current_bookmark_name
            )

            # Determine if this is the last used bookmark
            last_used_match = (
                current_folder_path and current_bookmark_name and
                full_path == f"{current_folder_path}:{current_bookmark_name}"
)

            prefix = "★ " if last_used_match else "  "
            if is_current:
                print(f"\033[32m{indent}{prefix}• {timestamp} 📖 {full_path} (current)\033[0m")
            else:
                print(f"{indent}{prefix}• {timestamp} 📖 {full_path}")



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
                current_bookmark_name=current_bookmark_name,
                inherited_tags=effective_inherited_tags
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

    # TODO(MFB): The current folder path is os-based and only has the basename, and the bookmark name contains pathing.
    # if '/' in current_folder_path:
    #     current_folder_path = current_folder_path.split('/')[-1]
    # current_bookmark = current_folder_path + ":" + current_bookmark_name
    # current_bookmark = current_bookmark.replace('/', ':')
    # print_color(f"🔍 Current bookmark: bm {current_bookmark}", 'magenta')

    return


def print_bookmarks_in_folder(folder_path, indent=0, last_used_path=None, inherited_tags=None):
    if inherited_tags is None:
        inherited_tags = set()

    folder_name = os.path.basename(folder_path)
    print(" " * indent + f"📁 {folder_name}")

    bookmark_tags_list = []
    child_bookmarks = []
    subfolders = []

    for entry in sorted(os.listdir(folder_path)):
        entry_path = os.path.join(folder_path, entry)
        if os.path.isdir(entry_path):
            subfolders.append(entry_path)
        elif entry == "bookmark_meta.json":
            with open(entry_path) as f:
                meta = json.load(f)
                tags = set(meta.get("tags", []))
                bookmark_tags_list.append(tags)
                child_bookmarks.append((entry_path, meta))

    folder_tags = compute_hoistable_tags(bookmark_tags_list)

    # Print folder-level tags (only if not already inherited)
    printable_tags = folder_tags - inherited_tags
    if printable_tags:
        tag_str = " ".join([f"•{tag}" for tag in sorted(printable_tags)])
        print(" " * (indent + 3) + f"🏷️ {tag_str}")

    # Print each bookmark, omitting inherited or folder-level tags
    for entry_path, meta in child_bookmarks:
        bookmark_dir = os.path.dirname(entry_path)
        bookmark_name = os.path.basename(bookmark_dir)
        tags = set(meta.get("tags", []))
        visible_tags = tags - folder_tags - inherited_tags
        time_str = meta.get("timestamp_formatted", "--:--")
        tag_str = " ".join([f"•{tag}" for tag in sorted(visible_tags)])
        display_line = f"{time_str} 📖 {bookmark_name}"
        if bookmark_dir == last_used_path:
            display_line += " ← last used"
        print(" " * (indent + 3) + f"• {display_line}")
        if tag_str:
            print(" " * (indent + 6) + f"🏷️ {tag_str}")

    # Recurse into subfolders
    for subfolder in subfolders:
        print_bookmarks_in_folder(subfolder, indent + 3, last_used_path, inherited_tags | folder_tags)

    # print_color('---- 2 full_folder_path:', 'magenta')
    # pprint(full_folder_path)

    # print_all_folders_and_bookmarks(
    #     current_folder_path=full_folder_path,
    #     current_bookmark_name=None,
    #     is_print_just_current_folder_bookmarks=True
    # )
