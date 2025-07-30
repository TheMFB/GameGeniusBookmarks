from app.bookmarks.last_used import save_last_used_bookmark
from app.bookmarks.redis_states.handle_bookmark_post_run_redis_states import (
    handle_bookmark_post_run_redis_states,
)
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.printing_utils import print_color


def handle_matched_bookmark_post_processing(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):
    """
    This function is used to handle the post-processing of a matched bookmark.

    It will handle the following:
    - Copy the redis_after.json to the bookmark's redis_after.json
    - Update the last_used_bookmark.json
    """
    # TODO(MFB): If dry-run, we should not push to redis.

    # Run Redis Post-Processing
    if not handle_bookmark_post_run_redis_states(matched_bookmark_obj, current_run_settings_obj):
        return 1

    # Save the last used bookmark at the end of successful operations
    if matched_bookmark_obj["bookmark_dir_slash_abs"]:
        print_color('saving last used bookmark', 'red')
        # TODO(?): If dry-run, should we not save the last used bookmark?
        save_last_used_bookmark(matched_bookmark_obj)

    return 0
