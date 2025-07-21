#!/usr/bin/env python3
# type: ignore
# pylint: disable-all
# flake8: noqa
"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from app.bookmarks_consts import IS_DEBUG, IS_DEBUG_FULL

# Load environment variables
load_dotenv()

def get_video_path_from_env():
    """Get the VIDEO_PATH from environment variables."""
    video_path = os.getenv('VIDEO_PATH')
    if not video_path:
        print("⚠️  VIDEO_PATH not found in environment variables")
        return None
    return video_path

def construct_full_video_file_path(video_filename):
    """Construct the full file path from VIDEO_PATH and filename."""
    video_path = get_video_path_from_env()
    if not video_path:
        return None

    # Ensure the video path ends with a separator
    if not video_path.endswith('/') and not video_path.endswith('\\'):
        video_path += '/'

    return os.path.join(video_path, video_filename)


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

def compute_hoistable_tags(list_of_tag_sets):
    if not list_of_tag_sets:
        return set()

    # Filter out any empty sets — if a child has no tags, then no tags should be hoisted
    non_empty_tag_sets = [tags for tags in list_of_tag_sets if tags]

    if len(non_empty_tag_sets) != len(list_of_tag_sets):
        # One or more children had no tags — cannot hoist anything
        return set()

    return set.intersection(*non_empty_tag_sets)



def load_bookmark_meta(bookmark_dir):
    """Load bookmark metadata and construct full file path."""
    meta_file = os.path.join(bookmark_dir, "bookmark_meta.json")
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
                meta_data['full_file_path'] = meta_data['file_path']
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
                    meta_data['full_file_path'] = full_path
                else:
                    print(f"⚠️  Could not construct full path for {video_filename}")
                    meta_data['full_file_path'] = ''
            else:
                if IS_DEBUG:
                    print(f"🔍 Debug - No file_path or video_filename found in metadata")
                meta_data['full_file_path'] = ''

            if IS_DEBUG_FULL:
                print(f"🔍 Debug - Final full_file_path: {meta_data.get('full_file_path', 'NOT_FOUND')}")

            return meta_data
        except json.JSONDecodeError:
            if IS_DEBUG:
                print(f"⚠️  Could not parse bookmark_meta.json in {bookmark_dir}")
            return {}
    return {}


def create_folder_meta(folder_path, folder_name, description="", tags=None):
    """Create or update folder_meta.json file"""
    folder_meta_file = os.path.join(folder_path, "folder_meta.json")

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


LAST_USED_JSON = os.path.join("obs_bookmark_saves", "last_used.json")

def load_last_used_bookmark_path():
    """Load the last used bookmark's folder and name from last_used.json"""
    if not os.path.exists(LAST_USED_JSON):
        if IS_DEBUG:
            print(f"⚠️  last_used.json does not exist at: {LAST_USED_JSON}")
        return None, None

    try:
        with open(LAST_USED_JSON, "r") as f:
            data = json.load(f)
            folder = data.get("folder_name")
            bookmark = data.get("bookmark_name")

            if IS_DEBUG:
                print(f"✅ loaded last_used.json: folder={folder}, bookmark={bookmark}")

            return folder, bookmark
    except Exception as e:
        print(f"❌ Error loading last_used.json: {e}")
        return None, None

