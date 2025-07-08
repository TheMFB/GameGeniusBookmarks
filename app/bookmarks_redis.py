#!/usr/bin/env python3
# type: ignore
# pylint: disable-all
# flake8: noqa
import subprocess
import os

from app.bookmarks_consts import IS_DEBUG, INITIAL_REDIS_STATE_DIR
from app.bookmarks_sessions import get_all_active_sessions, parse_session_bookmark_arg, find_session_by_name
from app.bookmarks import find_preceding_bookmark, find_matching_bookmark


def run_redis_command(command_args):
    """Run Redis management command"""
    try:
        cmd = f"docker exec -it session_manager python -m utils.standalone.redis_{command_args[0]} {' '.join(command_args[1:])}"
        if IS_DEBUG:
            print(f"🔧 Running Redis command: {' '.join(command_args)}")
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Redis command failed: {' '.join(command_args)}")
            print(f"   Error: {result.stderr}")
            print(f"   Output: {result.stdout}")
            return False
        if IS_DEBUG:
            print(f"✅ Redis command succeeded: {' '.join(command_args)}")
        return True
    except Exception as e:
        print(f"❌ Error running Redis command: {' '.join(command_args)}")
        print(f"   Exception: {e}")
        return False


def copy_preceding_redis_state(bookmark_name, session_dir):
    """Copy redis_after.json from the preceding bookmark to redis_before.json of current bookmark"""
    preceding_bookmark = find_preceding_bookmark(bookmark_name, session_dir)
    if not preceding_bookmark:
        print(f"❌ No preceding bookmark found for '{bookmark_name}'")
        return False

    # Handle nested paths for preceding bookmark
    preceding_dir = os.path.join(session_dir, preceding_bookmark)
    current_dir = os.path.join(session_dir, bookmark_name)

    # Ensure current bookmark directory exists
    if not os.path.exists(current_dir):
        os.makedirs(current_dir)

    # Copy redis_after.json from preceding to redis_before.json of current
    preceding_after = os.path.join(preceding_dir, "redis_after.json")
    current_before = os.path.join(current_dir, "redis_before.json")

    if not os.path.exists(preceding_after):
        print(
            f"❌ Preceding bookmark '{preceding_bookmark}' has no redis_after.json")
        return False

    try:
        import shutil
        if os.path.exists(preceding_after):
            shutil.copy2(preceding_after, current_before)
        else:
            print(
                f"❌ Preceding bookmark '{preceding_bookmark}' has no redis_after.json")
            return False

        # Also copy friendly version if it exists
        preceding_friendly_after = os.path.join(
            preceding_dir, "friendly_redis_after.json")
        current_friendly_before = os.path.join(
            current_dir, "friendly_redis_before.json")

        if os.path.exists(preceding_friendly_after):
            shutil.copy2(preceding_friendly_after, current_friendly_before)
        else:
            print(
                f"❌ Preceding bookmark '{preceding_bookmark}' has no friendly_redis_after.json")
            return False

        return True
    except Exception as e:
        print(f"❌ Error copying preceding Redis state: {e}")
        return False


def copy_specific_bookmark_redis_state(source_bookmark_arg, target_bookmark_name, target_session_dir):
    """Copy redis_after.json from a specific bookmark to redis_before.json of target bookmark"""
    # Parse the source bookmark argument (may be "bookmark" or "session:bookmark")
    source_session_name, source_bookmark_name = parse_session_bookmark_arg(
        source_bookmark_arg)

    if IS_DEBUG:
        print(
            f"🔍 Copying from source: session='{source_session_name}', bookmark='{source_bookmark_name}'")

    # Find the source bookmark
    source_bookmark_info = None
    source_session_dir = None

    if source_session_name:
        # Specific session specified
        source_session_dir = find_session_by_name(source_session_name)
        if not source_session_dir:
            print(f"❌ Source session '{source_session_name}' not found")
            return False

        # Find bookmark in that session
        matched_name, source_bookmark_info = find_matching_bookmark(
            source_bookmark_name, source_session_dir)
        if not matched_name:
            print(
                f"❌ Source bookmark '{source_bookmark_name}' not found in session '{source_session_name}'")
            return False
        source_bookmark_name = matched_name
    else:
        # Search across all sessions
        active_sessions = get_all_active_sessions()
        for session_path in active_sessions:
            matched_name, bookmark_info = find_matching_bookmark(
                source_bookmark_name, session_path)
            if matched_name:
                source_bookmark_name = matched_name
                source_bookmark_info = bookmark_info
                source_session_dir = session_path
                source_session_name = os.path.basename(session_path)
                break

        if not source_bookmark_info:
            print(
                f"❌ Source bookmark '{source_bookmark_name}' not found in any session")
            return False

    print(
        f"📋 Copying Redis state from '{source_session_name}:{source_bookmark_name}' to '{target_bookmark_name}'")

    # Ensure target bookmark directory exists
    target_dir = os.path.join(target_session_dir, target_bookmark_name)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Copy redis_after.json from source to redis_before.json of target
    source_after = os.path.join(
        source_session_dir, source_bookmark_name, "redis_after.json")
    target_before = os.path.join(target_dir, "redis_before.json")

    if not os.path.exists(source_after):
        print(
            f"❌ Source bookmark '{source_session_name}:{source_bookmark_name}' has no redis_after.json")
        return False

    try:
        import shutil
        shutil.copy2(source_after, target_before)
        print(
            f"✅ Copied redis_after.json from '{source_session_name}:{source_bookmark_name}'")

        # Also copy friendly version if it exists
        source_friendly_after = os.path.join(
            source_session_dir, source_bookmark_name, "friendly_redis_after.json")
        target_friendly_before = os.path.join(
            target_dir, "friendly_redis_before.json")

        if os.path.exists(source_friendly_after):
            shutil.copy2(source_friendly_after, target_friendly_before)
            print(
                f"✅ Copied friendly_redis_after.json from '{source_session_name}:{source_bookmark_name}'")
        else:
            print(f"⚠️  Source bookmark has no friendly_redis_after.json")

        return True
    except Exception as e:
        print(
            f"❌ Error copying Redis state from '{source_session_name}:{source_bookmark_name}': {e}")
        return False


def copy_initial_redis_state(bookmark_name, session_dir):
    """Copy initial Redis state files to the bookmark directory"""
    current_dir = os.path.join(session_dir, bookmark_name)

    # Ensure current bookmark directory exists
    if not os.path.exists(current_dir):
        os.makedirs(current_dir)

    # Paths to initial state files
    initial_redis = os.path.join(
        INITIAL_REDIS_STATE_DIR, "initial_redis_before.json")
    initial_friendly = os.path.join(
        INITIAL_REDIS_STATE_DIR, "initial_friendly_redis_before.json")

    # Copy initial redis state
    current_before = os.path.join(current_dir, "redis_before.json")
    current_friendly_before = os.path.join(
        current_dir, "friendly_redis_before.json")

    try:
        import shutil

        if os.path.exists(initial_redis):
            shutil.copy2(initial_redis, current_before)
            print(f"📋 Copied initial_redis_before.json to redis_before.json")
        else:
            print(f"❌ Initial Redis state file not found: {initial_redis}")
            return False

        if os.path.exists(initial_friendly):
            shutil.copy2(initial_friendly, current_friendly_before)
        else:
            print(
                f"❌ Initial friendly Redis state file not found: {initial_friendly}")
            return False

        return True
    except Exception as e:
        print(f"❌ Error copying initial Redis state: {e}")
        return False
