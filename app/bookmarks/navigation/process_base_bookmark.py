from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def process_base_bookmark(matched_bookmark_obj: MatchedBookmarkObj, current_run_settings_obj: CurrentRunSettings):
    """
    This function is used to process the base bookmark.

    It will handle the following:
    - Load the redis_before.json to redis dump directory.
    """
    base_bookmark_obj = current_run_settings_obj.get("base_bookmark_obj", None)
    cli_nav_arg_string = current_run_settings_obj.get("cli_nav_arg_string", None)






    pass