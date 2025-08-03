import json
import os
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


@print_def_name(IS_PRINT_DEF_NAME)
def handle_load_dump_into_local_redis(before_or_after: Literal["before", "after"]) -> int:
    """
    This function is used to load the redis state from the redis dump directory into the redis database.
    """
    filename = get_temp_redis_state_name(before_or_after)


    json_filepath = f"{REDIS_DUMP_DIR}/{filename}.json"

    r = redis.Redis(host=LOCAL_REDIS_SESSIONS_HOST,
                    port=LOCAL_REDIS_SESSIONS_PORT, db=LOCAL_REDIS_SESSIONS_DB)

    # Wipe the database before restoring
    r.flushdb()
    print("Redis database wiped.")

    data = None
    if os.path.exists(json_filepath):
        try:
            with open(json_filepath, "r") as f:
                data = json.load(f)
            print(f"Loaded backup from {json_filepath} (JSON)")
        except Exception as e:
            print(f"Failed to load JSON: {e}")

    if data is None:
        print("No backup file found or failed to load.")
        return 1

    session_ids = set()

    for key, value in data.items():
        if key.startswith('user_session'):
            session_ids.add(value)
        # If value is a dict or list, encode as JSON string
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        # If value is not bytes, encode as utf-8
        if not isinstance(value, bytes):
            value = str(value).encode('utf-8')
        r.set(key, value)
        # TODO(MFB): Loop through all of these and publish each...?


    print("Redis data restored!")
    return 0
