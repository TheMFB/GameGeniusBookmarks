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

from app.bookmarks_consts import IS_DEBUG


def load_session_meta(session_dir):
    """Load session metadata from session_meta.json"""
    session_meta_file = os.path.join(session_dir, "session_meta.json")
    if os.path.exists(session_meta_file):
        try:
            with open(session_meta_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            if IS_DEBUG:
                print(f"⚠️  Could not parse session_meta.json")
            return {}
    return {}


def load_folder_meta(folder_path):
    """Load folder metadata from session_meta.json"""
    folder_meta_file = os.path.join(folder_path, "session_meta.json")
    if os.path.exists(folder_meta_file):
        try:
            with open(folder_meta_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            if IS_DEBUG:
                print(
                    f"⚠️  Could not parse session_meta.json in {folder_path}")
            return {}
    return {}


def create_session_meta(session_dir, session_name):
    """Create or update session_meta.json file"""
    session_meta_file = os.path.join(session_dir, "session_meta.json")

    # Load existing or create new
    if os.path.exists(session_meta_file):
        try:
            with open(session_meta_file, 'r') as f:
                meta_data = json.load(f)
        except json.JSONDecodeError:
            meta_data = {}
    else:
        meta_data = {
            "created_at": datetime.now().isoformat(),
            "description": "",
            "tags": []
        }

    # Update last_modified
    meta_data["last_modified"] = datetime.now().isoformat()

    try:
        with open(session_meta_file, 'w') as f:
            json.dump(meta_data, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error creating session metadata: {e}")
        return False


def create_folder_meta(folder_path, folder_name, description="", tags=None):
    """Create or update session_meta.json file"""
    folder_meta_file = os.path.join(folder_path, "session_meta.json")

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
        "file_path": media_info.get('file_path', ''),
        "timestamp": media_info.get('timestamp', 0),
        "timestamp_formatted": media_info.get('timestamp_formatted', ''),
        "tags": tags or []  # Add tags to metadata
    }

    meta_file = os.path.join(bookmark_dir, "bookmark_meta.json")
    with open(meta_file, 'w') as f:
        json.dump(meta_data, f, indent=2)

    if IS_DEBUG:
        print(f"📋 Created bookmark metadata with tags: {tags}")
