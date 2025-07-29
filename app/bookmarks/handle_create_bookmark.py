import os
from app.types.bookmark_types import MatchedBookmarkObj
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
    bookmark_dir_slash_rel = cli_bookmark_obj["bookmark_dir_slash_rel"]

    os.makedirs(bookmark_dir_slash_abs, exist_ok=True)

    # CREATE DIRECTORY METADATA #

    # Create directory metadata for nested bookmarks
    path_parts = bookmark_dir_slash_rel.split('/')
    current_path = ABS_OBS_BOOKMARKS_DIR
    for i, dir_name in enumerate(path_parts[:-1]): # Take all but the last part (the bookmark name itself)
        current_path = os.path.join(current_path, dir_name)

        # TODO(KERCH): We would add in here the description and tags for when we have the -t# flags. https://app.clickup.com/t/86aaat28f

        # Create directory metadata if it doesn't exist
        create_directory_meta(current_path, description="", tags=None)
        if IS_DEBUG:
            print(f"📋 Created directory metadata for: {dir_name}")

    # CREATE BOOKMARK METADATA #
    # TODO(?): Debug -- We are updating the metadata for OBS during matched bookmark...
    create_bookmark_meta(
        cli_bookmark_obj,
        {},
        current_run_settings_obj["tags"],
    )

    return cli_bookmark_obj
