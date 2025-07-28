from app.consts.bookmarks_consts import IS_DEBUG
from app.consts.cli_consts import OPTIONS_HELP
from app.flag_handlers import handle_help, handle_ls, handle_which, open_video, find_cli_tags
from app.flag_handlers.preceding_bookmark import find_preceding_bookmark_args
from app.types.bookmark_types import CurrentRunSettings
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

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

default_processed_flags: CurrentRunSettings = {
    "is_overwrite_redis_after": False,
    "is_overwrite_redis_before": False,
    "is_save_updates": False,
    "is_use_preceding_bookmark": False,
    "is_blank_slate": False,
    "is_dry_run": False,
    "is_super_dry_run": False,
    "is_no_obs": False,
    "is_show_image": False,
    "is_add_bookmark": True,
    "cli_nav_arg_string": None,
    "tags": None,
    "nav_from_bookmark": None,
}

@print_def_name(IS_PRINT_DEF_NAME)
def process_flags(args) -> CurrentRunSettings | int:
    """Process command line flags and return a dictionary of flag values."""
    cli_nav_arg_string = None
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

    is_overwrite_redis_after = "--save-last-redis" in args or "-s" in args
    is_save_updates = "--save-updates" in args or "-s" in args
    is_use_preceding_bookmark = "--use-preceding-bookmark" in args or "-p" in args
    is_blank_slate = "--blank-slate" in args or "-b" in args
    is_dry_run = "--dry-run" in args or "-d" in args
    is_super_dry_run = "--super-dry-run" in args or "-sd" in args
    is_no_obs = "--no-obs" in args  # ✅ FIXED this line
    is_show_image = "--show-image" in args
    # is_add_bookmark = "--add" in args or "-a" in args

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
        cli_nav_arg_string = find_preceding_bookmark_args(args)

    # Parse tags from command line
    if "--tags" in args or "-t" in args:
        tags = find_cli_tags(args)

    if IS_DEBUG:
        print(f"🔍 Debug - is_overwrite_redis_after: {is_overwrite_redis_after}")
        print(f"🔍 Debug - is_save_updates: {is_save_updates}")
        print(f"🔍 Debug - is_blank_slate: {is_blank_slate}")
        print(f"🔍 Debug - is_no_obs: {is_no_obs}")

    return {
        **default_processed_flags,
        "is_overwrite_redis_after": is_overwrite_redis_after,
        "is_save_updates": is_save_updates,
        "is_use_preceding_bookmark": is_use_preceding_bookmark,
        "is_blank_slate": is_blank_slate,
        "is_dry_run": is_dry_run,
        "is_super_dry_run": is_super_dry_run,
        "is_no_obs": is_no_obs,
        "is_show_image": is_show_image,
        # "is_add_bookmark": is_add_bookmark,
        "cli_nav_arg_string": cli_nav_arg_string,
        "tags": tags,
    }
