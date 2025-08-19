import json
import os
from datetime import datetime
from typing import Any

from app.bookmarks.auto_tags.auto_tags_utils import safe_process_auto_tags
from app.consts.bookmarks_consts import IS_DEBUG, IS_DEBUG_FULL
from app.obs.videos import construct_full_video_file_path
from app.types.bookmark_types import BookmarkInfo, MatchedBookmarkObj, MediaInfo
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


# This is loaded for all bookmarks to create a tree of bookmarks and tags.
@print_def_name(False)
def load_folder_meta(folder_path: str) -> dict[str, Any]:
    """Load folder metadata from folder_meta.json"""
    folder_meta_file = os.path.join(folder_path, "folder_meta.json")
    if os.path.exists(folder_meta_file):
        try:
            with open(folder_meta_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            if IS_DEBUG:
                print(f"⚠️  Could not parse folder_meta.json in {folder_path}")
            return {}
    return {}


@print_def_name(IS_PRINT_DEF_NAME)
def load_bookmark_meta_from_rel(bookmark_dir_rel: str) -> BookmarkInfo | None:
    """Load bookmark metadata and construct full file path."""
    meta_file = os.path.join(bookmark_dir_rel, "bookmark_meta.json")
    if os.path.exists(meta_file):
        try:
            with open(meta_file, "r") as f:
                meta_data = json.load(f)

            if IS_DEBUG_FULL:
                print(f"🔍 Debug - Loading bookmark metadata from: {meta_file}")
                print(f"🔍 Debug - Raw metadata keys: {list(meta_data.keys())}")

            # Handle both old and new formats
            if "file_path" in meta_data:
                meta_data["video_path"] = meta_data["file_path"]
                if IS_DEBUG_FULL:
                    print(
                        f"🔍 Debug - Using old format file_path: {meta_data['file_path']}"
                    )
            elif "video_filename" in meta_data:
                video_filename = meta_data["video_filename"]
                if IS_DEBUG_FULL:
                    print(
                        f"🔍 Debug - Constructing full path for video_filename: {video_filename}"
                    )
                full_path = construct_full_video_file_path(video_filename)
                if IS_DEBUG_FULL:
                    print(f"🔍 Debug - Constructed full_path: {full_path}")
                if full_path:
                    meta_data["video_path"] = full_path
                else:
                    print(f"⚠️  Could not construct full path for {video_filename}")
                    meta_data["video_path"] = ""
            else:
                if IS_DEBUG:
                    print("🔍 Debug - No file_path or video_filename found in metadata")
                meta_data["video_path"] = ""

            if IS_DEBUG_FULL:
                print(
                    f"🔍 Debug - Final video_path: {meta_data.get('video_path', 'NOT_FOUND')}"
                )

            return meta_data
        except json.JSONDecodeError:
            if IS_DEBUG:
                print(f"⚠️  Could not parse bookmark_meta.json in {bookmark_dir_rel}")
            return None
    return None


# This is loaded for all bookmarks to create a tree of bookmarks and tags.
@print_def_name(False)
def load_bookmark_meta_from_abs(bookmark_path_abs: str) -> dict[str, Any] | None:
    """Load bookmark metadata from bookmark_meta.json"""
    bookmark_meta_path = os.path.join(bookmark_path_abs, "bookmark_meta.json")
    if os.path.exists(bookmark_meta_path):
        with open(bookmark_meta_path, "r") as f:
            return json.load(f)
    return None


# TODO(KERCH): Implement is_patch_updates
@print_def_name(IS_PRINT_DEF_NAME)
def create_directory_meta(
    dir_absolute_path: str,
    description: str = "",
    tags: list[str] | None = None,
    _is_patch_updates: bool = False,  # TODO: Implement or remove
    _is_overwrite: bool = False,  # TODO: Implement or remove
) -> bool:
    """Create or update folder_meta.json file"""

    dir_meta_file_path = os.path.join(dir_absolute_path, "folder_meta.json")

    if tags is None:
        tags = []

    if os.path.exists(dir_meta_file_path):
        # try:
        #     with open(dir_meta_file_path, 'r') as f:
        #         meta_data = json.load(f)
        # except json.JSONDecodeError:
        #     meta_data = {}
        return False

    # Create new
    meta_data = {
        "created_at": datetime.now().isoformat(),
        "description": description,
        "tags": tags,
        "video_filename": "",
    }

    # Update description and tags if provided
    if description:
        meta_data["description"] = description
    if tags:
        meta_data["tags"] = tags

    # Update last_modified
    meta_data["last_modified"] = datetime.now().isoformat()

    try:
        with open(dir_meta_file_path, "w") as f:
            json.dump(meta_data, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error creating folder metadata: {e}")
        return False


@print_def_name(IS_PRINT_DEF_NAME)
def create_bookmark_meta(
    matched_bookmark_obj: MatchedBookmarkObj,
    media_info: MediaInfo | dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> None:
    """Create bookmark metadata with optional tags."""
    bookmark_dir_slash_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    bookmark_tail_name = matched_bookmark_obj["bookmark_tail_name"]

    if media_info is None:
        media_info = {}

    meta_data = {
        "created_at": datetime.now().isoformat(),
        "bookmark_tail_name": bookmark_tail_name,
        "video_filename": media_info.get(
            "video_filename", ""
        ),  # Store just the filename
        "timestamp": media_info.get("timestamp", 0),
        "timestamp_formatted": media_info.get("timestamp_formatted", ""),
        "tags": tags or [],  # Add tags to metadata
    }

    meta_file = os.path.join(bookmark_dir_slash_abs, "bookmark_meta.json")

    with open(meta_file, "w") as f:
        json.dump(meta_data, f, indent=2)

    if IS_DEBUG:
        print(f"📋 Created bookmark metadata with tags: {tags}")

    safe_process_auto_tags(matched_bookmark_obj, current_run_settings_obj=None)


@print_def_name(IS_PRINT_DEF_NAME)
def update_bookmark_meta(
    matched_bookmark_obj: MatchedBookmarkObj,
    media_info: MediaInfo | dict[str, Any],
    tags: list[str] | None = None,
) -> None:
    """Update or create bookmark metadata with optional patching."""
    bookmark_dir_slash_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    bookmark_tail_name = matched_bookmark_obj["bookmark_tail_name"]

    meta_file = os.path.join(bookmark_dir_slash_abs, "bookmark_meta.json")
    meta_data = {}
    if os.path.exists(meta_file):
        with open(meta_file, "r") as f:
            try:
                meta_data = json.load(f)
            except Exception:
                meta_data = {}

    meta_data["updated_at"] = datetime.now().isoformat()
    meta_data["bookmark_tail_name"] = (
        bookmark_tail_name or meta_data["bookmark_tail_name"] or ""
    )
    meta_data["video_filename"] = (
        media_info.get("video_filename", "") or meta_data["video_filename"] or ""
    )
    meta_data["timestamp"] = (
        media_info.get("timestamp", 0) or meta_data["timestamp"] or 0
    )
    meta_data["timestamp_formatted"] = (
        media_info.get("timestamp_formatted", "") or meta_data["timestamp_formatted"]
    )

    if tags is not None:
        meta_data["tags"] = tags

    # If file doesn't exist, set created_at
    if "created_at" not in meta_data:
        meta_data["created_at"] = datetime.now().isoformat()
    with open(meta_file, "w") as f:
        json.dump(meta_data, f, indent=2)

    safe_process_auto_tags(matched_bookmark_obj, current_run_settings_obj=None)


@print_def_name(IS_PRINT_DEF_NAME)
def patch_bookmark_meta(
    matched_bookmark_obj: MatchedBookmarkObj,
    media_info: MediaInfo | dict[str, Any],
    tags: list[str] | None = None,
) -> None:
    """Update or create bookmark metadata with optional patching."""
    bookmark_dir_slash_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    bookmark_tail_name = matched_bookmark_obj["bookmark_tail_name"]

    meta_file = os.path.join(bookmark_dir_slash_abs, "bookmark_meta.json")
    meta_data = {}
    if os.path.exists(meta_file):
        with open(meta_file, "r") as f:
            try:
                meta_data = json.load(f)
            except Exception:
                meta_data = {}

    meta_data["updated_at"] = datetime.now().isoformat()
    meta_data["bookmark_tail_name"] = (
        meta_data["bookmark_tail_name"] or bookmark_tail_name or ""
    )
    meta_data["video_filename"] = (
        media_info.get("video_filename", "") or meta_data["video_filename"] or ""
    )
    meta_data["timestamp"] = (
        meta_data["timestamp"] or media_info.get("timestamp", 0) or 0
    )
    meta_data["timestamp_formatted"] = meta_data[
        "timestamp_formatted"
    ] or media_info.get("timestamp_formatted", "")

    if tags is not None:
        meta_data["tags"].extend(tags)

    # If file doesn't exist, set created_at
    if "created_at" not in meta_data:
        meta_data["created_at"] = datetime.now().isoformat()
    with open(meta_file, "w") as f:
        json.dump(meta_data, f, indent=2)
    if IS_DEBUG:
        print(f"📋 Patched bookmark metadata with tags: {tags}")

    safe_process_auto_tags(matched_bookmark_obj, current_run_settings_obj=None)


@print_def_name(IS_PRINT_DEF_NAME)
def update_missing_bookmark_meta_fields(
    matched_bookmark_obj: MatchedBookmarkObj,
    media_info: MediaInfo | dict[str, Any],
    tags: list[str] | None = None,
) -> None:
    """Update or create bookmark metadata with optional patching."""
    bookmark_dir_slash_abs = matched_bookmark_obj["bookmark_path_slash_abs"]
    bookmark_tail_name = matched_bookmark_obj["bookmark_tail_name"]

    meta_file = os.path.join(bookmark_dir_slash_abs, "bookmark_meta.json")
    meta_data = {}
    if os.path.exists(meta_file):
        with open(meta_file, "r") as f:
            try:
                meta_data = json.load(f)
            except Exception:
                meta_data = {}

    meta_data["updated_at"] = datetime.now().isoformat()
    meta_data["bookmark_tail_name"] = (
        meta_data["bookmark_tail_name"] or bookmark_tail_name or ""
    )
    meta_data["video_filename"] = (
        meta_data["video_filename"] or media_info.get("video_filename", "") or ""
    )
    meta_data["timestamp"] = (
        meta_data["timestamp"] or media_info.get("timestamp", 0) or 0
    )
    meta_data["timestamp_formatted"] = meta_data[
        "timestamp_formatted"
    ] or media_info.get("timestamp_formatted", "")

    if tags is not None:
        meta_data["tags"].extend(tags)

    # If file doesn't exist, set created_at
    if "created_at" not in meta_data:
        meta_data["created_at"] = datetime.now().isoformat()
    with open(meta_file, "w") as f:
        json.dump(meta_data, f, indent=2)
    if IS_DEBUG:
        print(f"📋 Patched bookmark metadata with tags: {tags}")

    safe_process_auto_tags(matched_bookmark_obj, current_run_settings_obj=None)
