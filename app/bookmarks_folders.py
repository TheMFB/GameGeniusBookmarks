# type: ignore
"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
from redis_friendly_converter import convert_file as convert_redis_to_friendly
import os
import sys
import subprocess
import time
import json
from datetime import datetime

from app.bookmarks_consts import IS_DEBUG, BOOKMARKS_DIR
from app.bookmarks_meta import load_folder_meta, create_folder_meta

def get_all_active_folders():
    """Recursively collect all folder paths under BOOKMARKS_DIR (excluding archive)"""
    try:
        if IS_DEBUG:
            print(f"🔍 Scanning for folders inside: {BOOKMARKS_DIR}")

        if not os.path.exists(BOOKMARKS_DIR):
            print(f"❌ Bookmarks directory does not exist: {BOOKMARKS_DIR}")
            return []

        excluded_dirs = {"archive"}
        active_folders = []

        for root, dirs, files in os.walk(BOOKMARKS_DIR):
            # Skip excluded dirs
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            # ✅ Include this folder if it contains a bookmark_meta.json
            if "bookmark_meta.json" in files:
                active_folders.append(root)

        return active_folders

    except Exception as e:
        print(f"⚠️  Error while finding active folders: {e}")
        return []




def select_folder_for_new_bookmark(bookmark_name):
    """Let user select which folder to create a new bookmark in"""
    active_folders = get_all_active_folders()

    if not active_folders:
        print("❌ No active folders found")
        return create_new_folder()

    print(f"📝 Creating new bookmark '{bookmark_name}' - select folder:")

    # Show existing folders
    for i, folder_path in enumerate(active_folders, 1):
        folder_name = os.path.basename(folder_path)
        folder_meta = load_folder_meta(folder_path)
        created_at = folder_meta.get('created_at', 'unknown')
        print(f"   {i}. {folder_name} (created: {created_at[:10]})")

    print(f"   {len(active_folders) + 1}. Create new folder")

    while True:
        try:
            choice = input(
                f"Enter choice (1-{len(active_folders) + 1}): ").strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(active_folders):
                selected_folder = active_folders[choice_num - 1]
                print(
                    f"✅ Selected folder: {os.path.basename(selected_folder)}")
                return selected_folder
            elif choice_num == len(active_folders) + 1:
                return create_new_folder()
            else:
                print(
                    f"❌ Invalid choice. Please enter 1-{len(active_folders) + 1}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            return None


def create_new_folder():
    """Create a new folder when no active folders exist"""
    try:
        # Ensure bookmarks directory exists
        if not os.path.exists(BOOKMARKS_DIR):
            os.makedirs(BOOKMARKS_DIR)

        # Prompt for folder name
        print("📝 No active folders found. Creating a new folder...")
        folder_name = input("Enter new folder name: ").strip()

        if not folder_name:
            print("❌ Folder name cannot be empty")
            return None

        # Create folder directory
        folder_dir = os.path.join(BOOKMARKS_DIR, folder_name)
        if os.path.exists(folder_dir):
            print(f"⚠️  Folder '{folder_name}' already exists")
            return folder_dir

        os.makedirs(folder_dir)

        # Create folder metadata
        if create_folder_meta(folder_dir, folder_name):
            print(f"✅ Created new folder: '{folder_name}'")
            return folder_dir
        else:
            print(f"❌ Failed to create folder metadata")
            return None

    except Exception as e:
        print(f"❌ Error creating new folder: {e}")
        return None


def get_current_folder_dir():
    """Get the current OBS folder directory"""
    try:
        if IS_DEBUG:
            print(f"🔍 Looking for folders in: {BOOKMARKS_DIR}")

        if not os.path.exists(BOOKMARKS_DIR):
            print(f"❌ Bookmarks directory does not exist: {BOOKMARKS_DIR}")
            return None

        # Get existing folders (excluding archive and screenshots dirs)
        excluded_dirs = {"archive"}
        folders = []
        for item in os.listdir(BOOKMARKS_DIR):
            item_path = os.path.join(BOOKMARKS_DIR, item)
            if os.path.isdir(item_path) and item not in excluded_dirs:
                folders.append(item)

        print(f"🔍 Found folders: {folders}")

        if not folders:
            print(f"❌ No active folders found")
            # CREATE NEW FOLDER WHEN NONE EXIST
            return create_new_folder()

        # Find most recent folder - look for folder with most recent activity
        most_recent = folders[0]
        most_recent_time = 0
        for folder in folders:
            folder_path = os.path.join(BOOKMARKS_DIR, folder)
            folder_meta_file = os.path.join(folder_path, "folder_meta.json")

            # Check folder_meta.json last_modified, fall back to directory mtime
            if os.path.exists(folder_meta_file):
                try:
                    with open(folder_meta_file, 'r') as f:
                        folder_meta = json.load(f)
                        last_modified = folder_meta.get(
                            'last_modified', folder_meta.get('created_at', ''))
                        if last_modified:
                            mod_time = datetime.fromisoformat(
                                last_modified.replace('Z', '+00:00')).timestamp()
                        else:
                            mod_time = os.path.getmtime(folder_path)
                except:
                    mod_time = os.path.getmtime(folder_path)
            else:
                mod_time = os.path.getmtime(folder_path)

            if mod_time > most_recent_time:
                most_recent_time = mod_time
                most_recent = folder

        folder_dir = os.path.join(BOOKMARKS_DIR, most_recent)
        if IS_DEBUG:
            print(f"🎯 Using folder directory: {folder_dir}")
        return folder_dir
    except Exception as e:
        print(f"⚠️  Could not determine folder directory: {e}")
        return None


def find_folder_by_name(folder_name):
    """Find folder directory by name or full relative path (e.g. kerch/comp/m02)"""
    active_folders = get_all_active_folders()
    for folder_path in active_folders:
        # Match either exact basename or full relative path from BOOKMARKS_DIR
        rel_path = os.path.relpath(folder_path, BOOKMARKS_DIR)
        folder_basename = os.path.basename(folder_path)
        
        # Check for exact matches first
        if folder_name == folder_basename or folder_name == rel_path:
            return folder_path
        
        # Check for partial matches (e.g., "respawn" should match "respawn-allies")
        if folder_name.lower() in folder_basename.lower():
            return folder_path
            
    return None



def create_folder_with_name(folder_name):
    """Create a new folder with the specified name"""
    try:
        # Ensure bookmarks directory exists
        if not os.path.exists(BOOKMARKS_DIR):
            os.makedirs(BOOKMARKS_DIR)

        # Create folder directory
        folder_dir = os.path.join(BOOKMARKS_DIR, folder_name)
        if os.path.exists(folder_dir):
            print(f"⚠️  Folder '{folder_name}' already exists")
            return folder_dir

        os.makedirs(folder_dir)

        # Create folder metadata
        if create_folder_meta(folder_dir, folder_name):
            print(f"✅ Created new folder: '{folder_name}'")
            return folder_dir
        else:
            print(f"❌ Failed to create folder metadata")
            return None

    except Exception as e:
        print(f"❌ Error creating folder '{folder_name}': {e}")
        return None


def parse_folder_bookmark_arg(bookmark_arg):
    """
    Parses a bookmark path in the format 'folder:bookmark' or 'folder:subfolder:bookmark'
    and returns (folder_name, bookmark_name).

    - Example: 'kerch:comp:m01:01-np' becomes:
        folder_name: 'kerch'
        bookmark_name: 'comp:m01:01-np'
    - Example: 'respawn-allies:ra-00-main-screen' becomes:
        folder_name: 'respawn-allies'
        bookmark_name: 'ra-00-main-screen'
    """
    if not bookmark_arg or ':' not in bookmark_arg:
        return None, bookmark_arg  # no folder path

    parts = bookmark_arg.split(':')
    if len(parts) == 2:
        # Simple case: folder:bookmark
        folder_name = parts[0]
        bookmark_name = parts[1]
    else:
        # Complex case: folder:subfolder:bookmark
        # Take the first part as folder, rest as bookmark path
        folder_name = parts[0]
        bookmark_name = ':'.join(parts[1:])  # Join the rest with colons

    return folder_name, bookmark_name



def update_folder_last_bookmark(folder_dir, bookmark_name):
    """Update the folder metadata with the last used bookmark."""
    folder_meta_path = os.path.join(folder_dir, "folder_meta.json")

    # Load existing metadata or create new
    if os.path.exists(folder_meta_path):
        try:
            with open(folder_meta_path, 'r') as f:
                meta_data = json.load(f)
        except json.JSONDecodeError:
            meta_data = {}
    else:
        meta_data = {
            "created_at": datetime.now().isoformat(),
            "description": "",
            "tags": []
        }

    # Update last used bookmark
    meta_data["last_used_bookmark"] = bookmark_name
    meta_data["last_modified"] = datetime.now().isoformat()

    # Save updated metadata
    with open(folder_meta_path, 'w') as f:
        json.dump(meta_data, f, indent=2)
