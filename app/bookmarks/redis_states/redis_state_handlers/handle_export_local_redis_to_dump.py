import json
import os
import pickle
from typing import Literal

import redis

from app.bookmarks.redis_states.redis_state_utils import get_temp_redis_state_name
from app.consts.bookmarks_consts import (
    LOCAL_REDIS_SESSIONS_DB,
    LOCAL_REDIS_SESSIONS_HOST,
    LOCAL_REDIS_SESSIONS_PORT,
    REDIS_DUMP_DIR,
)
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


# TODO(MFB): ++ These aren't hitting the docker redis databases. AND we have a name conflict. See <---
@print_def_name(IS_PRINT_DEF_NAME)
def handle_export_local_redis_to_dump(before_or_after: Literal["before", "after"]) -> int:
    """
    Export the current Redis database to redis backup or redis backup after into a temp folder.
    - Export the current redis database
    """

    temp_redis_state_name = get_temp_redis_state_name(before_or_after)

    json_filepath = f"{REDIS_DUMP_DIR}/{temp_redis_state_name}.json"
    pkl_filepath = f"{REDIS_DUMP_DIR}/{temp_redis_state_name}.pkl"

    try:
        r = redis.Redis(host=LOCAL_REDIS_SESSIONS_HOST,
                        port=LOCAL_REDIS_SESSIONS_PORT, db=LOCAL_REDIS_SESSIONS_DB)

        def safe_decode(value):
            if isinstance(value, bytes):
                try:
                    return value.decode('utf-8')
                except Exception:
                    return value  # fallback to bytes
            return value

        def try_json_load(value):
            # Try to decode a string as JSON, otherwise return as-is
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except Exception:
                    return value
            return value

        data = {}
        for key in r.scan_iter('*'):
            key_type = r.type(key)
            if key_type == b'string':
                value = r.get(key)
                if value is not None:
                    decoded = safe_decode(value)
                    data[key.decode("utf-8")] = try_json_load(decoded)
            else:
                print(
                    f"Skipping key {key.decode('utf-8')} of type {key_type.decode('utf-8')}") # type: ignore
    except Exception as e:
        print(f"❌ Error exporting from Redis to Redis Dump: {e}")
        return 1

    os.makedirs(REDIS_DUMP_DIR, exist_ok=True)

    # Try to save as JSON, fallback to pickle if it fails
    try:
        with open(json_filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Backup saved as {json_filepath} (JSON)")
    except Exception as e:
        with open(pkl_filepath, "wb") as f:
            pickle.dump(data, f)
        print(f"Backup saved as {pkl_filepath} (Pickle, reason: {e})")

    return 0


# @print_def_name(IS_PRINT_DEF_NAME)
# def handle_export_local_redis_to_dump_bak(filename: Literal["bookmark_temp", "bookmark_temp_after"]) -> int:
#     """
#     Export the current Redis database to redis backup or redis backup after into a temp folder.
#     - Export the current redis database
#     """

#     json_filepath = f"{REDIS_DUMP_DIR}/{filename}.json"
#     pkl_filepath = f"{REDIS_DUMP_DIR}/{filename}.pkl"

#     try:
#         r = redis.Redis(host=LOCAL_REDIS_SESSIONS_HOST,
#                         port=LOCAL_REDIS_SESSIONS_PORT, db=LOCAL_REDIS_SESSIONS_DB)

#         def safe_decode(value):
#             if isinstance(value, bytes):
#                 try:
#                     return value.decode('utf-8')
#                 except Exception:
#                     return value  # fallback to bytes
#             return value

#         def try_json_load(value):
#             # Try to decode a string as JSON, otherwise return as-is
#             if isinstance(value, str):
#                 try:
#                     return json.loads(value)
#                 except Exception:
#                     return value
#             return value

#         data = {}
#         for key in r.scan_iter('*'):
#             key_type = r.type(key)
#             if key_type == b'string':
#                 value = r.get(key)
#                 if value is not None:
#                     decoded = safe_decode(value)
#                     data[key.decode("utf-8")] = try_json_load(decoded)
#             else:
#                 print(
#                     f"Skipping key {key.decode('utf-8')} of type {key_type.decode('utf-8')}")
#     except Exception as e:
#         print(f"❌ Error exporting from Redis to Redis Dump: {e}")
#         return 1

#     os.makedirs(REDIS_DUMP_DIR, exist_ok=True)

#     # Try to save as JSON, fallback to pickle if it fails
#     try:
#         with open(json_filepath, "w") as f:
#             json.dump(data, f, indent=2)
#         print(f"Backup saved as {json_filepath} (JSON)")
#     except Exception as e:
#         with open(pkl_filepath, "wb") as f:
#             pickle.dump(data, f)
#         print(f"Backup saved as {pkl_filepath} (Pickle, reason: {e})")

#     return 0
