from pprint import pprint
import os
import json
from app.bookmarks_consts import IS_DEBUG, HIDDEN_COLOR, RESET_COLOR, ABS_OBS_BOOKMARKS_DIR
from app.bookmarks_meta import compute_hoistable_tags
from app.bookmarks.last_used import get_last_used_bookmark
from app.bookmarks.finders import get_all_valid_bookmarks_in_json_format
from app.utils import print_color, get_embedded_bookmark_file_link, abs_to_rel_path
from app.utils.decorators import print_def_name

IS_PRINT_VIDEO_FILE_NAMES = True
IS_HOIST_TAGS_WHEN_SINGLE_CHILD = True
# IS_HOIST_TAGS_WHEN_SINGLE_CHILD = False

IS_DEBUG = True
IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def is_ancestor_path(candidate, target):
    """Check if `candidate` is a parent or ancestor of `target` in colon-separated path format."""
    return target == candidate or target.startswith(candidate + ":")


@print_def_name(False) # This is loaded for all bookmarks to create a tree of bookmarks and tags.
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

@print_def_name(IS_PRINT_DEF_NAME)
def print_all_folders_and_bookmarks(
        bookmark_obj=None,
        is_print_just_current_folder_bookmarks=False
        # TODO(KERCH): We no longer have this being used? Re-implement it.
):
    """Print all folders and their bookmarks, highlighting the current one"""

    current_bookmark_name = None
    current_folder_abs_path = None
    current_folder_rel_path = None

    # Get last used bookmark for highlighting if not provided
    if not bookmark_obj:
        last_used_info = get_last_used_bookmark()
        if last_used_info:
            # TODO(MFB):
            print('++++ Make sure these match the deconstruction!')
            print('---- last_used_info:')
            pprint(last_used_info)
            current_bookmark_name = last_used_info.get('bookmark_name', '')
            current_folder_abs_path = last_used_info.get('rel_bookmark_dir', '')
            current_folder_rel_path = abs_to_rel_path(current_folder_abs_path, ABS_OBS_BOOKMARKS_DIR)
    else:
        current_bookmark_name = bookmark_obj["bookmark_tail_name"]
        current_folder_abs_path = bookmark_obj["bookmark_dir_slash_abs"]
        current_folder_rel_path = bookmark_obj["bookmark_dir_slash_rel"]


    if IS_DEBUG:
        print_color('---- current_bookmark_name after:', 'magenta')
        pprint(current_bookmark_name)
        print_color('---- current_folder_rel_path after:', 'magenta')
        pprint(current_folder_rel_path)

    all_bookmarks = get_all_valid_bookmarks_in_json_format()

    def print_tree_recursive(
        node,
        folder_name=None,
        indent_level=0,
        parent_path="",
        current_bookmark_name=None,
        current_folder_abs_path=None,
        inherited_tags=None
    ):
        if inherited_tags is None:
            inherited_tags = set()
        indent = "   " * indent_level

        if folder_name is not None:
            # Compute the full colon path of this folder
            full_folder_path = parent_path  # this folder's colon-style path (already passed in)
            full_last_used_path = f"{current_folder_abs_path}:{current_bookmark_name}" if current_folder_abs_path and current_bookmark_name else ""

            # Should we highlight this folder?
            should_highlight = full_last_used_path == full_folder_path or full_last_used_path.startswith(full_folder_path + ":")

            folder_line = f"{indent}{get_embedded_bookmark_file_link(full_folder_path, '📁')} {folder_name}"
            if should_highlight:
                print_color(folder_line, 'green')
            else:
                print(folder_line)


        # Recursively gather all tags in this folder
        all_tags = collect_all_bookmark_tags_recursive(node)
        folder_tags = set.intersection(*all_tags) if all_tags else set()

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
            full_rel_path = f"{parent_path}:{bookmark_name}" if parent_path else bookmark_name


            # print('---- current_bookmark_name:')
            # pprint(current_bookmark_name)



            full_found_rel_bookmark = f"{full_rel_path}:{bookmark_name}"
            full_current_bookmark = f"{current_folder_rel_path}:{current_bookmark_name}"

            # print('+++++ full_found_rel_bookmark:', full_found_rel_bookmark)
            # print('+++++ full_current_bookmark:', full_current_bookmark)

            is_current = current_bookmark_name and full_found_rel_bookmark == full_current_bookmark

            if is_current:
                print('')
                print('')
                print('')
                print('')
                print('')
                print('')

                print('+++++ is_current !!!!!:')
                print('')
                print('')
                print('')
                print('')
                print('')
                print('')



            hidden_ref_text = f" {HIDDEN_COLOR} {full_rel_path}{RESET_COLOR}"
            if is_current:
                print(
                    f"\033[32m{indent}   • {timestamp} {get_embedded_bookmark_file_link(full_rel_path, '📖')} {bookmark_name} (current)\033[0m" + hidden_ref_text)
            elif full_rel_path == f"{current_folder_abs_path}:{current_bookmark_name}":
                print(
                    f"{indent}   • {timestamp} {get_embedded_bookmark_file_link(full_rel_path, '📖')} \033[32m{bookmark_name} (current)\033[0m" + hidden_ref_text)
            else:
                print(
                    f"{indent}   • {timestamp} {get_embedded_bookmark_file_link(full_rel_path, '📖')} {bookmark_name} {hidden_ref_text}")

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
                current_folder_abs_path=current_folder_abs_path,
                inherited_tags=effective_inherited_tags
            )


    # Start printing from the root level
    for folder_name, folder_node in all_bookmarks.items():
        print_tree_recursive(
            node=all_bookmarks[folder_name],
            folder_name=folder_name,
            indent_level=0,
            parent_path=folder_name,
            current_bookmark_name=current_bookmark_name,
            current_folder_abs_path=current_folder_abs_path
        )


    print('')
    print("=" * 50)

    if current_bookmark_name and current_folder_abs_path:
        current_bookmark = current_folder_abs_path + ":" + current_bookmark_name
        rel_current_bookmark = abs_to_rel_path(current_bookmark, ABS_OBS_BOOKMARKS_DIR)
        rel_current_bookmark = rel_current_bookmark.replace('/', ':')
    else:
        current_bookmark = None
        rel_current_bookmark = None
        rel_current_bookmark = None

    print_color(f"🔍 Current bookmark: bm {rel_current_bookmark}", 'magenta')
    return


@print_def_name(IS_PRINT_DEF_NAME)
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
    #     current_folder_abs_path=full_folder_path,
    #     current_bookmark_name=None,
    #     is_print_just_current_folder_bookmarks=True
    # )
