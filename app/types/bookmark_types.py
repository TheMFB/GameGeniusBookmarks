from typing import Literal, NotRequired, TypedDict


class BookmarkPathDictionary(TypedDict):
    bookmark_tail_name: str

    # Colon-separated
    bookmark_dir_colon_rel: str  # grand-parent:parent
    bookmark_path_colon_rel: str  # grand-parent:parent:01
    # Note that we will never colon-separate absolute paths, as colon-syntax is for our internal use.

    # Slash-separated
    bookmark_dir_slash_abs: (
        str  # /Users/mfb/Desktop/obs_bookmark_saves/grand-parent/parent
    )
    bookmark_dir_slash_rel: str  # grand-parent/parent

    bookmark_path_slash_abs: (
        str  # /Users/mfb/Desktop/obs_bookmark_saves/grand-parent/parent/01
    )
    bookmark_path_slash_rel: str  # grand-parent/parent/01


class BookmarkInfo(TypedDict):
    bookmark_tail_name: str
    video_filename: str
    timestamp: float
    timestamp_formatted: str
    tags: list[str]
    auto_tags: NotRequired[list[str]]
    created_at: str
    description: NotRequired[str]


class MatchedBookmarkObj(BookmarkPathDictionary):
    bookmark_info: NotRequired[BookmarkInfo]


class CurrentRunSettings(TypedDict):
    alt_source_bookmark_obj: MatchedBookmarkObj | None
    alt_source_cli_nav_string: str | None
    current_bookmark_obj: MatchedBookmarkObj | None
    is_add_bookmark: bool
    is_blank_slate: bool
    is_no_docker: bool
    is_no_docker_no_redis: bool
    is_no_obs: bool
    is_no_saving_dry_run: bool
    is_save_bm_redis_after: bool
    is_reset_bm_redis_before: bool
    is_save_obs: bool
    is_save_updates: bool
    is_show_image: bool
    is_use_alt_source_bookmark: bool
    is_update_obs: bool
    tags: list[str] | None


class MediaInfo(TypedDict):
    file_path: str
    video_filename: str
    timestamp: float
    timestamp_formatted: str


# CLI FLAGS #

ValidRoutedFlags = Literal[
    "--help", "-h", "--ls", "-ls", "--which", "-w", "--open-video", "-v", "--pwd"
]

VALID_FLAGS = [
    # TODO(MFB): See if we aren't using some of these...
    "--add-bookmark",
    "--after",
    "--before",
    "--blank-slate",
    "--bookmark-alt-source",
    "--both",
    "--dry-run",
    "--no-docker",
    "--no-docker-no-redis",
    "--no-obs",
    "--no-saving",
    "--reset",
    # "--save-last-redis",
    "--save-obs",
    "--save-redis-after",
    "--save-redis-before",
    "--save-updates",
    "--show-image",
    "--tags",
    "--update-all",
    "--update-obs",
    "--update-redis-after",
    "--update-redis-before",
    "--use-preceding-bookmark",
    "-a",
    "-b",
    "-d",
    "-nd",
    "-ndnr",
    "-ndr",
    "-ns",
    "-p",
    "-r",
    "-s",
    "-sboth",
    "-so",
    "-t",
    "-u",
    "-uo",
    "--pwd",
]

default_processed_flags: CurrentRunSettings = {
    "alt_source_bookmark_obj": None,
    "alt_source_cli_nav_string": None,
    "current_bookmark_obj": None,
    "is_add_bookmark": True,
    "is_blank_slate": False,
    "is_no_docker": False,
    "is_no_docker_no_redis": False,
    "is_no_obs": False,
    "is_no_saving_dry_run": False,
    "is_save_bm_redis_after": False,
    "is_reset_bm_redis_before": False,
    "is_save_obs": False,
    "is_save_updates": False,
    "is_show_image": False,
    "is_use_alt_source_bookmark": False,
    "is_update_obs": False,
    "tags": None,
}

NAVIGATION_COMMANDS = [
    "next",
    "previous",
    "first",
    "last",
    "last_used",
    "current",
    "again",
]
NavigationCommand = Literal[
    "next", "previous", "first", "last", "last_used", "current", "again"
]
