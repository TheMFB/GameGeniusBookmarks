"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
from pprint import pprint
import os
import json
from datetime import datetime

from app.bookmarks_consts import IS_DEBUG, IS_DEBUG_FULL
from app.videos import construct_full_video_file_path
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(False) # This is loaded for all bookmarks to create a tree of bookmarks and tags.
def load_folder_meta(folder_path):
    """Load folder metadata from folder_meta.json"""
    folder_meta_file = os.path.join(folder_path, "folder_meta.json")
    if os.path.exists(folder_meta_file):
        try:
            with open(folder_meta_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            if IS_DEBUG:
                print(
                    f"⚠️  Could not parse folder_meta.json in {folder_path}")
            return {}
    return {}

# TODO(MFB): Do we have enough to make a tags folder?
@print_def_name(IS_PRINT_DEF_NAME)
def compute_hoistable_tags(list_of_tag_sets):
    """Given a list of tag sets (one per bookmark), return the set of tags shared by all -- in order to bring them up to the next parent folder"""
    if not list_of_tag_sets:
        return set()
    return set.intersection(*list_of_tag_sets)


@print_def_name(IS_PRINT_DEF_NAME)
def load_bookmark_meta_from_rel(bookmark_dir_rel):
    """Load bookmark metadata and construct full file path."""
    meta_file = os.path.join(bookmark_dir_rel, "bookmark_meta.json")
    if os.path.exists(meta_file):
        try:
            with open(meta_file, 'r') as f:
                meta_data = json.load(f)

            if IS_DEBUG_FULL:
                print(f"🔍 Debug - Loading bookmark metadata from: {meta_file}")
                print(f"🔍 Debug - Raw metadata keys: {list(meta_data.keys())}")

            # Handle both old and new formats
            if 'file_path' in meta_data:
                # Old format - file_path already contains full path
                meta_data['video_path'] = meta_data['file_path']
                if IS_DEBUG_FULL:
                    print(f"🔍 Debug - Using old format file_path: {meta_data['file_path']}")
            elif 'video_filename' in meta_data:
                # New format - construct full path from VIDEO_PATH and filename
                video_filename = meta_data['video_filename']
                if IS_DEBUG_FULL:
                    print(f"🔍 Debug - Constructing full path for video_filename: {video_filename}")
                full_path = construct_full_video_file_path(video_filename)
                if IS_DEBUG_FULL:
                    print(f"🔍 Debug - Constructed full_path: {full_path}")
                if full_path:
                    meta_data['video_path'] = full_path
                else:
                    print(f"⚠️  Could not construct full path for {video_filename}")
                    meta_data['video_path'] = ''
            else:
                if IS_DEBUG:
                    print(f"🔍 Debug - No file_path or video_filename found in metadata")
                meta_data['video_path'] = ''

            if IS_DEBUG_FULL:
                print(f"🔍 Debug - Final video_path: {meta_data.get('video_path', 'NOT_FOUND')}")

            return meta_data
        except json.JSONDecodeError:
            if IS_DEBUG:
                print(f"⚠️  Could not parse bookmark_meta.json in {bookmark_dir_rel}")
            return {}
    return {}

@print_def_name(False) # This is loaded for all bookmarks to create a tree of bookmarks and tags.
def load_bookmark_meta_from_abs(bookmark_path_abs):
    """Load bookmark metadata from bookmark_meta.json"""
    bookmark_meta_path = os.path.join(bookmark_path_abs, "bookmark_meta.json")
    if os.path.exists(bookmark_meta_path):
        with open(bookmark_meta_path, 'r') as f:
            return json.load(f)
    return None

@print_def_name(IS_PRINT_DEF_NAME)
def create_folder_meta(abs_folder_dir, description="", tags=None):
    """Create or update folder_meta.json file"""
    folder_meta_file = os.path.join(abs_folder_dir, "folder_meta.json")

    if tags is None:
        tags = []

    # Load existing or create new
    if os.path.exists(folder_meta_file):
        try:
            with open(folder_meta_file, 'r') as f:
                meta_data = json.load(f)
        except json.JSONDecodeError:
            meta_data = {}
    else:
        meta_data = {
            "created_at": datetime.now().isoformat(),
            "description": description,
            "tags": tags
        }

    # Update description and tags if provided
    if description:
        meta_data["description"] = description
    if tags:
        meta_data["tags"] = tags

    # Update last_modified
    meta_data["last_modified"] = datetime.now().isoformat()

    try:
        with open(folder_meta_file, 'w') as f:
            json.dump(meta_data, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error creating folder metadata: {e}")
        return False


@print_def_name(IS_PRINT_DEF_NAME)
def create_bookmark_meta(bookmark_dir, bookmark_name, media_info, tags=None):
    """Create bookmark metadata with optional tags."""
    meta_data = {
        "created_at": datetime.now().isoformat(),
        "bookmark_name": bookmark_name,
        "video_filename": media_info.get('video_filename', ''),  # Store just the filename
        "timestamp": media_info.get('timestamp', 0),
        "timestamp_formatted": media_info.get('timestamp_formatted', ''),
        "tags": tags or []  # Add tags to metadata
    }

    meta_file = os.path.join(bookmark_dir, "bookmark_meta.json")
    with open(meta_file, 'w') as f:
        json.dump(meta_data, f, indent=2)

    if IS_DEBUG:
        print(f"📋 Created bookmark metadata with tags: {tags}")
