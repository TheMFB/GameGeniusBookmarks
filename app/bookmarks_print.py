import json
import os

from app.bookmarks.bookmarks import get_all_live_bookmarks_in_json_format
from app.bookmarks.last_used import get_last_used_bookmark
from app.bookmarks_meta import compute_hoistable_tags
from app.consts.bookmarks_consts import (
    ABS_OBS_BOOKMARKS_DIR,
    HIDDEN_COLOR,
    IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS,
    NON_NAME_BOOKMARK_KEYS,
    RESET_COLOR,
)
from app.utils.bookmark_utils import abs_to_rel_path
from app.utils.decorators import only_run_once, print_def_name
from app.utils.printing_utils import get_embedded_bookmark_file_link, print_color

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

    for _key, value in node.items():
        if isinstance(value, dict):
            if value.get('type') == 'bookmark':
                all_tags.append(set(value.get('tags', [])))
            else:
                # Recurse into sub_dir
                all_tags.extend(collect_all_bookmark_tags_recursive(value))

    return all_tags

@print_def_name(False)
@only_run_once
def print_all_live_directories_and_bookmarks(
        is_print_just_current_directory_bookmarks=IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS
):
    """Print all folders and their bookmarks, highlighting the current one"""
    print('')
    print('=' * 50)

    # Get last used bookmark for highlighting if not provided with the current bookmark object.
    last_used_info = get_last_used_bookmark() or {}
    current_bm_tail_name = last_used_info.get('bookmark_tail_name', None)
    current_bm_dir_slash_abs = last_used_info.get('bookmark_dir_slash_abs', None)
    current_bm_path_colon_rel = last_used_info.get('bookmark_path_colon_rel', None)

    all_bookmarks = get_all_live_bookmarks_in_json_format()

    def print_tree_recursive(
        indent_level,
        parent_bm_dir_name,
        parent_bm_dir_col_rel,
        bookmark_dir_json_without_parent,
        inherited_tags=None
    ):
        """
        bookmark_dir_json_without_parent: The JSON object for the current directory, without the parent directory.
        parent_bm_dir_name: The name of the parent directory.
        indent_level: The level of indentation for the current directory.
        parent_bm_dir_col_rel: The relative colon path of the parent directory.
        current_bm_tail_name: The name of the current bookmark.
        current_bm_dir_slash_abs: The absolute path of the current directory.
        inherited_tags: The tags that are inherited from the parent directory.
        """

        if inherited_tags is None:
            inherited_tags = set()
        indent = "   " * indent_level
        is_parent_dir_current = False

        if parent_bm_dir_name is not None:
            # Is this the current directory/bookmark?
            is_parent_dir_current = current_bm_path_colon_rel and parent_bm_dir_col_rel and current_bm_path_colon_rel.startswith(
                parent_bm_dir_col_rel)
            parent_bm_path_slash_abs = os.path.join(
                ABS_OBS_BOOKMARKS_DIR, parent_bm_dir_col_rel.replace(':', '/'))

            parent_bm_dir_name_print_string = f"{indent}{get_embedded_bookmark_file_link(parent_bm_path_slash_abs, '📁')} {parent_bm_dir_name}"
            if is_parent_dir_current:
                print_color(parent_bm_dir_name_print_string, 'green')
            elif not is_print_just_current_directory_bookmarks:
                print(parent_bm_dir_name_print_string)


        # Recursively gather all tags in this folder
        bm_sub_dir_tags = set()
        if 'tags' in bookmark_dir_json_without_parent and bookmark_dir_json_without_parent['tags']:
            bm_sub_dir_tags = set(bookmark_dir_json_without_parent['tags'])
        # else:
        #     # Prefer node's own tags if present, else compute from children
        #     all_tags = collect_all_bookmark_tags_recursive(bookmark_dir_json_without_parent)
        #     bm_sub_dir_tags = set.intersection(*all_tags) if all_tags else set()

        if bm_sub_dir_tags:
            print_color(f"{indent}🏷️ {' '.join(f'•{tag}' for tag in sorted(bm_sub_dir_tags))}", 'cyan')

        # effective_inherited_tags = inherited_tags | bm_sub_dir_tags

        # Print folder description
        if 'description' in bookmark_dir_json_without_parent and bookmark_dir_json_without_parent['description']:
            print_color(f"{indent}   {bookmark_dir_json_without_parent['description']}", 'cyan')

        # Gather bookmarks and sub_dirs
        bookmarks_in_tree = []
        sub_dirs_in_tree = []

        for sub_parent_bm_dir_name, sub_dir_json_without_parent in bookmark_dir_json_without_parent.items():
            if isinstance(sub_dir_json_without_parent, dict):
                # Sub Dir is a bookmark
                if sub_dir_json_without_parent.get('type') == 'bookmark':
                    bookmarks_in_tree.append((sub_parent_bm_dir_name, sub_dir_json_without_parent))
                # Sub Dir is a directory
                elif sub_parent_bm_dir_name not in NON_NAME_BOOKMARK_KEYS:
                    sub_dirs_in_tree.append((sub_parent_bm_dir_name, sub_dir_json_without_parent))

        # Print bookmarks_in_tree at this level (do NOT treat as folders)
        for tree_bookmark_tail_name, tree_bookmark_json in sorted(bookmarks_in_tree):
            # bookmark_tags = set(bookmark_info.get('tags', [])) - effective_inherited_tags
            bookmark_tags = set(tree_bookmark_json.get('tags', []))
            timestamp = tree_bookmark_json.get('timestamp', 'unknown time')
            if len(timestamp) < 5:
                timestamp = '0' + timestamp

            tree_bm_path_col_rel = f"{parent_bm_dir_col_rel}:{tree_bookmark_tail_name}" if parent_bm_dir_col_rel else tree_bookmark_tail_name
            tree_bm_path_slash_rel = tree_bm_path_col_rel.replace(':', '/')
            tree_bm_path_slash_abs = os.path.join(ABS_OBS_BOOKMARKS_DIR, tree_bm_path_slash_rel)

            is_current = parent_bm_dir_col_rel and current_bm_path_colon_rel and current_bm_path_colon_rel.startswith(tree_bm_path_col_rel)

            if is_print_just_current_directory_bookmarks and not is_parent_dir_current:
                continue

            hidden_ref_text = f" {HIDDEN_COLOR} {tree_bm_path_col_rel}{RESET_COLOR}"
            if is_current:
                print(
                    f"\033[32m{indent}   • {timestamp} {get_embedded_bookmark_file_link(tree_bm_path_slash_abs, '📖')} {tree_bookmark_tail_name} (current)\033[0m" + hidden_ref_text)
            else:
                print(
                    f"{indent}   • {timestamp} {get_embedded_bookmark_file_link(tree_bm_path_slash_abs, '📖')} {tree_bookmark_tail_name} {hidden_ref_text}")

            bookmark_description = tree_bookmark_json.get('description', '')
            if bookmark_description:
                print_color(f"{indent}      {bookmark_description}", 'cyan')
            if bookmark_tags:
                print_color(f"{indent}      🏷️ {' '.join(f'•{tag}' for tag in sorted(bookmark_tags))}", 'cyan')

        # Recurse into sub_dirs_in_tree
        for sub_dir_name, sub_dir_node in sorted(sub_dirs_in_tree):
            next_path = f"{parent_bm_dir_col_rel}:{sub_dir_name}" if parent_bm_dir_col_rel else sub_dir_name
            print_tree_recursive(
                indent_level=indent_level + 1,
                parent_bm_dir_name=sub_dir_name,
                parent_bm_dir_col_rel=next_path,
                bookmark_dir_json_without_parent=sub_dir_node,
                # inherited_tags=effective_inherited_tags
            )

    # Start printing from the root level
    for parent_bm_dir_name, sub_dir_json_without_parent in all_bookmarks.items():
        print('')
        print_tree_recursive(
            indent_level=0,
            parent_bm_dir_name=parent_bm_dir_name,
            parent_bm_dir_col_rel=parent_bm_dir_name,
            bookmark_dir_json_without_parent=sub_dir_json_without_parent,
        )

    print('')
    print("=" * 50)

    if current_bm_tail_name and current_bm_dir_slash_abs:
        current_bookmark = current_bm_dir_slash_abs + ":" + current_bm_tail_name
        rel_current_bookmark = abs_to_rel_path(current_bookmark, ABS_OBS_BOOKMARKS_DIR)
        rel_current_bookmark = rel_current_bookmark.replace('/', ':')
    else:
        current_bookmark = None
        rel_current_bookmark = None
        rel_current_bookmark = None

    print_color(f"🔍 Current bookmark: bm {rel_current_bookmark}", 'magenta')
    return


@print_def_name(IS_PRINT_DEF_NAME)
def print_bookmarks_in_directory(folder_path, indent=0, last_used_path=None, inherited_tags=None):
    if inherited_tags is None:
        inherited_tags = set()

    folder_name = os.path.basename(folder_path)
    print(" " * indent + f"📁 {folder_name}")

    bookmark_tags_list = []
    child_bookmarks = []
    sub_dirs = []

    for entry in sorted(os.listdir(folder_path)):
        entry_path = os.path.join(folder_path, entry)
        if os.path.isdir(entry_path):
            sub_dirs.append(entry_path)
        elif entry == "bookmark_meta.json":
            with open(entry_path) as f:
                meta = json.load(f)
                tags = set(meta.get("tags", []))
                bookmark_tags_list.append(tags)
                child_bookmarks.append((entry_path, meta))

    bm_sub_dir_tags = compute_hoistable_tags(bookmark_tags_list)

    # Print folder-level tags (only if not already inherited)
    printable_tags = bm_sub_dir_tags - inherited_tags
    if printable_tags:
        tag_str = " ".join([f"•{tag}" for tag in sorted(printable_tags)])
        print(" " * (indent + 3) + f"🏷️ {tag_str}")

    # Print each bookmark, omitting inherited or folder-level tags
    for entry_path, meta in child_bookmarks:
        bookmark_dir = os.path.dirname(entry_path)
        bookmark_tail_name = os.path.basename(bookmark_dir)
        tags = set(meta.get("tags", []))
        visible_tags = tags - bm_sub_dir_tags - inherited_tags
        time_str = meta.get("timestamp_formatted", "--:--")
        tag_str = " ".join([f"•{tag}" for tag in sorted(visible_tags)])
        display_line = f"{time_str} 📖 {bookmark_tail_name}"
        if bookmark_dir == last_used_path:
            display_line += " ← last used"
        print(" " * (indent + 3) + f"• {display_line}")
        if tag_str:
            print(" " * (indent + 6) + f"🏷️ {tag_str}")

    # Recurse into sub_dirs
    for sub_dir in sub_dirs:
        print_bookmarks_in_directory(sub_dir, indent + 3, last_used_path, inherited_tags | bm_sub_dir_tags)
