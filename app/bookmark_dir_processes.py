import os

from app.utils.printing_utils import *
from app.consts.bookmarks_consts import IS_DEBUG, ABS_OBS_BOOKMARKS_DIR, EXCLUDED_DIRS
from app.bookmarks_meta import create_directory_meta
from app.utils.decorators import print_def_name, memoize

IS_PRINT_DEF_NAME = True

@print_def_name(False)
@memoize
def get_all_valid_root_dir_names() -> list[str]:
    """Collect all folder paths under ABS_OBS_BOOKMARKS_DIR that contain folder_meta.json (excluding archive)"""
    print('++++ get_all_valid_root_dir_names')
    try:
        if IS_DEBUG:
            print(f"🔍 Scanning for folders inside: {ABS_OBS_BOOKMARKS_DIR}")

        if not os.path.exists(ABS_OBS_BOOKMARKS_DIR):
            print(f"❌ Bookmarks directory does not exist: {ABS_OBS_BOOKMARKS_DIR}")
            return []

        excluded_dirs = EXCLUDED_DIRS
        live_folders = []

        # Only scan the immediate subdirectories of ABS_OBS_BOOKMARKS_DIR
        for item in os.listdir(ABS_OBS_BOOKMARKS_DIR):
            item_path = os.path.join(ABS_OBS_BOOKMARKS_DIR, item)
            if os.path.isdir(item_path) and item not in excluded_dirs:
                # Check if this directory contains a folder_meta.json (indicating it's a folder, not a bookmark)
                folder_meta_file = os.path.join(item_path, "folder_meta.json")
                if os.path.exists(folder_meta_file):
                    live_folders.append(item_path)
                    if IS_DEBUG:
                        print(f"✅ Found live folder: {item_path}")

        return live_folders

    except Exception as e:
        print(f"⚠️  Error while finding live folders: {e}")
        return []

# Unused
# @print_def_name(IS_PRINT_DEF_NAME)
# def select_dir_for_new_bookmark(bookmark_name):
#     """Let user select which folder to create a new bookmark in"""
#     print_color('???? 0 bookmark_string select_dir_for_new_bookmark:', 'red')
#     print(bookmark_name)

#     live_folders = get_all_valid_root_dir_names()

#     if not live_folders:
#         print("❌ No live folders found")
#         return create_new_bookmark_dir()

#     print(f"📝 Creating new bookmark '{bookmark_name}' - select folder:")

#     # Show existing folders
#     for i, folder_path in enumerate(live_folders, 1):
#         directory_name = os.path.basename(folder_path)
#         folder_meta = load_folder_meta(folder_path)
#         created_at = folder_meta.get('created_at', 'unknown')
#         print(f"   {i}. {directory_name} (created: {created_at[:10]})")

#     print(f"   {len(live_folders) + 1}. Create new folder")

#     while True:
#         try:
#             choice = input(
#                 f"Enter choice (1-{len(live_folders) + 1}): ").strip()
#             choice_num = int(choice)

#             if 1 <= choice_num <= len(live_folders):
#                 selected_folder = live_folders[choice_num - 1]
#                 print(
#                     f"✅ Selected folder: {os.path.basename(selected_folder)}")
#                 return selected_folder
#             elif choice_num == len(live_folders) + 1:
#                 return create_new_bookmark_dir()
#             else:
#                 print(
#                     f"❌ Invalid choice. Please enter 1-{len(live_folders) + 1}")
#         except ValueError:
#             print("❌ Please enter a valid number")
#         except KeyboardInterrupt:
#             print("\n❌ Cancelled")
#             return None


@print_def_name(IS_PRINT_DEF_NAME)
def create_new_bookmark_dir():
    """Create a new folder when no live folders exist"""
    try:
        # Ensure bookmarks directory exists
        if not os.path.exists(ABS_OBS_BOOKMARKS_DIR):
            os.makedirs(ABS_OBS_BOOKMARKS_DIR)

        # Prompt for folder name
        print("📝 No live folders found. Creating a new folder...")
        directory_name = input("Enter new folder name: ").strip()

        if not directory_name:
            print("❌ Folder name cannot be empty")
            return None

        # Create folder directory
        dir_abs_path = os.path.join(ABS_OBS_BOOKMARKS_DIR, directory_name)
        if os.path.exists(dir_abs_path):
            print(f"⚠️  Folder '{directory_name}' already exists")
            return dir_abs_path

        os.makedirs(dir_abs_path)

        # Create folder metadata
        if create_directory_meta(dir_abs_path, directory_name):
            print(f"✅ Created new folder: '{directory_name}'")
            return dir_abs_path
        else:
            print(f"❌ Failed to create folder metadata")
            return None

    except Exception as e:
        print(f"❌ Error creating new folder: {e}")
        return None


# TODO(MFB): This needs to be updated to pull the bookmark name from the end and the rest as the folder_path.

@print_def_name(IS_PRINT_DEF_NAME)
def parse_cli_bookmark_args(args_for_run_bookmarks):
    """
    Parses a bookmark path in the format 'folder:bookmark' or 'folder:subfolder:bookmark'
    and returns (dir_colon_rel, bookmark_tail_name).

    - Example: 'kerch:comp:m01:01-np' becomes:
        dir_colon_rel: 'kerch:comp:m01'
        bookmark_tail_name: '01-np'
    - Example: 'respawn-allies:ra-00-main-screen' becomes:
        dir_colon_rel: 'respawn-allies'
        bookmark_tail_name: 'ra-00-main-screen'
    """
    if not args_for_run_bookmarks or ':' not in args_for_run_bookmarks:
        return None, args_for_run_bookmarks  # no folder path

    parts = args_for_run_bookmarks.split(':')
    # Take the last entry as the bookmark name and the rest as the folder name
    dir_colon_rel = ':'.join(parts[:-1])
    bookmark_tail_name = parts[-1]

    print(
        f"🎯 Specified folder: '{dir_colon_rel}', bookmark path: '{bookmark_tail_name}'")

    return dir_colon_rel, bookmark_tail_name
