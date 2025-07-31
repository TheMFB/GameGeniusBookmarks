# import os
# import shutil

# from app.consts.bookmarks_consts import (
#     INITIAL_REDIS_STATE_DIR,
#     IS_DEBUG,
#     REDIS_DUMP_DIR,
# )
# from app.utils.decorators import print_def_name

# IS_PRINT_DEF_NAME = True


# @print_def_name(IS_PRINT_DEF_NAME)
# def handle_copy_blank_slate_to_redis_dump():
#     """
#     Handles saving the final Redis state (bookmark_temp or bookmark_temp_after) to redis_after.json or redis_before.json
#     Returns: True if redis_after was saved, False otherwise
#     """
#     initial_redis_before_state_filename = "initial_redis_before.json"
#     initial_redis_before_state_path = os.path.join(
#         INITIAL_REDIS_STATE_DIR, initial_redis_before_state_filename)

#     redis_temp_state_filename = "bookmark_temp.json"
#     redis_dump_state_path = os.path.join(
#         REDIS_DUMP_DIR, redis_temp_state_filename)

#     # Make sure the source file exists
#     if not os.path.exists(initial_redis_before_state_path):
#         print(
#             f"❌ Initial Redis before state file does not exist: {initial_redis_before_state_path}")
#         return False

#     if IS_DEBUG:
#         print(
#             f"💾 Saving Blank Slate {initial_redis_before_state_filename} to Redis Temp as {redis_temp_state_filename}...")

#     # if not run_redis_command('export', 'bookmark_temp_after'):
#     #     print("❌ Failed to export final Redis state")
#     #     return False

#     # Move the final Redis export to the bookmark directory
#     shutil.move(initial_redis_before_state_path, redis_dump_state_path)
#     if IS_DEBUG:
#         print(f"💾 Saved Blank Slate to: {redis_dump_state_path}")

#     return False
