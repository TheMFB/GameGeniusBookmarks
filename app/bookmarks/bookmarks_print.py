from typing import Any

from app.bookmarks.bookmarks import get_all_live_bookmarks_in_json_format
from app.bookmarks.last_used import get_last_used_bookmark
from app.bookmarks.print_tree_recursive import print_tree_recursive
from app.consts.bookmarks_consts import (
    ABS_OBS_BOOKMARKS_DIR,
    IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS,
)
from app.types.bookmark_types import CurrentRunSettings
from app.utils.bookmark_utils import abs_to_rel_path
from app.utils.decorators import only_run_once, print_def_name
from app.utils.printing_utils import print_color

IS_PRINT_VIDEO_FILE_NAMES = True
IS_HOIST_TAGS_WHEN_SINGLE_CHILD = True
# IS_HOIST_TAGS_WHEN_SINGLE_CHILD = False

IS_DEBUG = True
IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def is_ancestor_path(candidate: str, target: str) -> bool:
    """Check if `candidate` is a parent or ancestor of `target` in colon-separated path format."""
    return target == candidate or target.startswith(candidate + ":")


@print_def_name(False)
@only_run_once
def print_all_live_directories_and_bookmarks(
    is_print_just_current_directory_bookmarks: bool = IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS,
    current_run_settings_obj: CurrentRunSettings | None = None,
) -> None:
    """Print all folders and their bookmarks, highlighting the current one"""
    print("")
    print("=" * 50)

    # Get last used bookmark for highlighting if not provided with the current bookmark object.
    if current_run_settings_obj is not None and current_run_settings_obj.get(
        "current_bookmark_obj"
    ):
        current_bookmark_obj = (
            current_run_settings_obj.get("current_bookmark_obj") or {}
        )
    else:
        current_bookmark_obj = get_last_used_bookmark() or {}

    current_bm_tail_name = current_bookmark_obj.get("bookmark_tail_name", None)
    current_bm_dir_slash_abs = current_bookmark_obj.get("bookmark_dir_slash_abs", None)
    current_bm_path_colon_rel = current_bookmark_obj.get(
        "bookmark_path_colon_rel", None
    )

    all_bookmarks: dict[str, Any] = get_all_live_bookmarks_in_json_format(
        _is_override_run_once=True
    )

    # TODO(Kerch): make a file that sits along bookmarks_print.py that is named print_tree_recursive.py and pull that in. Add a new parameter or two depending on what the issues are. make comments to help step the reader through what is going on.

    # Start printing from the root level
    for parent_bm_dir_name, sub_dir_json_without_parent in all_bookmarks.items():
        parent_bm_dir_col_rel = parent_bm_dir_name  # Top-level key, e.g., 'videos-1'

        # Only recurse into matching tree if filtering is active
        if is_print_just_current_directory_bookmarks and current_bm_path_colon_rel:
            if not is_ancestor_path(parent_bm_dir_col_rel, current_bm_path_colon_rel):
                continue
        print(f"DEBUG: parent_bm_dir_name = {parent_bm_dir_name}")
        # ✅ If we're filtering, only recurse into the current bookmark's root tree

        print("")
        print_tree_recursive(
            current_bm_path_colon_rel=current_bm_path_colon_rel,
            is_print_just_current_directory_bookmarks=is_print_just_current_directory_bookmarks,
            indent_level=0,
            parent_bm_dir_name=parent_bm_dir_name,
            # parent_bm_dir_col_rel=parent_bm_dir_name,
            parent_bm_dir_col_rel=parent_bm_dir_col_rel,
            bookmark_dir_json_without_parent=sub_dir_json_without_parent,
            full_colon_path_to_here=parent_bm_dir_col_rel,
        )

    print("")
    print("=" * 50)

    if current_bm_tail_name and current_bm_dir_slash_abs:
        current_bookmark = current_bm_dir_slash_abs + ":" + current_bm_tail_name
        rel_current_bookmark = abs_to_rel_path(current_bookmark, ABS_OBS_BOOKMARKS_DIR)
        rel_current_bookmark = rel_current_bookmark.replace("/", ":")
    else:
        current_bookmark = None
        rel_current_bookmark = None
        rel_current_bookmark = None

    print_color(f"🔍 Current bookmark: bm {rel_current_bookmark}", "magenta")
    return


# @print_def_name(IS_PRINT_DEF_NAME)
# def print_bookmarks_in_directory(
#     folder_path: str,
#     indent: int = 0,
#     last_used_path: str | None = None,
#     inherited_tags: set[str] | None = None,
# ) -> None:
#     if inherited_tags is None:
#         inherited_tags = set()
#     else:
#         inherited_tags = inherited_tags

#     folder_name = os.path.basename(folder_path)
#     print(" " * indent + f"📁 {folder_name}")

#     bookmark_tags_list: list[set[str]] = []
#     child_bookmarks: list[tuple[str, dict[str, Any]]] = []
#     sub_dirs: list[str] = []

#     # Goes through folder contents to separate bookmarks and sub-directories
#     for entry in sorted(os.listdir(folder_path)):
#         entry_path = os.path.join(folder_path, entry)
#         if os.path.isdir(entry_path):
#             sub_dirs.append(entry_path)
#         elif entry == "bookmark_meta.json":
#             with open(entry_path) as f:
#                 meta = json.load(f)
#                 tags = set(meta.get("tags", []))
#                 bookmark_tags_list.append(tags)
#                 child_bookmarks.append((entry_path, meta))

#     bm_sub_dir_tags: set[str] = compute_hoistable_tags(bookmark_tags_list)

#     # Print folder-level tags (only if not already inherited)
#     printable_tags = bm_sub_dir_tags - inherited_tags
#     if printable_tags:
#         tag_str = " ".join([f"•{tag}" for tag in sorted(printable_tags)])
#         print(" " * (indent + 3) + f"🏷️ {tag_str}")

#     # Print each bookmark, omitting inherited or folder-level tags
#     print("========== TEST 1")
#     for entry_path, meta in child_bookmarks:
#         bookmark_dir: str = os.path.dirname(entry_path)
#         bookmark_tail_name: str = os.path.basename(bookmark_dir)
#         tags: set[str] = set(meta.get("tags", []))
#         visible_tags: set[str] = tags - bm_sub_dir_tags - inherited_tags
#         time_str = meta.get("timestamp_formatted", "--:--")
#         tag_str = " ".join([f"•{tag}" for tag in sorted(visible_tags)])
#         display_line = f"{time_str} 📖 {bookmark_tail_name}"
#         if bookmark_dir == last_used_path:
#             display_line += " ← last used"
#         print(" " * (indent + 3) + f"• {display_line}")
#         if tag_str:
#             print(" " * (indent + 6) + f"🏷️ {tag_str}")

#     print("========== TEST 2")

#     # Recurse into sub_dirs
#     for sub_dir in sub_dirs:
#         print_bookmarks_in_directory(
#             sub_dir, indent + 3, last_used_path, inherited_tags | bm_sub_dir_tags
#         )
