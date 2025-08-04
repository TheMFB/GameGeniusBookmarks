# import os
# import shutil
# from typing import Literal

# from app.bookmarks.redis_states.redis_friendly_converter import (
#     convert_redis_state_file_to_friendly_and_save,
# )
# from app.consts.bookmarks_consts import IS_DEBUG, REDIS_DUMP_DIR
# from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
# from app.utils.decorators import print_def_name

# IS_PRINT_DEF_NAME = True

# @print_def_name(IS_PRINT_DEF_NAME)
# def handle_copy_bookmark_redis_state_from_dump(
#     matched_bookmark_obj: MatchedBookmarkObj,
#     current_run_settings_obj: CurrentRunSettings,
#     bookmark_redis_state_type: Literal["before", "after"],
#     redis_temp_state_filename: Literal["bookmark_temp", "bookmark_temp_after"]
# ):
#     """
#     Handles copying the saved temp redis state (bookmark_temp or bookmark_temp_after) to redis_after.json or redis_before.json
#     Returns: True if redis_after was saved, False otherwise
#     """
#     bookmark_dir_slash_abs = matched_bookmark_obj["bookmark_dir_slash_abs"]
#     bookmark_path_slash_abs = matched_bookmark_obj["bookmark_path_slash_abs"]

#     bookmark_redis_state_filename = "redis_" + bookmark_redis_state_type + ".json"
#     bookmark_redis_state_path = os.path.join(bookmark_path_slash_abs, bookmark_redis_state_filename)

#     redis_temp_state_filename_json = redis_temp_state_filename + ".json"
#     redis_dump_state_path = os.path.join(REDIS_DUMP_DIR, redis_temp_state_filename_json)

#     # Make sure the source file exists
#     if not os.path.exists(redis_dump_state_path):
#         print(f"❌ Redis dump state file does not exist: {redis_dump_state_path}")
#         return False

#     # Make sure the bookmark directory exists
#     if not os.path.exists(bookmark_dir_slash_abs):
#         print(f"❌ Bookmark directory does not exist: {bookmark_dir_slash_abs}")
#         return False

#     is_save_updates = current_run_settings_obj["is_save_updates"] or current_run_settings_obj["is_overwrite_bm_redis_after"]
#     bm_redis_state_exists = os.path.exists(bookmark_redis_state_path)
#     is_should_save_redis_after = is_save_updates or not bm_redis_state_exists

#     if is_should_save_redis_after:
#         if IS_DEBUG:
#             if is_save_updates and bm_redis_state_exists:
#                 print("💾 Overwriting existing Redis after state...")
#             else:
#                 print("💾 Saving final Redis state...")

#         # Move the final Redis export to the bookmark directory
#         _ = shutil.move(redis_dump_state_path, bookmark_redis_state_path)
#         if IS_DEBUG:
#             print(f"💾 Saved final Redis state to: {bookmark_redis_state_path}")

#         # Generate friendly version
#         try:
#             results = convert_redis_state_file_to_friendly_and_save(
#                 bookmark_redis_state_path)
#             if IS_DEBUG:
#                 print("📋 Generated friendly Redis after")
#             return results
#         except Exception as e:
#             print(f"⚠️  Could not generate friendly Redis after: {e}")


#     return False
