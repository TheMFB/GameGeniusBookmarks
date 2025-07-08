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
from app.bookmarks_meta import load_session_meta, create_session_meta

def get_all_active_sessions():
    """Get all active session directories (excluding archive and screenshots)"""
    try:
        if IS_DEBUG:
            print(f"🔍 Looking for sessions in: {BOOKMARKS_DIR}")

        if not os.path.exists(BOOKMARKS_DIR):
            print(f"❌ Bookmarks directory does not exist: {BOOKMARKS_DIR}")
            return []

        # Get existing sessions (excluding archive and screenshots dirs)
        excluded_dirs = {"archive"}
        sessions = []
        for item in os.listdir(BOOKMARKS_DIR):
            item_path = os.path.join(BOOKMARKS_DIR, item)
            if os.path.isdir(item_path) and item not in excluded_dirs:
                sessions.append(item_path)

        return sessions
    except Exception as e:
        print(f"⚠️  Could not determine session directories: {e}")
        return []


def select_session_for_new_bookmark(bookmark_name):
    """Let user select which session to create a new bookmark in"""
    active_sessions = get_all_active_sessions()

    if not active_sessions:
        print("❌ No active sessions found")
        return create_new_session()

    print(f"📝 Creating new bookmark '{bookmark_name}' - select session:")

    # Show existing sessions
    for i, session_path in enumerate(active_sessions, 1):
        session_name = os.path.basename(session_path)
        session_meta = load_session_meta(session_path)
        created_at = session_meta.get('created_at', 'unknown')
        print(f"   {i}. {session_name} (created: {created_at[:10]})")

    print(f"   {len(active_sessions) + 1}. Create new session")

    while True:
        try:
            choice = input(
                f"Enter choice (1-{len(active_sessions) + 1}): ").strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(active_sessions):
                selected_session = active_sessions[choice_num - 1]
                print(
                    f"✅ Selected session: {os.path.basename(selected_session)}")
                return selected_session
            elif choice_num == len(active_sessions) + 1:
                return create_new_session()
            else:
                print(
                    f"❌ Invalid choice. Please enter 1-{len(active_sessions) + 1}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            return None


def create_new_session():
    """Create a new session when no active sessions exist"""
    try:
        # Ensure bookmarks directory exists
        if not os.path.exists(BOOKMARKS_DIR):
            os.makedirs(BOOKMARKS_DIR)

        # Prompt for session name
        print("📝 No active sessions found. Creating a new session...")
        session_name = input("Enter new session name: ").strip()

        if not session_name:
            print("❌ Session name cannot be empty")
            return None

        # Create session directory
        session_dir = os.path.join(BOOKMARKS_DIR, session_name)
        if os.path.exists(session_dir):
            print(f"⚠️  Session '{session_name}' already exists")
            return session_dir

        os.makedirs(session_dir)

        # Create session metadata
        if create_session_meta(session_dir, session_name):
            print(f"✅ Created new session: '{session_name}'")
            return session_dir
        else:
            print(f"❌ Failed to create session metadata")
            return None

    except Exception as e:
        print(f"❌ Error creating new session: {e}")
        return None


def get_current_session_dir():
    """Get the current OBS session directory"""
    try:
        if IS_DEBUG:
            print(f"🔍 Looking for sessions in: {BOOKMARKS_DIR}")

        if not os.path.exists(BOOKMARKS_DIR):
            print(f"❌ Bookmarks directory does not exist: {BOOKMARKS_DIR}")
            return None

        # Get existing sessions (excluding archive and screenshots dirs)
        excluded_dirs = {"archive"}
        sessions = []
        for item in os.listdir(BOOKMARKS_DIR):
            item_path = os.path.join(BOOKMARKS_DIR, item)
            if os.path.isdir(item_path) and item not in excluded_dirs:
                sessions.append(item)

        print(f"🔍 Found sessions: {sessions}")

        if not sessions:
            print(f"❌ No active sessions found")
            # CREATE NEW SESSION WHEN NONE EXIST
            return create_new_session()

        # Find most recent session - look for session with most recent activity
        most_recent = sessions[0]
        most_recent_time = 0
        for session in sessions:
            session_path = os.path.join(BOOKMARKS_DIR, session)
            session_meta_file = os.path.join(session_path, "session_meta.json")

            # Check session_meta.json last_modified, fall back to directory mtime
            if os.path.exists(session_meta_file):
                try:
                    with open(session_meta_file, 'r') as f:
                        session_meta = json.load(f)
                        last_modified = session_meta.get(
                            'last_modified', session_meta.get('created_at', ''))
                        if last_modified:
                            mod_time = datetime.fromisoformat(
                                last_modified.replace('Z', '+00:00')).timestamp()
                        else:
                            mod_time = os.path.getmtime(session_path)
                except:
                    mod_time = os.path.getmtime(session_path)
            else:
                mod_time = os.path.getmtime(session_path)

            if mod_time > most_recent_time:
                most_recent_time = mod_time
                most_recent = session

        session_dir = os.path.join(BOOKMARKS_DIR, most_recent)
        if IS_DEBUG:
            print(f"🎯 Using session directory: {session_dir}")
        return session_dir
    except Exception as e:
        print(f"⚠️  Could not determine session directory: {e}")
        return None


def find_session_by_name(session_name):
    """Find session directory by name"""
    active_sessions = get_all_active_sessions()
    for session_path in active_sessions:
        if os.path.basename(session_path) == session_name:
            return session_path
    return None


def create_session_with_name(session_name):
    """Create a new session with the specified name"""
    try:
        # Ensure bookmarks directory exists
        if not os.path.exists(BOOKMARKS_DIR):
            os.makedirs(BOOKMARKS_DIR)

        # Create session directory
        session_dir = os.path.join(BOOKMARKS_DIR, session_name)
        if os.path.exists(session_dir):
            print(f"⚠️  Session '{session_name}' already exists")
            return session_dir

        os.makedirs(session_dir)

        # Create session metadata
        if create_session_meta(session_dir, session_name):
            print(f"✅ Created new session: '{session_name}'")
            return session_dir
        else:
            print(f"❌ Failed to create session metadata")
            return None

    except Exception as e:
        print(f"❌ Error creating session '{session_name}': {e}")
        return None


def parse_session_bookmark_arg(bookmark_arg):
    """
    Parse bookmark argument that may contain session:bookmark format or nested folder structure
    
    Args:
        bookmark_arg: String that may be "bookmark", "session:bookmark", or "session:folder1:folder2:bookmark"
        
    Returns:
        tuple: (session_name, bookmark_path) where session_name may be None and bookmark_path is the full nested path
    """
    if ':' in bookmark_arg:
        parts = bookmark_arg.split(':')  # Split on all colons
        if len(parts) >= 2:
            session_name = parts[0].strip()
            # Join all remaining parts as the nested bookmark path
            bookmark_path = '/'.join(parts[1:])
            return session_name, bookmark_path

    # No colon found, treat as just bookmark name
    return None, bookmark_arg
