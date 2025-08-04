from typing import Literal

from app.bookmarks.redis_states.redis_state_handlers.handle_load_dump_into_docker_redis import (
    handle_load_dump_into_docker_redis,
)
from app.bookmarks.redis_states.redis_state_handlers.handle_load_dump_into_local_redis import (
    handle_load_dump_into_local_redis,
)
from app.consts.bookmarks_consts import IS_LOCAL_REDIS_DEV
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_load_into_redis(
    before_or_after: Literal["before", "after"] = "after"
) -> int:
    """
    This function is used to load the redis state into the redis database.
    It first copies the redis_before.json to the redis dump directory and then loads it into the redis database.
    It then cleans up the temp file.
    """

    # Import from redis dump

    if IS_LOCAL_REDIS_DEV:
        results = handle_load_dump_into_local_redis(before_or_after)
        if results == 1:
            return 1
    else:
        results = handle_load_dump_into_docker_redis(before_or_after)
        if results == 1:
            return 1

    return 0