"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
from pprint import pprint
import json

from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.bookmarks_consts import IS_DEBUG, IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON
from app.bookmarks_meta import load_bookmark_meta_from_rel, load_bookmark_meta_from_abs, load_folder_meta
from app.types import MatchedBookmarkObj, BookmarkPathDictionary
from app.utils.printing_utils import print_color
from app.utils.decorators import print_def_name, memoize

IS_AGGREGATE_TAGS = False
IS_PRINT_DEF_NAME = True

# Global
has_printed_all_bookmarks_json = False


@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def load_bookmarks_from_folder(folder_dir_abs):
    matched_bookmarks = {}
    print_color('Loading bookmarks from folder: ' + folder_dir_abs, 'cyan')

    if not os.path.exists(folder_dir_abs):
        return matched_bookmarks

    root_name = os.path.basename(folder_dir_abs)

    def scan_for_bookmarks(dir, current_path=""):
        """Recursively scan dir for bookmark_meta.json files"""
        for item in os.listdir(dir):
            item_path = os.path.join(dir, item)
            if os.path.isdir(item_path):
                # Check if this dir contains a bookmark_meta.json
                meta_file = os.path.join(item_path, "bookmark_meta.json")
                if os.path.exists(meta_file):
                    # This is a bookmark dir
                    # Use forward slashes for consistency across platforms
                    if current_path:
                        bookmark_key = f"{root_name}/{current_path}/{item}"
                    else:
                        bookmark_key = f"{root_name}/{item}"

                    # Use the new load_bookmark_meta function
                    bookmark_meta = load_bookmark_meta_from_rel(item_path)
                    if bookmark_meta:
                        matched_bookmarks[bookmark_key] = bookmark_meta
                    else:
                        if IS_DEBUG:
                            print(
                                f"⚠️  Could not load bookmark metadata from {item_path}")
                else:
                    # This is a regular dir, scan recursively
                    # Use forward slashes for consistency across platforms
                    if current_path:
                        new_path = f"{current_path}/{item}"
                    else:
                        new_path = item
                    scan_for_bookmarks(item_path, new_path)

    scan_for_bookmarks(folder_dir_abs)
    return matched_bookmarks


@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def get_all_valid_bookmarks_in_json_format():
    """Recursively scan all live folders and build a nested JSON structure with folder and bookmark tags/descriptions, including aggregated tags as 'tags'."""
    # TODO(MFB): Look into this, as this is likely a (relatively) VERY heavy operation.

    def scan_folder(folder_path):
        node = {}
        # Add folder meta if present
        folder_meta = load_folder_meta(folder_path)
        folder_tags = set()
        if folder_meta:
            folder_tags = set(folder_meta.get('tags', []))
            node['description'] = folder_meta.get('description', '')
            node['video_filename'] = folder_meta.get('video_filename', '')

        # List all items in this folder
        try:
            items = os.listdir(folder_path)
        except Exception:
            return node

        sub_dirs = {}

        for item in items:
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                # Recurse into subfolder
                sub_dirs[item] = scan_folder(item_path)
            elif item == "bookmark_meta.json":
                # This folder is a bookmark (leaf)
                bookmark_meta = load_bookmark_meta_from_abs(folder_path)
                node.update({
                    'tags': bookmark_meta.get('tags', []),
                    'description': bookmark_meta.get('description', ''),
                    'timestamp': bookmark_meta.get('timestamp_formatted', ''),
                    'video_filename': bookmark_meta.get('video_filename', ''),
                    'type': 'bookmark'
                })
                return node  # Do not process further, this is a bookmark

        # Attach sub_dirs to node
        for sub_dir_name, sub_dir_node in sub_dirs.items():
            node[sub_dir_name] = sub_dir_node

        if IS_AGGREGATE_TAGS:
            # --- Tag aggregation logic ---
            # Gather tags from all children (sub_dirs and bookmarks)
            child_tag_sets = []
            for sub_dir_node in sub_dirs.values():
                child_tags = set(sub_dir_node.get('tags', []))
                if child_tags:
                    child_tag_sets.append(child_tags)

            # Only hoist if there are children
            if child_tag_sets:
                grouped_tags = set.intersection(
                    *child_tag_sets) if child_tag_sets else set()
            else:
                grouped_tags = set()

            # Remove grouped_tags from all children
            for sub_dir_node in sub_dirs.values():
                if 'tags' in sub_dir_node:
                    sub_dir_node['tags'] = list(
                        set(sub_dir_node['tags']) - grouped_tags)

            # Combine folder's own tags and grouped tags, and uniquify
            all_tags = folder_tags.union(grouped_tags)
            if all_tags:
                node['tags'] = list(sorted(all_tags))
            elif 'tags' in node:
                # Remove empty tags list if present
                del node['tags']

        return node

    all_bookmarks = {}
    for folder_path in get_all_valid_root_dir_names():
        folder_name = os.path.basename(folder_path)
        all_bookmarks[folder_name] = scan_folder(folder_path)

    if IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON:
        global has_printed_all_bookmarks_json
        if not has_printed_all_bookmarks_json:
            print('')
            print('')
            print_color('++++ all_bookmarks json:', 'cyan')
            pprint(all_bookmarks)
            print('')
            print('')
            has_printed_all_bookmarks_json = True

    return all_bookmarks




@print_def_name(IS_PRINT_DEF_NAME)
def get_bookmark_info(cli_bookmark_obj: BookmarkPathDictionary) -> MatchedBookmarkObj | None:
    """
    Get the information file from the bookmark 
    """
    print_color('---- valid_root_dir_names ----', 'magenta')

    bookmark_path_slash_abs = cli_bookmark_obj["bookmark_path_slash_abs"]
    meta_file = os.path.join(bookmark_path_slash_abs, "bookmark_meta.json")

    if not os.path.exists(meta_file):
        print(f"❌ Bookmark metadata file not found: {meta_file}")
        return None

    try:
        with open(meta_file, 'r') as f:
            meta_data = json.load(f)
            return {
                **cli_bookmark_obj,
                "bookmark_info": meta_data,
            }
    except Exception as e:
        print(f"❌ Error loading bookmark metadata: {e}")
        return cli_bookmark_obj


@print_def_name(IS_PRINT_DEF_NAME)
def create_bookmark_symlinks(matched_bookmark_obj):
    """Create symlinks for the last used bookmark and its folder."""
    import os
    import shutil


    # Get the root directory of the bookmark manager
    root_dir = os.path.dirname(os.path.dirname(__file__))
    shortcuts_dir = os.path.join(root_dir, "shortcuts")

    # Create shortcuts directory if it doesn't exist
    if not os.path.exists(shortcuts_dir):
        os.makedirs(shortcuts_dir)

    # Create last_used_bookmark directory if it doesn't exist
    last_used_bookmark_dir = os.path.join(shortcuts_dir, "last_used_bookmark")
    if not os.path.exists(last_used_bookmark_dir):
        os.makedirs(last_used_bookmark_dir)

    # Create last_used_bookmark_folder directory if it doesn't exist
    last_used_bookmark_folder_dir = os.path.join(shortcuts_dir, "last_used_bookmark_folder")
    if not os.path.exists(last_used_bookmark_folder_dir):
        os.makedirs(last_used_bookmark_folder_dir)

    # Clear the last_used_bookmark directory - remove everything first
    if os.path.exists(last_used_bookmark_dir):
        for item in os.listdir(last_used_bookmark_dir):
            item_path = os.path.join(last_used_bookmark_dir, item)
            try:
                if os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"⚠️  Warning: Could not remove {item_path}: {e}")

    # Clear the last_used_bookmark_folder directory - remove everything first
    if os.path.exists(last_used_bookmark_folder_dir):
        for item in os.listdir(last_used_bookmark_folder_dir):
            item_path = os.path.join(last_used_bookmark_folder_dir, item)
            try:
                if os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"⚠️  Warning: Could not remove {item_path}: {e}")

    # Construct the target paths
    bookmark_dir = matched_bookmark_obj["bookmark_dir_slash_abs"]
    bookmark_path = matched_bookmark_obj["bookmark_path_slash_abs"]
    bookmark_tail_name = matched_bookmark_obj["bookmark_tail_name"]
    bookmark_parent_name = os.path.basename(os.path.dirname(bookmark_path))



    # Get the bookmark name and folder name (last parts of the paths)

    # Define symlink paths
    bookmark_symlink_path = os.path.join(
        last_used_bookmark_dir, bookmark_tail_name)
    folder_symlink_path = os.path.join(
        last_used_bookmark_folder_dir, bookmark_parent_name)

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


# TODO(MFB): Bugfix
@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def get_all_live_bookmark_path_slash_rels():
    """
    Return a flat list of all bookmark paths from all live folders.
    """
    bookmark_paths = []

    for folder in get_all_valid_root_dir_names():
        all_bookmark_objects = load_bookmarks_from_folder(folder)
        bookmark_paths.extend(all_bookmark_objects.keys())

    return bookmark_paths


