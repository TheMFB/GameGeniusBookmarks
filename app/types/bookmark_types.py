from typing import NotRequired, TypedDict

class BookmarkPathDictionary(TypedDict):
    bookmark_tail_name: str

    # Colon-separated
    bookmark_dir_colon_rel: str
    bookmark_path_colon_rel: str
    # bookmark_dir_colon_abs: str # We never will use a colon-separated absolute path, as colon-syntax is for our internal use.
    # bookmark_path_colon_abs: str # We never will use a colon-separated absolute path, as colon-syntax is for our internal use.

    # Slash-separated
    bookmark_dir_slash_abs: str
    bookmark_dir_slash_rel: str

    bookmark_path_slash_abs: str
    bookmark_path_slash_rel: str


class BookmarkInfo(TypedDict):
    bookmark_name: str
    video_filename: str
    timestamp: float
    timestamp_formatted: str
    tags: list[str]
    created_at: str
    description: NotRequired[str]

class MatchedBookmarkObj(BookmarkPathDictionary):
    bookmark_info: NotRequired[BookmarkInfo]