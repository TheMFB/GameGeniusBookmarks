import os
import sys
import subprocess
import traceback
from app.bookmarks.redis_states import handle_copy_temp_redis_to_bm_redis_after
from app.utils.printing_utils import *
from app.consts.bookmarks_consts import IS_DEBUG, IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS
from app.bookmarks_print import print_all_live_directories_and_bookmarks
from app.flag_handlers import handle_main_process, process_flags, CurrentRunSettings
from app.types import MatchedBookmarkObj
from app.bookmarks.matching.bookmark_matching import find_best_bookmark_match_or_create
from app.bookmarks.last_used import save_last_used_bookmark


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

    # Save the last used bookmark at the end of successful operations
    if matched_bookmark_obj["bookmark_dir_slash_abs"]:
        print_color('saving last used bookmark', 'red')
        save_last_used_bookmark(matched_bookmark_obj)
