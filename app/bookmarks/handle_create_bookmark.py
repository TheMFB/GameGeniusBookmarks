import os

from app.bookmarks.bookmarks_meta import create_bookmark_meta, create_directory_meta
from app.consts.bookmarks_consts import ABS_OBS_BOOKMARKS_DIR, IS_DEBUG
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.bookmark_utils import convert_exact_bookmark_path_to_bm_obj
from app.utils.decorators import print_def_name
from app.utils.printing_utils import pprint, print_dev

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_create_bookmark_and_parent_dirs(
    cli_bookmark_string: str,
    current_run_settings_obj: CurrentRunSettings,
) -> MatchedBookmarkObj | int | None:
    """
    This function creates the bookmark directory and its parent directories, and creates the bookmark and directory metadata.
    
    """
    # Create bookmark directory
    cli_bookmark_obj = convert_exact_bookmark_path_to_bm_obj(
        cli_bookmark_string)
    bookmark_dir_slash_abs = cli_bookmark_obj["bookmark_dir_slash_abs"]
    bookmark_dir_slash_rel = cli_bookmark_obj["bookmark_dir_slash_rel"]
    bookmark_path_slash_abs = cli_bookmark_obj["bookmark_path_slash_abs"]

    if not current_run_settings_obj["is_no_saving_dry_run"]:
        os.makedirs(bookmark_dir_slash_abs, exist_ok=True)

        # CREATE DIRECTORY METADATA #

        # Create directory metadata for nested bookmarks
        path_parts = bookmark_dir_slash_rel.split('/')
        current_path = ABS_OBS_BOOKMARKS_DIR
        for _i, dir_name in enumerate(path_parts[:-1]): # Take all but the last part (the bookmark name itself)
            current_path = os.path.join(current_path, dir_name)

            # TODO(KERCH): We would add in here the description and tags for when we have the -t# flags. https://app.clickup.com/t/86aaat28f

            # Create directory metadata if it doesn't exist
            create_directory_meta(current_path, description="", tags=None)
            if IS_DEBUG:
                print(f"📋 Created directory metadata for: {dir_name}")

        print_dev('===== CREATE BOOKMARK METADATA:', 'magenta')

        # CREATE BOOKMARK FOLDER #
        os.makedirs(bookmark_path_slash_abs, exist_ok=True)

        # CREATE BOOKMARK METADATA #
        create_bookmark_meta(
            cli_bookmark_obj,
            {},
            current_run_settings_obj["tags"],
        )
    else:
        print("💧 DRY RUN: Skipping bookmark metadata creation")
        print('💧 DRY RUN: Would have created bookmark metadata for:')
        pprint(cli_bookmark_obj)

    return cli_bookmark_obj
