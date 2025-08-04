
from app.bookmarks.navigation.find_alt_source_bookmark import (
    find_alt_source_bookmark_match,
)
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj

DEFAULT_ALT_SOURCE_CLI_NAV_STRING = 'previous'


def process_alt_source_bookmark(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
) -> CurrentRunSettings | int:
    """
    This function is used to process the alt source bookmark.
    """

    # Check if the alt source bookmark is being used
    is_use_alt_source_bookmark = current_run_settings_obj.get("is_use_alt_source_bookmark", False)
    if not is_use_alt_source_bookmark:
        return current_run_settings_obj

    # Find the alt source bookmark
    alt_source_bookmark_obj = find_alt_source_bookmark_match(matched_bookmark_obj, current_run_settings_obj)
    if isinstance(alt_source_bookmark_obj, int):
        return alt_source_bookmark_obj

    if not alt_source_bookmark_obj:
        return 1

    current_run_settings_obj["alt_source_bookmark_obj"] = alt_source_bookmark_obj

    return current_run_settings_obj
