import os

from app.obs.obs_utils import (
    load_bookmark_into_obs,
    save_obs_media_info_to_bookmark_meta,
    save_obs_screenshot_to_bookmark_path,
)
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.printing_utils import print_color


def handle_bookmark_obs_pre_run(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
) -> int:
    """
    This function is used to handle the pre-run of a bookmark.

    If the bookmark meta does not have all of the video meta information, or the --save-obs flag is set, we will update the metadata. If not, we will pull the metadata and load the state into OBS.
    """

    if current_run_settings_obj["is_no_obs"]:
        return 0

    if not os.path.exists(matched_bookmark_obj["bookmark_path_slash_abs"]):
        print_color(f"❌ Could not create bookmark metadata - bookmark directory doesn't exist: {matched_bookmark_obj['bookmark_path_slash_abs']}", 'red')
        return 1

    is_load_media_info_into_obs  = True
    bookmark_info = matched_bookmark_obj.get("bookmark_info", {})
    if not bookmark_info or not bookmark_info.get("video_filename") or not bookmark_info.get("timestamp"):
        is_load_media_info_into_obs = False

    if is_load_media_info_into_obs:
        # The bookmark that we are using already has the media info, so we can load it into OBS.
        return load_bookmark_into_obs(matched_bookmark_obj)

    # The bookmark that we are using does not have the media info, so we need to save it to the bookmark meta.
    save_obs_screenshot_to_bookmark_path(matched_bookmark_obj, current_run_settings_obj)
    return save_obs_media_info_to_bookmark_meta(matched_bookmark_obj, current_run_settings_obj)
