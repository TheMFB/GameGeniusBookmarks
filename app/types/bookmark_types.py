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
    is_overwrite_redis_after: bool
    is_overwrite_redis_before: bool
    is_save_updates: bool
    is_use_preceding_bookmark: bool
    is_blank_slate: bool
    is_no_docker: bool
    is_no_docker_no_redis: bool
    is_no_obs: bool
    is_show_image: bool
    is_add_bookmark: bool
    cli_nav_arg_string: list[str] | None
    tags: list[str] | None
    nav_from_bookmark: MatchedBookmarkObj | None
