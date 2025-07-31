from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def process_alt_source_bookmark(_matched_bookmark_obj: MatchedBookmarkObj, _current_run_settings_obj: CurrentRunSettings):
    """
    This function is used to process the alt source bookmark.

    It will handle the following:
    - Load the redis_before.json to redis dump directory.
    """
    # source_bookmark_obj = current_run_settings_obj.get("source_bookmark_obj", None)
    # cli_nav_arg_string = current_run_settings_obj.get("cli_nav_arg_string", None)


# ---------------------------------------------------------








    pass
