from typing import Callable, cast

from app.bookmarks.navigation.find_alt_source_bookmark import (
    find_alt_source_bookmark_match,
)
from app.consts.bookmarks_consts import IS_DEBUG
from app.consts.cli_consts import OPTIONS_HELP
from app.flag_handlers.help import handle_help
from app.flag_handlers.ls import handle_ls
from app.flag_handlers.open_video import open_video
from app.flag_handlers.which import handle_which
from app.tags.find_cli_tags import find_cli_tags
from app.types.bookmark_types import (
    VALID_FLAGS,
    CurrentRunSettings,
    ValidRoutedFlags,
    default_processed_flags,
)
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

flag_route_handler_map: dict[ValidRoutedFlags, Callable] = {
    "--help": handle_help,
    "-h": handle_help,
    "--ls": handle_ls,
    "-ls": handle_ls,
    "--which": handle_which,
    "-w": handle_which,
    "--open-video": open_video,
    "-v": open_video,
}


@print_def_name(IS_PRINT_DEF_NAME)
def process_flags(args) -> CurrentRunSettings | int:
    """Process command line flags and return a dictionary of flag values."""
    cli_nav_arg_string = None
    source_bookmark_obj = None
    tags = []

    # Handle all flags that terminate the program afterwards (routed flags)
    # for flag, handler in flag_route_handler_map.items():
    for flag, handler in flag_route_handler_map.items():
        if flag in args:
            handler(args)
            return 0

    # Check for unsupported flags
    unsupported_flags = [arg for arg in args if arg.startswith(
        "--") or arg.startswith("-") and arg not in VALID_FLAGS]
    if unsupported_flags:
        print(f"⚠️  Warning: Unsupported flags detected: {unsupported_flags}")
        print(OPTIONS_HELP)
        print()

    def is_flag_in_args(flags):
        return any(flag in args for flag in flags)

    # TODO(MFB): Clean this up.
    is_overwrite_bm_redis_after = is_flag_in_args([
        "--save-last-redis",
        "-s"
    ])
    is_save_updates = is_flag_in_args([
        "--save-updates",
        "-s"
    ])
    # TODO(MFB): --continue
    is_use_alt_source_bookmark = is_flag_in_args([
        "--use-preceding-bookmark",
        "-p",
        "--bookmark-alt-source",
        "-bs"
    ])
    is_blank_slate = is_flag_in_args([
        "--blank-slate",
        "-b"
    ])
    is_no_saving_dry_run = is_flag_in_args([
        "--dry-run",
        "-d",
        "--no-saving",
        "-ns"
    ])
    is_no_docker = is_flag_in_args([
        "--no-docker",
        "-nd"
    ])
    is_no_docker_no_redis = is_flag_in_args([
        "--no-docker-no-redis",
        "-ndr",
        "-ndnr"
    ])
    is_no_obs = is_flag_in_args([
        "--no-obs"
    ])
    is_show_image = is_flag_in_args([
        "--show-image"
    ])
    # is_add_bookmark = "--add" in args or "-a" in args

    if is_no_docker_no_redis:
        print("💧 NO DOCKER NO REDIS: Will skip Redis operations and Docker commands.")
        print("💧 Still creating/updating bookmarks and metadata.")
        if IS_DEBUG:
            print(f"🔍 Debug - is_no_docker_no_redis: {is_no_docker_no_redis}")
    if is_no_docker and IS_DEBUG:

        print(f"🔍 Debug - is_no_docker: {is_no_docker}")
        # TODO(MFB): Print what this does (different f)

    # Parse the alt source bookmark for --use-preceding-bookmark if specified
    if is_use_alt_source_bookmark:
        source_match_results = find_alt_source_bookmark_match(args)
        if isinstance(source_match_results, int):
            print(f"❌ find_alt_source_bookmark_match Error: {source_match_results}")
            return source_match_results
        if isinstance(source_match_results, str):
            cli_nav_arg_string = source_match_results
        source_bookmark_obj = source_match_results


    # Parse tags from command line
    if "--tags" in args or "-t" in args:
        tags = find_cli_tags(args)

    if IS_DEBUG:
        print(
            f"🔍 Debug - is_overwrite_bm_redis_after: {is_overwrite_bm_redis_after}")
        print(f"🔍 Debug - is_save_updates: {is_save_updates}")
        print(f"🔍 Debug - is_blank_slate: {is_blank_slate}")
        print(f"🔍 Debug - is_no_obs: {is_no_obs}")

    return cast(CurrentRunSettings, {
        **default_processed_flags,
        "source_bookmark_obj": source_bookmark_obj,
        "cli_nav_arg_string": cli_nav_arg_string,
        # "is_add_bookmark": is_add_bookmark,
        "is_blank_slate": is_blank_slate,
        "is_no_docker": is_no_docker,
        "is_no_docker_no_redis": is_no_docker_no_redis,
        "is_no_obs": is_no_obs,
        "is_no_saving_dry_run": is_no_saving_dry_run,
        "is_overwrite_bm_redis_after": is_overwrite_bm_redis_after,
        # "is_overwrite_bm_redis_before": is_overwrite_bm_redis_before,
        "is_save_updates": is_save_updates,
        "is_show_image": is_show_image,
        "is_use_alt_source_bookmark": is_use_alt_source_bookmark,
        "tags": tags,
    })
