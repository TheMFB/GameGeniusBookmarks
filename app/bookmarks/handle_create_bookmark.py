import os
# from app.flag_handlers.save_current_redis_to_bm_before_json import save_current_redis_to_bm_before_json
from app.types.bookmark_types import MatchedBookmarkObj
from app.flag_handlers.save_obs_screenshot import save_obs_screenshot
from app.utils.obs_utils import get_media_source_info
from app.utils.bookmark_utils import convert_exact_bookmark_path_to_dict
from app.utils.decorators import print_def_name
from app.utils.printing_utils import *
from app.consts.bookmarks_consts import IS_DEBUG, ABS_OBS_BOOKMARKS_DIR
from app.bookmarks_meta import create_bookmark_meta, create_directory_meta
from app.types.bookmark_types import CurrentRunSettings

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_create_bookmark_and_parent_dirs(
    cli_bookmark_string: str,
    current_run_settings_obj: CurrentRunSettings,
) -> MatchedBookmarkObj | int | None:
    # Create bookmark directory
    cli_bookmark_obj = convert_exact_bookmark_path_to_dict(
        cli_bookmark_string)
    bookmark_dir_slash_abs = cli_bookmark_obj["bookmark_dir_slash_abs"]
    bookmark_path_slash_abs = cli_bookmark_obj["bookmark_path_slash_abs"]
    bookmark_path_colon_rel = cli_bookmark_obj["bookmark_path_colon_rel"]
    bookmark_dir_slash_rel = cli_bookmark_obj["bookmark_dir_slash_rel"]
    cli_bookmark_tail_name = cli_bookmark_obj["bookmark_tail_name"]


    # if not current_run_settings_obj["is_super_dry_run"]:
    #     save_current_redis_to_bm_before_json(bookmark_path_slash_abs)

    os.makedirs(bookmark_dir_slash_abs, exist_ok=True)

    # Get media source info and create bookmark metadata
    if current_run_settings_obj["is_no_obs"]:
        # Create minimal metadata without OBS info
        media_info = {
            'file_path': '',
            'video_filename': '',
            'timestamp': 0,
            'timestamp_formatted': '00:00:00'
        }

        print(
            f"📋 Created minimal bookmark metadata (no OBS info) with tags: {current_run_settings_obj["tags"]}")
        print(f"📷 No-OBS mode: Skipping screenshot capture")

    else:
        media_info = get_media_source_info()
        if media_info:
            save_obs_screenshot(bookmark_path_slash_abs, is_overwrite=current_run_settings_obj["is_save_updates"])

            print(
                f"📋 Created bookmark metadata with tags: {current_run_settings_obj["tags"]}")

            print(
                f"✅ Created new bookmark:{bookmark_path_colon_rel}")

    # CREATE DIRECTORY METADATA #

    # Create folder metadata for nested bookmarks
    path_parts = bookmark_dir_slash_rel.split('/')
    current_path = ABS_OBS_BOOKMARKS_DIR
    for i, dir_name in enumerate(path_parts[:-1]): # Take all but the last part (the bookmark name itself)
        current_path = os.path.join(current_path, dir_name)

        # TODO(KERCH): We would add in here the description and tags for when we have the -t# flags.
        # Create folder metadata if it doesn't exist
        create_directory_meta(current_path, description="", tags=None)
        if IS_DEBUG:
            print(f"📋 Created directory metadata for: {dir_name}")

    # CREATE BOOKMARK METADATA #

    create_bookmark_meta(
        bookmark_path_slash_abs,
        cli_bookmark_tail_name,
        media_info,
        current_run_settings_obj["tags"],
        is_patch_updates=False,
        is_overwrite=False,
    )

    return cli_bookmark_obj
