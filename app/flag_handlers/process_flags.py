import os
import sys
import subprocess
from pprint import pprint
# from networkx import to_dict_of_dicts

from app.utils import print_color, convert_bookmark_path
from app.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR, OPTIONS_HELP, IS_PRINT_JUST_CURRENT_FOLDER_BOOKMARKS
from app.bookmarks_folders import get_all_valid_root_dir_names, parse_cli_bookmark_args
from app.bookmarks import get_bookmark_info, save_last_used_bookmark, resolve_navigation_bookmark, get_last_used_bookmark, find_matching_bookmarks_strict
from app.bookmarks_print import print_all_folders_and_bookmarks
from app.flag_handlers import handle_help, handle_ls, handle_which, find_preceding_bookmark, open_video, find_tags, handle_matched_bookmark, handle_bookmark_not_found, handle_main_process, handle_redis_operations
# Mapping of known standalone flags to their handler functions
from typing_extensions import TypedDict, NotRequired, Literal


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


class ProcessedFlags(TypedDict):
    is_save_last_redis: bool
    is_save_updates: bool
    is_use_preceding_bookmark: bool
    is_blank_slate: bool
    is_dry_run: bool
    is_super_dry_run: bool
    is_no_obs: bool
    is_show_image: bool
    is_add_bookmark: bool
    cli_args_list: list[str] | None
    tags: list[str] | None

def process_flags(args) -> ProcessedFlags | int:
    """Process command line flags and return a dictionary of flag values."""
    cli_args_list = None
    tags = []

    # Handle all flags that terminate the program afterwards (routed flags)
    for flag, handler in flag_routes.items():
        if flag in args:
            handler(args)
            return 0


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

    return {
        "is_save_last_redis": is_save_last_redis,
        "is_save_updates": is_save_updates,
        "is_use_preceding_bookmark": is_use_preceding_bookmark,
        "is_blank_slate": is_blank_slate,
        "is_dry_run": is_dry_run,
        "is_super_dry_run": is_super_dry_run,
        "is_no_obs": is_no_obs,
        "is_show_image": is_show_image,
        "is_add_bookmark": is_add_bookmark,
        "cli_args_list": cli_args_list,
        "tags": tags,
    }
