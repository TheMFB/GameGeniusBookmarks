import json
import os
import shutil

from app.bookmarks.bookmark_dir_processes import get_all_valid_root_dir_names
from app.bookmarks.bookmarks_meta import (
    load_bookmark_meta_from_abs,
    load_bookmark_meta_from_rel,
    load_folder_meta,
)
from app.consts.bookmarks_consts import (
    IS_DEBUG,
    IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON,
    REPO_ROOT,
)
from app.types.bookmark_types import (
    BookmarkInfo,
    BookmarkPathDictionary,
    MatchedBookmarkObj,
)
from app.utils.decorators import memoize, print_def_name
from app.utils.printing_utils import pprint, print_color

IS_AGGREGATE_TAGS_AND_HOIST_GROUPED = True
IS_PRINT_DEF_NAME = True

# Global
has_printed_all_bookmarks_json = False  # pylint: disable=C0103


@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def get_all_deep_bookmarks_in_dir_with_meta(
    bookmark_dir_abs: str,
) -> dict[str, BookmarkInfo]:
    """
    Recursively search bookmark_dir_abs for directories containing bookmark_meta.json.
    Returns a dict mapping from a human-readable key to BookmarkInfo.
    """
    matched_bookmarks = {}

    if not os.path.exists(bookmark_dir_abs):
        return matched_bookmarks

    parent_dir_name = os.path.basename(bookmark_dir_abs)

    def scan_for_bookmarks(current_abs_path: str, current_rel_path: str = ""):
        for entry in os.listdir(current_abs_path):
            full_entry_path = os.path.join(current_abs_path, entry)
            if os.path.isdir(full_entry_path):
                meta_file = os.path.join(full_entry_path, "bookmark_meta.json")
                if os.path.exists(meta_file):
                    # This is a bookmark directory
                    bookmark_key = (
                        f"{parent_dir_name}/{current_rel_path}/{entry}"
                        if current_rel_path
                        else f"{parent_dir_name}/{entry}"
                    )
                    bookmark_meta = load_bookmark_meta_from_rel(full_entry_path)
                    if bookmark_meta:
                        matched_bookmarks[bookmark_key] = bookmark_meta
                    elif IS_DEBUG:
                        print(
                            f"⚠️  Could not load bookmark metadata from {full_entry_path}"
                        )
                else:
                    # Recurse deeper
                    new_rel_path = (
                        f"{current_rel_path}/{entry}" if current_rel_path else entry
                    )
                    scan_for_bookmarks(full_entry_path, new_rel_path)

    scan_for_bookmarks(bookmark_dir_abs)
    return matched_bookmarks


@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def get_all_shallow_bookmark_abs_paths_in_dir(
    parent_bookmark_dir_abs: str,
) -> list[str]:
    """
    Returns a list of immediate absolute bookmark paths inside `parent_bookmark_dir_abs` that contain a 'bookmark_meta.json' file.
    """
    if not os.path.exists(parent_bookmark_dir_abs):
        print(f"⚠️  Could not find {parent_bookmark_dir_abs}")
        return []

    result = []

    try:
        for entry in os.listdir(parent_bookmark_dir_abs):
            entry_path = os.path.join(parent_bookmark_dir_abs, entry)
            if os.path.isdir(entry_path):
                meta_path = os.path.join(entry_path, "bookmark_meta.json")
                if os.path.exists(meta_path):
                    result.append(entry_path)
    except Exception as e:
        if IS_DEBUG:
            print(f"⚠️ Failed to read {parent_bookmark_dir_abs}: {e}")

    return result


@print_def_name(False)
@memoize
def get_all_live_bookmarks_in_json_format(_is_override_run_once: bool = False):
    """
    Recursively scan all live folders and build a nested JSON structure with folder and bookmark tags/descriptions, including aggregated tags as 'tags'.
    """
    # TODO(MFB): Look into this, as this is likely a (relatively) VERY heavy operation.

    def scan_folder(folder_path):
        node = {}
        # Add folder meta if present
        folder_meta = load_folder_meta(folder_path)
        folder_tags = set()
        if folder_meta:
            folder_tags = set(folder_meta.get("tags", []))
            node["description"] = folder_meta.get("description", "")
            node["video_filename"] = folder_meta.get("video_filename", "")

        # List all items in this folder
        try:
            items = os.listdir(folder_path)
        except Exception:
            return node

        sub_dirs = {}

        for item in items:
            file_abs_path = os.path.join(folder_path, item)
            if os.path.isdir(file_abs_path):
                # Recurse into subfolder
                sub_dirs[item] = scan_folder(file_abs_path)
            elif item == "bookmark_meta.json":
                # This folder is a bookmark (leaf)
                bookmark_meta = load_bookmark_meta_from_abs(folder_path)
                if bookmark_meta:
                    node.update(
                        {
                            "tags": bookmark_meta.get("tags", []),
                            "description": bookmark_meta.get("description", ""),
                            "timestamp": bookmark_meta.get("timestamp_formatted", ""),
                            "video_filename": bookmark_meta.get("video_filename", ""),
                            "type": "bookmark",
                        }
                    )
                return node  # Do not process further, this is a bookmark

        # Attach sub_dirs to node
        for sub_dir_name, sub_dir_node in sub_dirs.items():
            node[sub_dir_name] = sub_dir_node

        if IS_AGGREGATE_TAGS_AND_HOIST_GROUPED:
            # --- Tag aggregation logic ---
            # Gather tags from all children (sub_dirs and bookmarks)
            child_tag_sets = []
            for sub_dir_node in sub_dirs.values():
                child_tags = set(sub_dir_node.get("tags", []))
                if child_tags:
                    child_tag_sets.append(child_tags)

            # Only hoist if there are children
            if child_tag_sets:
                grouped_tags = (
                    set.intersection(*child_tag_sets) if child_tag_sets else set()
                )
            else:
                grouped_tags = set()

            # Remove grouped_tags from all children
            for sub_dir_node in sub_dirs.values():
                if "tags" in sub_dir_node:
                    sub_dir_node["tags"] = list(
                        set(sub_dir_node["tags"]) - grouped_tags
                    )

            # Combine folder's own tags and grouped tags, and unique-ify
            all_tags = folder_tags.union(grouped_tags)
            if all_tags:
                node["tags"] = list(sorted(all_tags))
            elif "tags" in node:
                # Remove empty tags list if present
                del node["tags"]

        return node

    all_bookmarks = {}
    for folder_path in get_all_valid_root_dir_names():
        folder_name = os.path.basename(folder_path)
        all_bookmarks[folder_name] = scan_folder(folder_path)

    if IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON:
        global has_printed_all_bookmarks_json
        if not has_printed_all_bookmarks_json:
            print("")
            print("")
            print_color("++++ all_bookmarks json:", "cyan")
            pprint(all_bookmarks)
            print("")
            print("")
            has_printed_all_bookmarks_json = True

    return all_bookmarks


@print_def_name(IS_PRINT_DEF_NAME)
def get_bookmark_info(
    cli_bookmark_obj: BookmarkPathDictionary,
) -> MatchedBookmarkObj | None:
    """
    Get the information file from the bookmark
    """

    bookmark_path_slash_abs = cli_bookmark_obj["bookmark_path_slash_abs"]
    meta_file = os.path.join(bookmark_path_slash_abs, "bookmark_meta.json")

    if not os.path.exists(meta_file):
        print(f"⚠️ Bookmark metadata file not found: {meta_file}")
        return None

    try:
        with open(meta_file, "r") as f:
            meta_data = json.load(f)
            return {
                **cli_bookmark_obj,
                "bookmark_info": meta_data,
            }
    except Exception as e:
        print(f"❌ Error loading bookmark metadata: {e}")
        return None


@print_def_name(IS_PRINT_DEF_NAME)
def create_bookmark_symlinks(matched_bookmark_obj):
    """Create symlinks for the last used bookmark and its folder."""

    # Get the root directory of the bookmark manager
    shortcuts_dir = os.path.join(REPO_ROOT, "shortcuts")
    os.makedirs(shortcuts_dir, exist_ok=True)

    # Create last_used_bookmark directory if it doesn't exist
    last_used_bookmark_dir = os.path.join(shortcuts_dir, "last_used_bookmark")
    os.makedirs(last_used_bookmark_dir, exist_ok=True)

    # Create last_used_bookmark_folder directory if it doesn't exist
    last_used_bookmark_folder_dir = os.path.join(
        shortcuts_dir, "last_used_bookmark_folder"
    )
    os.makedirs(last_used_bookmark_folder_dir, exist_ok=True)

    def clear_directory(directory_path):
        for item in os.listdir(directory_path):
            file_abs_path = os.path.join(directory_path, item)
            try:
                if os.path.islink(file_abs_path):
                    os.unlink(file_abs_path)
                elif os.path.isfile(file_abs_path):
                    os.remove(file_abs_path)
                elif os.path.isdir(file_abs_path):
                    shutil.rmtree(file_abs_path)
            except Exception as e:
                print(f"⚠️  Warning: Could not remove {file_abs_path}: {e}")

    clear_directory(last_used_bookmark_dir)
    clear_directory(last_used_bookmark_folder_dir)

    # Construct the target paths
    bookmark_dir = matched_bookmark_obj["bookmark_dir_slash_abs"]
    bookmark_path = matched_bookmark_obj["bookmark_path_slash_abs"]
    bookmark_tail_name = matched_bookmark_obj["bookmark_tail_name"]
    bookmark_parent_name = os.path.basename(os.path.dirname(bookmark_path))

    # Define symlink paths
    bookmark_symlink_path = os.path.join(last_used_bookmark_dir, bookmark_tail_name)
    folder_symlink_path = os.path.join(
        last_used_bookmark_folder_dir, bookmark_parent_name
    )

    try:
        # Create symlink for the specific bookmark (named after the bookmark)
        if os.path.exists(bookmark_symlink_path):
            if os.path.islink(bookmark_symlink_path):
                os.unlink(bookmark_symlink_path)
            else:
                os.remove(bookmark_symlink_path)
        os.symlink(bookmark_path, bookmark_symlink_path)

        # Create symlink for the bookmark's folder (named after the folder)
        if os.path.exists(folder_symlink_path):
            if os.path.islink(folder_symlink_path):
                os.unlink(folder_symlink_path)
            else:
                os.remove(folder_symlink_path)
        os.symlink(bookmark_dir, folder_symlink_path)

    except Exception as e:
        print(f"⚠️  Could not create symlinks: {e}")


@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def get_all_live_bookmark_path_slash_rels():
    """
    Return a flat list of all bookmark paths from all live folders.
    """
    bookmark_paths = []

    for folder in get_all_valid_root_dir_names():
        all_bookmark_objects = get_all_deep_bookmarks_in_dir_with_meta(folder)
        bookmark_paths.extend(all_bookmark_objects.keys())

    return bookmark_paths
