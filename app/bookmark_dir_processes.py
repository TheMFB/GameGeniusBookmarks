import os

from app.utils.printing_utils import *
from app.consts.bookmarks_consts import IS_DEBUG, ABS_OBS_BOOKMARKS_DIR, EXCLUDED_DIRS
from app.bookmarks_meta import load_folder_meta, create_folder_meta
from app.utils.decorators import print_def_name, memoize

IS_PRINT_DEF_NAME = True

@print_def_name(False)
@memoize
def get_all_valid_root_dir_names():
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


@print_def_name(IS_PRINT_DEF_NAME)
def select_dir_for_new_bookmark(bookmark_name):
    """Let user select which folder to create a new bookmark in"""
    print_color('???? 0 bookmark_string select_dir_for_new_bookmark:', 'red')
    print(bookmark_name)

    live_folders = get_all_valid_root_dir_names()

    if not live_folders:
        print("❌ No live folders found")
        return create_new_bookmark_dir()

    print(f"📝 Creating new bookmark '{bookmark_name}' - select folder:")

    # Show existing folders
    for i, folder_path in enumerate(live_folders, 1):
        folder_name = os.path.basename(folder_path)
        folder_meta = load_folder_meta(folder_path)
        created_at = folder_meta.get('created_at', 'unknown')
        print(f"   {i}. {folder_name} (created: {created_at[:10]})")

    print(f"   {len(live_folders) + 1}. Create new folder")

    while True:
        try:
            choice = input(
                f"Enter choice (1-{len(live_folders) + 1}): ").strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(live_folders):
                selected_folder = live_folders[choice_num - 1]
                print(
                    f"✅ Selected folder: {os.path.basename(selected_folder)}")
                return selected_folder
            elif choice_num == len(live_folders) + 1:
                return create_new_bookmark_dir()
            else:
                print(
                    f"❌ Invalid choice. Please enter 1-{len(live_folders) + 1}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            return None


@print_def_name(IS_PRINT_DEF_NAME)
def create_new_bookmark_dir():
    """Create a new folder when no live folders exist"""
    try:
        # Ensure bookmarks directory exists
        if not os.path.exists(ABS_OBS_BOOKMARKS_DIR):
            os.makedirs(ABS_OBS_BOOKMARKS_DIR)

        # Prompt for folder name
        print("📝 No live folders found. Creating a new folder...")
        folder_name = input("Enter new folder name: ").strip()

        if not folder_name:
            print("❌ Folder name cannot be empty")
            return None

        # Create folder directory
        folder_dir = os.path.join(ABS_OBS_BOOKMARKS_DIR, folder_name)
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


@print_def_name(IS_PRINT_DEF_NAME)
def find_bookmark_dir_by_name(bookmark_dir_arg: str):
    """Find folder directory by name or full relative path (e.g. kerch/comp/m02)"""
    # TODO(): ++++ This is not working as expected. We should pull in the all bookmarks json, and attempt to step through the tree, and see if there are any full / partial matches. The all_live_folders is giving a full system path, but only the basename for what we need.

    # ---- 0 cli_bookmark_dir:
    # 'videos/0001_green_dog/g01/m01'
    # ---- 0 folder_name find_bookmark_dir_by_name:
    # videos/0001_green_dog/g01/m01
    # ---- 1 folder_path find_bookmark_dir_by_name:
    # /Users/mfb/dev/MFBTech/GameGeniusProject/GameGenius/game-genius-bookmarks/obs_bookmark_saves/videos
    # ---- 1 folder_dir find_bookmark_dir_by_name:
    # None
    print_color('---- 0 bookmark_dir_abs find_bookmark_dir_by_name:', 'green')
    print(bookmark_dir_arg)


    # live_root_dirs_abs = get_all_valid_root_dir_names()
    # for live_root_dir_abs in live_root_dirs_abs:
    #     print_color(
    #         '---- 1 live_root_dir_abs find_bookmark_dir_by_name:', 'magenta')
    #     print(live_root_dir_abs)

    #     # Match either exact basename or full relative path from ABS_OBS_BOOKMARKS_DIR
    #     live_root_dir_name = os.path.relpath(live_root_dir_abs, ABS_OBS_BOOKMARKS_DIR)
    #     print_color(
    #         '++++ 2 live_root_dir_name find_bookmark_dir_by_name:', 'magenta')
    #     print(live_root_dir_name)


    #     # ✅ Check for exact matches first
    #     if folder_name == live_root_dir_name or folder_name == rel_path:
    #         return rel_path

    #     # ✅ Check for partial matches (e.g., "respawn" should match "respawn-allies")
    #     if folder_name.lower() in live_root_dir_name.lower():
    #         return rel_path

    # return None
    return bookmark_dir_arg

# TODO(): How is this different from the one above? Any way to combine?

@print_def_name(IS_PRINT_DEF_NAME)
def create_dir_with_name(rel_folder_dir):
    """Create a new folder with the specified name"""

    try:
        # Ensure bookmarks directory exists
        if not os.path.exists(ABS_OBS_BOOKMARKS_DIR):
            os.makedirs(ABS_OBS_BOOKMARKS_DIR)

        # Create folder directory
        abs_folder_dir = os.path.join(ABS_OBS_BOOKMARKS_DIR, rel_folder_dir)
        if os.path.exists(abs_folder_dir):
            print(f"⚠️  Folder '{abs_folder_dir}' already exists")
            return abs_folder_dir

        os.makedirs(abs_folder_dir)

        # TODO(): HERE go ahead and create the folder_meta.json file in each of these folders if it doesn't exist. (recursive check down path)

        # Create folder metadata
        if create_folder_meta(abs_folder_dir):
            return abs_folder_dir
        else:
            print(f"❌ Failed to create folder metadata")
            return None

    except Exception as e:
        print(f"❌ Error creating folder '{rel_folder_dir}': {e}")
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


# TODO(): This is for a local-last saved bookmark. For now, we're not using it.
# @print_def_name(IS_PRINT_DEF_NAME)
# def update_folder_last_bookmark(folder_dir, bookmark_name):
#     """Update the folder metadata with the last used bookmark."""
#     folder_meta_path = os.path.join(folder_dir, "folder_meta.json")

#     # Load existing metadata or create new
#     if os.path.exists(folder_meta_path):
#         try:
#             with open(folder_meta_path, 'r') as f:
#                 meta_data = json.load(f)
#         except json.JSONDecodeError:
#             meta_data = {}
#     else:
#         meta_data = {
#             "created_at": datetime.now().isoformat(),
#             "description": "",
#             "tags": []
#         }

#     # Update last used bookmark
#     meta_data["last_used_bookmark"] = bookmark_name
#     meta_data["last_modified"] = datetime.now().isoformat()

#     # Save updated metadata
#     with open(folder_meta_path, 'w') as f:
#         json.dump(meta_data, f, indent=2)
