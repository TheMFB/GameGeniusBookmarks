"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
import os
import sys
import subprocess
from pprint import pprint
# from networkx import to_dict_of_dicts

from app.utils import print_color, convert_bookmark_path
from app.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR, OPTIONS_HELP, IS_PRINT_JUST_CURRENT_FOLDER_BOOKMARKS
from app.bookmarks_folders import get_all_valid_root_dir_names, parse_cli_bookmark_args
from app.bookmarks import get_bookmark_info, save_last_used_bookmark, resolve_navigation_bookmark, get_last_used_bookmark, find_matching_bookmark_strict
from app.bookmarks_print import print_all_folders_and_bookmarks
from app.flag_handlers import handle_help, handle_ls, handle_which, find_preceding_bookmark, open_video, find_tags, handle_matched_bookmark, handle_bookmark_not_found, handle_main_process, handle_redis_operations


# Mapping of known standalone flags to their handler functions
flag_routes = {
    "--help": handle_help,
    "-h": handle_help,
    "--ls": handle_ls,
    "-ls": handle_ls,
    "--which": handle_which,
    "-w": handle_which,
    "--open-video": open_video,
    "-v": open_video,
}


# Define supported flags
supported_flags = [
    "-a",
    "--add",
    "-s",
    "--save-updates",
    "-p",
    "--use-preceding-bookmark",
    "-b",
    "--blank-slate",
    "-d",
    "--dry-run",
    "-sd",
    "--super-dry-run",
    "--no-obs",
    "--save-last-redis",
    "-v",
    "--open-video",
    "-t",
    "--tags",
    "--show-image",
]


def main():
    cli_args_list = None
    matched_bookmark_name = None
    bookmark_tail_name = None
    bookmark_name = None
    bookmark_path_rel = None
    tags = []
    # Parse command line arguments
    args = sys.argv[1:]
    if IS_DEBUG:
        print(f"🔍 Debug - args: {args}")

    # Route simple flags using the flag_routes table
    for flag, handler in flag_routes.items():
        if flag in args:
            return handler(args)

    # Otherwise, we have a bookmark/reserved bookmark name

    args_for_run_bookmarks = args[0]

    # Check if this is a navigation command
    navigation_commands = ["next", "previous", "first", "last"]
    is_navigation = args_for_run_bookmarks in navigation_commands

    # Check for unsupported flags
    ignore_flags = ["--scale"]
    unsupported_flags = [arg for arg in args if arg.startswith(
        "--") and arg not in supported_flags + ignore_flags]
    if unsupported_flags:
        print(f"⚠️  Warning: Unsupported flags detected: {unsupported_flags}")
        print(OPTIONS_HELP)
        print()

    is_save_last_redis = "--save-last-redis" in args or "-s" in args
    is_save_updates = "--save-updates" in args or "-s" in args
    is_use_preceding_bookmark = "--use-preceding-bookmark" in args or "-p" in args
    is_blank_slate = "--blank-slate" in args or "-b" in args
    is_dry_run = "--dry-run" in args or "-d" in args
    is_super_dry_run = "--super-dry-run" in args or "-sd" in args
    is_no_obs = "--no-obs" in args  # ✅ FIXED this line
    is_show_image = "--show-image" in args
    is_add_bookmark = "--add" in args or "-a" in args

    if is_super_dry_run:
        print("💧 SUPER DRY RUN: Will skip Redis operations and Docker commands.")
        print("💧 Still creating/updating bookmarks and metadata.")
        if IS_DEBUG:
            print(f"🔍 Debug - is_super_dry_run: {is_super_dry_run}")
    if is_dry_run and IS_DEBUG:

        print(f"🔍 Debug - is_dry_run: {is_dry_run}")
        # TODO(MFB): Print what this does (different f)

    # Parse the source bookmark for --use-preceding-bookmark if specified

    if is_use_preceding_bookmark:
        cli_args_list = find_preceding_bookmark(args)

    # Parse tags from command line
    if "--tags" in args or "-t" in args:
        tags = find_tags(args)

    if IS_DEBUG:
        print(f"🔍 Debug - is_save_last_redis: {is_save_last_redis}")
        print(f"🔍 Debug - is_save_updates: {is_save_updates}")
        print(f"🔍 Debug - is_blank_slate: {is_blank_slate}")
        print(f"🔍 Debug - is_no_obs: {is_no_obs}")

    # Parse folder:bookmark format if present (only if not navigation)
    # TODO(MFB): Globally change these back to bookmark_name
    cli_bookmark_dir, bookmark_tail_name = parse_cli_bookmark_args(
        args_for_run_bookmarks)
    print_color('---- parse_cli_bookmark_args cli_bookmark_dir:', 'cyan')
    pprint(cli_bookmark_dir)
    print_color('---- parse_cli_bookmark_args bookmark_tail_name:', 'cyan')
    pprint(bookmark_tail_name)
    print('')


    # Handle navigation commands
    if is_navigation:
        # TODO(MFB): Need to check Navigation commands here.
        print_color('---- is_navigation ----', 'magenta')
        # Get the last used bookmark to determine the folder
        last_used_info = get_last_used_bookmark()
        if not last_used_info:
            print(
                f"❌ No last used bookmark found. Cannot navigate with '{args_for_run_bookmarks}'")
            return 1

        folder_name = last_used_info.get("rel_bookmark_dir")

        # Find the folder directory
        folder_dir = None
        valid_root_dir_names = get_all_valid_root_dir_names()
        for folder_path in valid_root_dir_names:
            # TODO(MFB): This is where we need to look for our navigation bugfix.
            if os.path.basename(folder_path) == folder_name:
                folder_dir = folder_path
                break

        if not folder_dir:
            print(f"❌ Could not find folder directory for '{folder_name}'")
            return 1

        # Resolve the navigation command
        matched_bookmark_path_rel, bookmark_info = resolve_navigation_bookmark(
            args_for_run_bookmarks, folder_dir)
        print('+++++ ? resolve_navigation_bookmark matched_bookmark_path_rel:')
        pprint(matched_bookmark_path_rel)

        if not matched_bookmark_path_rel:
            print(
                f"❌ No bookmark name found for'{matched_bookmark_path_rel}' '{args_for_run_bookmarks}'")
            return 1


    else:
        print_color('---- not navigation ----', 'magenta')
        # TODO(MFB): GOOD TO HERE ==================================================

        # Normal bookmark lookup
        matched_bookmark_path_rel, bookmark_info = get_bookmark_info(
            bookmark_tail_name)
        print('+++++ get_bookmark_info matched_bookmark_path_rel:')
        pprint(matched_bookmark_path_rel)

    if IS_DEBUG:
        print(
            f"🎯 Starting integrated runonce-redis workflow for bookmark: '{matched_bookmark_path_rel}'")
        print(f"🔧 Redis dump directory: {REDIS_DUMP_DIR}")
        if is_save_last_redis:
            print(f"💾 Mode: Save current Redis state as redis_after.json")
        if is_save_updates:
            print(f"💾 Mode: Save redis state updates (before and after)")
        if is_use_preceding_bookmark:
            print(
                f"📋 Mode: Use preceding bookmark's redis_after.json as redis_before.json")
        if is_blank_slate:
            print(f"🆕 Mode: Use initial blank slate Redis state")
        if is_dry_run:
            print(f"📖 Mode: Load bookmark only (no main process)")
        if is_super_dry_run:
            print(f"💾 Super dry run mode: Skipping all OBS operations")
        if is_no_obs:
            print(f"📷 No-OBS mode: Skipping all OBS operations")

    # Ensure Redis dump directory exists
    if not os.path.exists(REDIS_DUMP_DIR):
        print(f"❌ Redis dump directory does not exist: {REDIS_DUMP_DIR}")
        return 1

    # Check if bookmark exists (with fuzzy matching)
    # This check is now redundant if we are resolving a navigation command
    # if not is_add_bookmark and not matched_bookmark_name:
    #     print(f"❌ Bookmark '{args_for_run_bookmarks}' not found. Use -a or --add to create it.")
    #     return 1
    # If the bookmark exists, continue as normal (do not return early)

    # Check for exact bookmark path match
    if is_add_bookmark and cli_bookmark_dir:
        print_color('---- is_add_bookmark and cli_bookmark_dir ----', 'magenta')
        folder_path = os.path.join("obs_bookmark_saves", cli_bookmark_dir)
        existing_path = find_matching_bookmark_strict(
            bookmark_tail_name, folder_path)
        print_color('---- bookmark_tail_name:', 'red')
        pprint(bookmark_tail_name)
        if existing_path:
            print(f"⚠️ Bookmark already exists: {existing_path}")
            print("What would you like to do?")
            print("  1. Load existing")
            print("  2. Overwrite before redis")
            print("  3. Overwrite after redis")
            print("  4. Overwrite both")
            print("  5. Cancel")
            while True:
                choice = input("Enter choice (1–5): ").strip()
                if choice == "1":
                    matched_bookmark_name = existing_path
                    bookmark_info = get_bookmark_info(
                        f"{cli_bookmark_dir}:{bookmark_tail_name}")[1]
                    break
                elif choice == "2":
                    matched_bookmark_name = existing_path
                    overwrite_redis_after = False
                    break
                elif choice == "3":
                    matched_bookmark_name = existing_path
                    overwrite_redis_after = True
                    break
                elif choice == "4":
                    matched_bookmark_name = existing_path
                    overwrite_redis_after = True  # will handle both below
                    break
                elif choice == "5":
                    print("❌ Cancelled.")
                    return 1
                else:
                    print("❌ Invalid choice. Please enter 1–5.")

    # Main workflow: Load existing bookmark OR create new one
    folder_dir = None

    if matched_bookmark_name:
        print_color('---- matched_bookmark_name:', 'magenta')
        pprint(matched_bookmark_name)

        result = handle_matched_bookmark(
            matched_bookmark_name,
            bookmark_info,
            is_show_image,
            is_no_obs,
            is_super_dry_run,
            is_blank_slate,
            is_use_preceding_bookmark,
            is_save_updates,
            is_save_last_redis,
            tags,
            cli_args_list
        )
        if isinstance(result, int):
            print("❌ Error in handle_matched_bookmark")
            return result  # an error code like 1 was returned
        folder_dir, bookmark_name = result

        print('+++++ handle_matched_bookmark folder_dir:')
        pprint(folder_dir)

        # ✅ Final confirmation for matched bookmarks
        relative_path = os.path.relpath(os.path.join(
            folder_dir, bookmark_name), folder_dir)
        normalized_path = relative_path.replace('/', ':')
        folder_name = os.path.basename(folder_dir)
        print(f"✅ Match found: {folder_name}:{normalized_path}")

    else:
        print_color('---- no matched_bookmark_name ----', 'magenta')
        print_color('---- cli_bookmark_dir:', 'cyan')
        pprint(cli_bookmark_dir)
        print('')

        # If we matched a folder path (e.g. from fuzzy match), split it

        if ':' in cli_bookmark_dir:
            parts = cli_bookmark_dir.split(':')
            cli_bookmark_dir = '/'.join(parts)
            bookmark_tail_name = bookmark_name
        else:
            # fallback (user gave folder manually or it's blank)
            bookmark_tail_name = bookmark_name

        rel_bookmark_dir, bookmark_tail_name, bookmark_path_rel = convert_bookmark_path(cli_bookmark_dir, bookmark_tail_name)

        # Bookmark does not exist, and user intends to create it
        folder_dir = handle_bookmark_not_found(
            bookmark_tail_name,
            cli_bookmark_dir,
            is_super_dry_run,
            is_blank_slate,
            is_use_preceding_bookmark,
            is_save_updates,
            is_no_obs,
            tags,
            cli_args_list
        )

        print('+++++ handle_bookmark_not_found folder_dir:')
        pprint(folder_dir)

        if folder_dir == 1 or folder_dir == 0:
            print(f"❌ Error in handle_bookmark_not_found")
            return folder_dir

    # Run the main process (unless dry run modes)
    if not is_dry_run and not is_super_dry_run:
        print("🚀 Running main process...")
        result = handle_main_process()
        if result != 0:
            print("❌ Main process failed")
            return result

    # Check if redis_after.json already exists before saving final state (skip in dry run modes)
    should_save_redis_after = False
    if not is_dry_run and not is_super_dry_run:
        should_save_redis_after = handle_redis_operations(
            folder_dir, bookmark_tail_name, is_save_updates
        )
    else:
        if is_super_dry_run:
            print(f"💾 Super dry run mode: Skipping final Redis state save")
        else:
            print(f"📖 Load-only mode: Skipping final Redis state save")

    # Save the last used bookmark at the end of successful operations
    if folder_dir:
        print_color('---- folder_dir:', 'red')
        pprint(folder_dir)
        folder_name = os.path.basename(folder_dir)
        save_last_used_bookmark(folder_name, bookmark_name, bookmark_info)
        if IS_DEBUG:
            print(
                f"📋 Saved last used bookmark: '{folder_name}:{bookmark_name}'")

        # Handle --preview flag
    if '--preview' in args or '-pv' in args:
        import platform

        screenshot_path = os.path.join(
            folder_dir, bookmark_name, "screenshot.jpg")
        if os.path.exists(screenshot_path):
            print(f"🖼️ Previewing screenshot: {screenshot_path}")
            if platform.system() == "Darwin":
                subprocess.run(["open", screenshot_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", screenshot_path])
            # elif platform.system() == "Windows":
            #     os.startfile(screenshot_path)
            else:
                print(f"⚠️ Preview not supported on this platform.")
            return 0
        else:
            print(f"❌ No screenshot.jpg found for bookmark '{bookmark_name}'")
            return 1

    # Don't update folder metadata at the end - only update when actually creating new folders
    if IS_DEBUG and folder_dir:
        folder_name = os.path.basename(folder_dir)
        print(f"📋 Skipping final folder metadata update for '{folder_name}'")

    if is_super_dry_run:
        print(f"✅ Super dry run workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_name}'")
            print(f"   OBS bookmark loaded")
            print(f"   No Redis operations performed")
    elif is_dry_run:
        print(f"✅ Load-only workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_name}'")
            print(f"   OBS bookmark loaded")
            print(f"   Redis before: {bookmark_name}/redis_before.json")
    elif is_no_obs:
        print(f"✅ No-OBS workflow completed successfully!")
        if IS_DEBUG:
            print(f"   Bookmark: '{bookmark_name}'")
            print(f"   No OBS operations performed")
            print(f"   No Redis operations performed")
    else:
        if IS_DEBUG:
            print(f"✅ Integrated workflow completed successfully!")
            print(f"   Bookmark: '{bookmark_name}'")
            print(f"   OBS screenshot: {bookmark_name}/screenshot.jpg")
            print(f"   Redis before: {bookmark_name}/redis_before.json")
            if should_save_redis_after:
                print(
                    f"   Redis after: {bookmark_name}/redis_after.json (new)")
            else:
                print(
                    f"   Redis after: {bookmark_name}/redis_after.json (existing)")
    print('=' * 60)
    print('')

    # Print all folders and bookmarks with current one highlighted
    if folder_dir:
        print_all_folders_and_bookmarks(
            current_folder_abs_path=folder_dir,
            current_bookmark_name=bookmark_name,
            current_bookmark_info=bookmark_info,
            is_print_just_current_folder_bookmarks=IS_PRINT_JUST_CURRENT_FOLDER_BOOKMARKS
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
