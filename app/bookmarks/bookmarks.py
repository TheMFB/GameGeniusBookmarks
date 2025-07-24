"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
import re
from pprint import pprint
import json

from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.utils import print_color, print_def_name
from app.bookmarks.finders import find_matching_bookmarks, load_bookmarks_from_folder
from app.types import MatchedBookmarkObj, BookmarkPathDictionary

IS_AGGREGATE_TAGS = False
IS_PRINT_DEF_NAME = True


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


def token_match_bookmarks(query_string, folder_dir):
    """
    Returns a list of bookmark paths where all query tokens appear in the path.
    """
    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return []

    query_tokens = set(query_string.lower().replace(
        ":", " ").replace("/", " ").split())
    matches = []

    for path in all_bookmark_objects.keys():
        path_tokens = set(re.split(r"[-_/]", path.lower()))
        if query_tokens.issubset(path_tokens):
            matches.append(path)

    return matches


# def get_all_bookmark_paths(valid_root_dir_names):
#     """
#     Return a flat list of all bookmark paths from all live folders.
#     """
#     bookmark_paths = []

#     for folder in valid_root_dir_names:
#         all_bookmark_objects = load_bookmarks_from_folder(folder)
#         bookmark_paths.extend(all_bookmark_objects.keys())

#     return bookmark_paths


# def build_bookmark_token_map(include_tags_and_descriptions=True):
#     """
#     Return a dict mapping each bookmark path to a token set for matching.
#     """
#     from app.bookmark_dir_processes import get_all_valid_root_dir_names
#     from app.bookmarks_meta import load_bookmark_meta_from_rel, load_folder_meta

#     bookmark_token_map = {}
#     valid_root_dir_names = get_all_valid_root_dir_names()

#     for folder_path in valid_root_dir_names:
#         folder_name = os.path.basename(folder_path)

#         # Load folder-level metadata
#         folder_meta = load_folder_meta(folder_path)
#         folder_tags = folder_meta.get("tags", []) if include_tags_and_descriptions else []
#         folder_description = folder_meta.get("description", "") if include_tags_and_descriptions else ""

#         # Load bookmarks
#         all_bookmark_objects = load_bookmarks_from_folder(folder_path)

#         for bookmark_path, bookmark_data in all_bookmark_objects.items():
#             full_key = f"{folder_name}:{bookmark_path}".replace("/", ":")  # normalized key

#             tokens = set()

#             # Split bookmark path into parts
#             parts = bookmark_path.split('/')
#             for part in parts:
#                 tokens.update(part.lower().split('-'))  # split kebab-case parts

#             tokens.add(folder_name.lower())

#             if include_tags_and_descriptions:
#                 # Add bookmark-level meta
#                 full_path = os.path.join(folder_path, bookmark_path)
#                 # TODO(MFB): I'm not sure this is rel...
#                 meta = load_bookmark_meta_from_rel(full_path)

#                 tokens.update([tag.lower() for tag in meta.get("tags", [])])

#                 if desc := meta.get("description"):
#                     if folder_description:
#                         tokens.update(folder_description.lower().split())


#                 # Also add folder-level tags/descriptions
#                 tokens.update([tag.lower() for tag in folder_tags])
#                 if folder_description:
#                     tokens.update(folder_description.lower().split())


#             bookmark_token_map[full_key] = {
#                 "tokens": tokens,
#                 "bookmark_name": os.path.basename(bookmark_path),
#                 "folder_name": folder_name,
#             }

#     return bookmark_token_map


# def fuzzy_match_bookmark_tokens(query: str, include_tags_and_descriptions: bool = True, top_n: int = 5):
#     token_map = build_bookmark_token_map(include_tags_and_descriptions)
#     query_tokens = set(query.lower().split())

#     scored_matches = []

#     for key, data in token_map.items():
#         overlap = data["tokens"].intersection(query_tokens)
#         score = len(overlap)
#         query_lower = query.lower()

#     # Boost if bookmark name starts with query
#     if data["bookmark_name"].lower().startswith(query_lower):
#         score += 10  # strong boost

#     # Boost if folder name starts with query
#     if data["folder_name"].lower().startswith(query_lower):
#         score += 5  # moderate boost

#     if score > 0:
#         print(f"{key} -> match score: {score}, overlap: {overlap}")
#         scored_matches.append((score, key))

#     # Sort by score descending, then alphabetically by key
#     scored_matches.sort(key=lambda x: (-x[0], x[1]))

#     top_matches = [match[1] for match in scored_matches[:top_n]]
#     return top_matches

# def interlive_fuzzy_lookup(query: str, top_n: int = 5):
#     """
#     Perform fuzzy matching and ask user to choose a bookmark from the top N matches.
#     Returns the selected bookmark path, or None if cancelled.
#     """
#     matches = fuzzy_match_bookmark_tokens(query, top_n=top_n)

#     if not matches:
#         print("❌ No matches found.")
#         return None

#     print(f"🤔 Fuzzy matches for '{query}':")
#     for idx, match in enumerate(matches, 1):
#         print(f"  {idx}. {match}")
#     print("  0. Cancel")

#     while True:
#         try:
#             choice = input(f"Enter your choice (1-{len(matches)} or 0 to cancel): ").strip()
#             if choice == "0":
#                 print("❌ Cancelled.")
#                 return None
#             choice_num = int(choice)
#             if 1 <= choice_num <= len(matches):
#                 selected = matches[choice_num - 1]
#                 print(f"✅ Selected: {selected}")
#                 return selected
#             else:
#                 print(f"❌ Invalid input. Choose between 0 and {len(matches)}.")
#         except ValueError:
#             print("❌ Please enter a number.")

