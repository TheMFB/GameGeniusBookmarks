# import os
# import json
# from app.consts.bookmarks_consts import IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS
# from app.bookmark_dir_processes import find_bookmark_dir_by_name
# from app.bookmarks_print import print_all_live_directories_and_bookmarks
# from app.bookmarks.matching.matching_utils import token_match_bookmarks
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def handle_ls(args):
    # Remove -ls so we can check what came before it
    # TODO(MFB): Redo this.
    return 0
    # args_copy = args.copy()
    # args_copy.remove('-ls') if '-ls' in args_copy else args_copy.remove('--ls')

    # # Detect --json flag
    # is_json = False
    # if '--json' in args_copy:
    #     is_json = True
    #     args_copy.remove('--json')

    # # Detect --show-image flag
    # show_image = False
    # for flag in ['--show-image', '-i']:
    #     if flag in args_copy:
    #         show_image = True
    #         args_copy.remove(flag)


    # # If no folder path is provided: list everything
    # if not args_copy:
    #     print_all_live_directories_and_bookmarks(
    #         is_print_just_current_directory_bookmarks=IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS
    #     )
    #     return 0

    # # If a folder path is provided, list only that folder
    # folder_arg = ' '.join(args_copy).strip()
    # print(f"🔍 Searching for tokens: {folder_arg}")

    # folder_path = find_bookmark_dir_by_name(folder_arg)

    # if folder_path:
    #     from app.bookmarks_print import print_bookmarks_in_directory
    #     print_bookmarks_in_directory(folder_path)
    #     return 0
    # else:
    #     # Fall back to which-style logic
    #     from app.bookmark_dir_processes import get_all_valid_root_dir_names

    #     all_folders = get_all_valid_root_dir_names()
    #     all_matches = []

    #     for folder in all_folders:
    #         matched_paths = token_match_bookmarks(folder_arg, folder)
    #         print(f"📎 Matched in {folder}: {matched_paths}")
    #         for matched_path in matched_paths:
    #             folder_name = os.path.basename(folder)
    #             full_path = f"{folder_name}:{matched_path.replace('/', ':')}"
    #             all_matches.append(full_path)

    #     if is_json:
    #         print(json.dumps(all_matches, indent=2))
    #         return 0 if all_matches else 1
    #     else:
    #         if not all_matches:
    #             print(f"❌ No bookmarks matched '{folder_arg}'")
    #             return 1

    #         if len(all_matches) == 1:
    #             print("✅ Match found:")
    #             print(f"  • {all_matches[0]}")

    #             if show_image:
    #                 from app.utils.printing_utils import print_image
    #                 folder_name, path = all_matches[0].split(":", 1)
    #                 bookmark_dir = os.path.join("obs_bookmark_saves", folder_name, *path.split(":"))
    #                 for ext in ['jpg', 'png']:
    #                     image_path = os.path.join(bookmark_dir, f"screenshot.{ext}")
    #                     if os.path.exists(image_path):
    #                         print_image(image_path)
    #                         break

    #             return 0

    #         print(f"⚠️  Multiple bookmarks matched '{folder_arg}':")
    #         from app.utils.printing_utils import print_image

    #         for m in all_matches:
    #             print(f"  • {m}")
    #             if show_image:
    #                 folder_name, path = m.split(":", 1)
    #                 bookmark_dir = os.path.join("obs_bookmark_saves", folder_name, *path.split(":"))
    #                 for ext in ['jpg', 'png']:
    #                     image_path = os.path.join(bookmark_dir, f"screenshot.{ext}")
    #                     if os.path.exists(image_path):
    #                         print_image(image_path)
    #                         break

    #         print("Please be more specific.")
    #         return 1

# Unused

# @print_def_name(IS_PRINT_DEF_NAME)
# def find_bookmark_dir_by_name(bookmark_dir_arg: str):
#     """Find folder directory by name or full relative path (e.g. kerch/comp/m02)"""
#     # TODO(): ++++ This is not working as expected. We should pull in the all bookmarks json, and attempt to step through the tree, and see if there are any full / partial matches. The all_live_folders is giving a full system path, but only the basename for what we need.

#     # ---- 0 cli_bookmark_dir:
#     # 'videos/0001_green_dog/g01/m01'
#     # ---- 0 directory_name find_bookmark_dir_by_name:
#     # videos/0001_green_dog/g01/m01
#     # ---- 1 folder_path find_bookmark_dir_by_name:
#     # /Users/mfb/dev/MFBTech/GameGeniusProject/GameGenius/game-genius-bookmarks/obs_bookmark_saves/videos
#     # ---- 1 folder_dir find_bookmark_dir_by_name:
#     # None
#     print_color('---- 0 bookmark_dir_abs find_bookmark_dir_by_name:', 'green')
#     print(bookmark_dir_arg)

#     # live_root_dirs_abs = get_all_valid_root_dir_names()
#     # for live_root_dir_abs in live_root_dirs_abs:
#     #     print_color(
#     #         '---- 1 live_root_dir_abs find_bookmark_dir_by_name:', 'magenta')
#     #     print(live_root_dir_abs)

#     #     # Match either exact basename or full relative path from ABS_OBS_BOOKMARKS_DIR
#     #     live_root_dir_name = os.path.relpath(live_root_dir_abs, ABS_OBS_BOOKMARKS_DIR)
#     #     print_color(
#     #         '++++ 2 live_root_dir_name find_bookmark_dir_by_name:', 'magenta')
#     #     print(live_root_dir_name)

#     #     # ✅ Check for exact matches first
#     #     if directory_name == live_root_dir_name or directory_name == rel_path:
#     #         return rel_path

#     #     # ✅ Check for partial matches (e.g., "respawn" should match "respawn-allies")
#     #     if directory_name.lower() in live_root_dir_name.lower():
#     #         return rel_path

#     # return None
#     return bookmark_dir_arg
