import os
from typing import Any, Dict, cast

from app.consts.bookmarks_consts import (
    ABS_OBS_BOOKMARKS_DIR,
    HIDDEN_COLOR,
    NON_NAME_BOOKMARK_KEYS,
    RESET_COLOR,
)
from app.tags.tag_utils import get_effective_tags
from app.utils.printing_utils import get_embedded_bookmark_file_link, print_color

IS_PRINT_VIDEO_FILE_NAMES = True
IS_HOIST_TAGS_WHEN_SINGLE_CHILD = True
# IS_HOIST_TAGS_WHEN_SINGLE_CHILD = False

IS_DEBUG = True
IS_PRINT_DEF_NAME = True


def print_tree_recursive(
    current_bm_path_colon_rel: str | None,
    is_print_just_current_directory_bookmarks: bool,
    indent_level: int,
    parent_bm_dir_name: str | None,
    parent_bm_dir_col_rel: str | None,
    bookmark_dir_json_without_parent: dict[str, Any],
    full_colon_path_to_here: str,
    inherited_tags: set[str] | None = None,
) -> None:
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
        is_parent_dir_current = (
            current_bm_path_colon_rel
            and parent_bm_dir_col_rel
            and current_bm_path_colon_rel.startswith(parent_bm_dir_col_rel)
        )
        if parent_bm_dir_col_rel is not None:
            parent_bm_path_slash_abs = os.path.join(
                ABS_OBS_BOOKMARKS_DIR, parent_bm_dir_col_rel.replace(":", "/")
            )
        else:
            parent_bm_path_slash_abs = ABS_OBS_BOOKMARKS_DIR

        parent_bm_dir_name_print_string = f"{indent}{get_embedded_bookmark_file_link(parent_bm_path_slash_abs, '📁')} {parent_bm_dir_name}"
        if is_parent_dir_current:
            print_color(parent_bm_dir_name_print_string, "green")
        elif not is_print_just_current_directory_bookmarks:
            print(parent_bm_dir_name_print_string)

    # Recursively gather all tags in this folder

    # Recursively gather all tags in this folder, including tiered auto-tags
    bm_sub_dir_tags: set[str] = set()

    for tag_key in ("tags", "auto_tags_t2", "auto_tags_t3"):
        tag_list = bookmark_dir_json_without_parent.get(tag_key, [])
        if tag_list:
            bm_sub_dir_tags.update(tag_list)

    # TODO(MFB): Do we want to do this?
    # else:
    #     # Prefer node's own tags if present, else compute from children
    #     all_tags = collect_all_bookmark_tags_recursive(bookmark_dir_json_without_parent)
    #     bm_sub_dir_tags = set.intersection(*all_tags) if all_tags else set()

    if is_print_just_current_directory_bookmarks and not is_parent_dir_current:
        bm_sub_dir_tags = set()

    # Print normal tags

    if (
        "tags" in bookmark_dir_json_without_parent
        and bookmark_dir_json_without_parent["tags"]
    ):
        print_color(
            f"{indent}🏷️ {' '.join(f'•{tag}' for tag in sorted(bookmark_dir_json_without_parent['tags']))}",
            "cyan",
        )

    # Print tiered auto-tags
    for tier_key in ("auto_tags_t2", "auto_tags_t3"):
        if (
            tier_key in bookmark_dir_json_without_parent
            and bookmark_dir_json_without_parent[tier_key]
        ):
            print_color(
                f"{indent}🏷️ {' '.join(f'•{tag}' for tag in sorted(bookmark_dir_json_without_parent[tier_key]))}",
                "orange",
            )

    # effective_inherited_tags = inherited_tags | bm_sub_dir_tags

    # Print folder description
    if (
        "description" in bookmark_dir_json_without_parent
        and bookmark_dir_json_without_parent["description"]
    ):
        print_color(
            f"{indent}   {bookmark_dir_json_without_parent['description']}", "cyan"
        )

    # Gather bookmarks and sub_dirs
    bookmarks_in_tree: list[tuple[str, dict[str, Any]]] = []
    sub_dirs_in_tree: list[tuple[str, dict[str, Any]]] = []

    for (
        sub_parent_bm_dir_name,
        sub_dir_json_without_parent,
    ) in bookmark_dir_json_without_parent.items():
        # Skip metadata fields we don't want to recurse into
        if sub_parent_bm_dir_name in NON_NAME_BOOKMARK_KEYS:
            continue

        if isinstance(sub_dir_json_without_parent, dict):
            sub_dir_json_without_parent = cast(
                Dict[str, Any], sub_dir_json_without_parent
            )
            if sub_dir_json_without_parent.get("type") == "bookmark":
                bookmarks_in_tree.append(
                    (sub_parent_bm_dir_name, sub_dir_json_without_parent)
                )
            else:
                sub_dirs_in_tree.append(
                    (sub_parent_bm_dir_name, sub_dir_json_without_parent)
                )
        else:
            print(
                f"WARNING: Unexpected non-dict in print_tree_recursive: key={sub_parent_bm_dir_name} value={repr(sub_dir_json_without_parent)}"
            )

    # Print bookmarks_in_tree at this level (do NOT treat as folders)
    for tree_bookmark_tail_name, tree_bookmark_json in sorted(bookmarks_in_tree):
        # bookmark_tags = set(bookmark_info.get('tags', [])) - effective_inherited_tags
        bookmark_tags = set(get_effective_tags(tree_bookmark_json))
        timestamp = tree_bookmark_json.get("timestamp", "unknown time")
        if len(timestamp) < 5:
            timestamp = "0" + timestamp

        tree_bm_path_col_rel = (
            f"{parent_bm_dir_col_rel}:{tree_bookmark_tail_name}"
            if parent_bm_dir_col_rel
            else tree_bookmark_tail_name
        )
        tree_bm_path_slash_rel = tree_bm_path_col_rel.replace(":", "/")
        tree_bm_path_slash_abs = os.path.join(
            ABS_OBS_BOOKMARKS_DIR, tree_bm_path_slash_rel
        )

        is_current = (
            parent_bm_dir_col_rel
            and current_bm_path_colon_rel
            and current_bm_path_colon_rel.startswith(tree_bm_path_col_rel)
        )

        if is_print_just_current_directory_bookmarks and not is_parent_dir_current:
            continue

        hidden_ref_text = f" {HIDDEN_COLOR} {tree_bm_path_col_rel}{RESET_COLOR}"
        if is_current:
            print(
                f"\033[32m{indent}   • {timestamp} {get_embedded_bookmark_file_link(tree_bm_path_slash_abs, '📖')} {tree_bookmark_tail_name} (current)\033[0m"
                + hidden_ref_text
            )
        else:
            print(
                f"{indent}   • {timestamp} {get_embedded_bookmark_file_link(tree_bm_path_slash_abs, '📖')} {tree_bookmark_tail_name} {hidden_ref_text}"
            )

        bookmark_description = tree_bookmark_json.get("description", "")
        if bookmark_description:
            print_color(f"{indent}      {bookmark_description}", "cyan")
        if bookmark_tags:
            print_color(
                f"{indent}      🏷️ {' '.join(f'•{tag}' for tag in sorted(bookmark_tags))}",
                "cyan",
            )

    # Recurse into sub_dirs_in_tree
    for sub_dir_name, sub_dir_node in sorted(sub_dirs_in_tree):
        next_path = f"{full_colon_path_to_here}:{sub_dir_name}"

        # Only recurse if we're printing the full tree or the subfolder is part of the current path
        if not is_print_just_current_directory_bookmarks or (
            current_bm_path_colon_rel
            and current_bm_path_colon_rel.startswith(next_path)
        ):
            print_tree_recursive(
                current_bm_path_colon_rel=current_bm_path_colon_rel,
                is_print_just_current_directory_bookmarks=is_print_just_current_directory_bookmarks,
                indent_level=indent_level + 1,
                parent_bm_dir_name=sub_dir_name,
                parent_bm_dir_col_rel=next_path,
                bookmark_dir_json_without_parent=sub_dir_node,
                full_colon_path_to_here=next_path,
                # inherited_tags=effective_inherited_tags
            )
