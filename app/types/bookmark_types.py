from typing import NotRequired, TypedDict


class BookmarkPathDictionary(TypedDict):
    bookmark_tail_name: str

    # Colon-separated
    bookmark_dir_colon_rel: str  # grand-parent:parent
    bookmark_path_colon_rel: str # grand-parent:parent:01
    # Note that we will never colon-separate absolute paths, as colon-syntax is for our internal use.

    # Slash-separated
    bookmark_dir_slash_abs: str # /Users/mfb/Desktop/obs_bookmark_saves/grand-parent/parent
    bookmark_dir_slash_rel: str # grand-parent/parent

    bookmark_path_slash_abs: str # /Users/mfb/Desktop/obs_bookmark_saves/grand-parent/parent/01
    bookmark_path_slash_rel: str # grand-parent/parent/01


class BookmarkInfo(TypedDict):
    bookmark_tail_name: str
    video_filename: str
    timestamp: float
    timestamp_formatted: str
    tags: list[str]
    created_at: str
    description: NotRequired[str]

class MatchedBookmarkObj(BookmarkPathDictionary):
    bookmark_info: NotRequired[BookmarkInfo]

class CurrentRunSettings(TypedDict):
    base_bookmark_obj: MatchedBookmarkObj | None
    cli_nav_arg_string: list[str] | None
    is_add_bookmark: bool
    is_blank_slate: bool
    is_no_docker: bool
    is_no_docker_no_redis: bool
    is_no_obs: bool
    is_no_saving_dry_run: bool
    is_overwrite_redis_after: bool
    is_overwrite_redis_before: bool
    is_save_updates: bool
    is_show_image: bool
    is_use_bookmark_as_base: bool
    tags: list[str] | None


# CLI FLAGS #

VALID_FLAGS = [
    "-a",
    "--add",
    "-s",
    "--save-updates",
    "-p",
    "--use-preceding-bookmark",
    "--bookmark-base",
    "-b",
    "--blank-slate",
    "-d",
    "--dry-run",
    "-sd",
    "-nd",
    "--super-dry-run",
    "-ndr",
    "-ndnr",
    "--no-obs",
    "--save-last-redis",
    "-v",
    "--open-video",
    "-t",
    "--tags",
    "--show-image",
    "--no-saving",
    "-ns"
]

default_processed_flags: CurrentRunSettings = {
    "base_bookmark_obj": None,
    "cli_nav_arg_string": None,
    "is_add_bookmark": True,
    "is_blank_slate": False,
    "is_no_docker": False,
    "is_no_docker_no_redis": False,
    "is_no_obs": False,
    "is_no_saving_dry_run": False,
    "is_overwrite_redis_after": False,
    "is_overwrite_redis_before": False,
    "is_save_updates": False,
    "is_show_image": False,
    "is_use_bookmark_as_base": False,
    "tags": None,
}

NAVIGATION_COMMANDS = ["next", "previous", "first", "last", "last_used"]
