# type: ignore
"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
from app.bookmarks_consts import IS_DEBUG, HIDDEN_COLOR, RESET_COLOR, USAGE_HELP
from app.bookmarks_sessions import get_all_active_sessions
from app.bookmarks_meta import load_session_meta, load_folder_meta
from app.bookmarks import load_bookmarks_from_session
from app.utils import print_color


def print_all_sessions_and_bookmarks(current_session_name=None, current_bookmark_name=None):
    """Print all sessions and their bookmarks, highlighting the current one"""
    active_sessions = get_all_active_sessions()

    if not active_sessions:
        print("❌ No active sessions found")
        return

    # print("📚 All Sessions and Bookmarks:")
    # print("=" * 50)

    for session_path in active_sessions:
        session_name = os.path.basename(session_path)

        # Print session name
        if session_name == current_session_name:
            print_color(f"📁 {session_name}", 'green')
        else:
            print(f"📁 {session_name}")

        # Load session metadata and display description if it exists
        session_meta = load_session_meta(session_path)
        session_description = session_meta.get('description', '')
        if session_description:
            print_color(f"   {session_description}", 'cyan')

        # Load session metadata and display tags if they exist
        session_meta = load_session_meta(session_path)
        session_tags = session_meta.get('tags', [])
        if session_tags:
            print_color(
                f"   {' '.join(f'•{tag}' for tag in session_tags)}", 'cyan')

        # Load and print bookmarks for this session
        bookmarks = load_bookmarks_from_session(session_path)
        if bookmarks:
            from collections import defaultdict

            # Step 1: Build folder and bookmark hierarchies
            # full_folder_path -> list of (bookmark_name, bookmark_info)
            folder_hierarchy = defaultdict(list)
            # parent_folder_path -> list of child folder paths
            folder_tree = defaultdict(list)

            if IS_DEBUG:
                print(f"🔍 Debug - All bookmarks in {session_name}:")
                for path, info in sorted(bookmarks.items()):
                    print(
                        f"   {path} -> {info.get('timestamp_formatted', 'unknown')}")
                print()

            for bookmark_path, bookmark_info in bookmarks.items():
                path_parts = bookmark_path.split('/')

                if len(path_parts) == 1:
                    folder_hierarchy['root'].append(
                        (bookmark_path, bookmark_info))
                    if IS_DEBUG:
                        print(
                            f"🔍 Debug - Added root bookmark: {bookmark_path}")
                else:
                    full_folder_path = '/'.join(path_parts[:-1])
                    bookmark_name = path_parts[-1]
                    folder_hierarchy[full_folder_path].append(
                        (bookmark_name, bookmark_info))
                    if IS_DEBUG:
                        print(
                            f"🔍 Debug - Added bookmark {bookmark_name} to folder {full_folder_path}")

                    # Build the folder tree structure
                    for i in range(1, len(path_parts)):
                        parent = '/'.join(path_parts[:i-1]
                                          ) if i > 1 else 'root'
                        child = '/'.join(path_parts[:i])
                        if child not in folder_tree[parent]:
                            folder_tree[parent].append(child)
                            if IS_DEBUG:
                                print(
                                    f"🔍 Debug - Added folder {child} under {parent}")

            if IS_DEBUG:
                print(f"🔍 Debug - Folder hierarchy for {session_name}:")
                for folder, bookmarks_in_folder in sorted(folder_hierarchy.items()):
                    print(
                        f"   {folder}: {[b[0] for b in bookmarks_in_folder]}")
                print()

            def print_folder_contents(folder_path, indent_level):
                indent = "   " * indent_level

                # Print folder (skip for 'root')
                if folder_path != 'root':
                    folder_name = folder_path.split('/')[-1]

                    # Highlight if this folder contains current bookmark
                    folder_contains_current = False
                    if current_bookmark_name and session_name == current_session_name:
                        current_path_parts = current_bookmark_name.split('/')
                        current_folder_path = '/'.join(current_path_parts[:-1])
                        folder_contains_current = folder_path == current_folder_path or current_folder_path.startswith(
                            folder_path + '/')

                    if folder_contains_current:
                        print_color(f"{indent}📁 {folder_name}", 'green')
                    else:
                        print(f"{indent}📁 {folder_name}")

                    # Load and display folder metadata
                    folder_meta = load_folder_meta(
                        os.path.join(session_path, folder_path))
                    folder_description = folder_meta.get('description', '')
                    folder_tags = folder_meta.get('tags', [])

                    if folder_description:
                        print_color(f"{indent}   {folder_description}", 'cyan')

                    if folder_tags:
                        print_color(
                            f"{indent}   {' '.join(f'•{tag}' for tag in folder_tags)}", 'cyan')

                # Print bookmarks directly in this folder
                for bookmark_name, bookmark_info in sorted(folder_hierarchy.get(folder_path, [])):
                    timestamp = bookmark_info.get(
                        'timestamp_formatted', 'unknown time')
                    if len(timestamp) < 5:
                        timestamp = '0' + timestamp

                    # Construct full path
                    full_path = f"{folder_path}/{bookmark_name}" if folder_path != 'root' else bookmark_name
                    is_current = (
                        session_name == current_session_name and full_path == current_bookmark_name)

                    if is_current:
                        print_color(
                            f"{indent}   • {timestamp} 📖 {bookmark_name} (current)", 'green')
                    else:
                        ref_path = f"{session_name}:{full_path.replace('/', ':')}"
                        print(
                            f"{indent}   • {timestamp} 📖 {bookmark_name} {HIDDEN_COLOR} {ref_path}{RESET_COLOR}")

                    # Bookmark description
                    bookmark_description = bookmark_info.get('description', '')
                    if bookmark_description:
                        print_color(
                            f"{indent}      {bookmark_description}", 'cyan')

                    # Bookmark tags
                    bookmark_tags = bookmark_info.get('tags', [])
                    if bookmark_tags:
                        print_color(
                            f"{indent}      {' '.join(f'•{tag}' for tag in bookmark_tags)}", 'cyan')

                # Recurse into subfolders
                for child_folder in sorted(folder_tree.get(folder_path, [])):
                    print_folder_contents(child_folder, indent_level + 1)

            # Start the recursive display from root
            print_folder_contents('root', indent_level=0)
        else:
            print("   (no bookmarks)")

        print()  # Empty line between sessions

    print('')
    # Convert slashes to colons for display
    display_bookmark_name = current_bookmark_name.replace('/', ':') if current_bookmark_name else ''
    print_color(f'runonce-redis {current_session_name}:{display_bookmark_name}', 'blue')
    print(
        f"   {USAGE_HELP}")

    print("=" * 50)
