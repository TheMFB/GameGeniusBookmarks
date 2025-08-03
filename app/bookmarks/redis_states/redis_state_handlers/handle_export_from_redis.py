from typing import Literal

from app.bookmarks.redis_states.redis_state_handlers.handle_export_docker_redis_to_dump import (
    handle_export_docker_redis_to_redis_dump,
)
from app.bookmarks.redis_states.redis_state_handlers.handle_export_local_redis_to_dump import (
    handle_export_local_redis_to_dump,
)
from app.consts.bookmarks_consts import IS_LOCAL_REDIS_DEV
from app.utils.decorators import print_def_name
from app.utils.printing_utils import print_dev

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_export_from_redis(
    before_or_after: Literal["before", "after"] = "after"
) -> int:
    """
    This function is used to load the redis state into the redis database.
    It first copies the redis_before.json to the redis dump directory and then loads it into the redis database.
    It then cleans up the temp file.
    """
    # Export from redis to redis dump
    if IS_LOCAL_REDIS_DEV:
        print_dev('---- !!!! handle_export_from_redis IS_LOCAL_REDIS_DEV', 'red')
        results =  handle_export_local_redis_to_dump(before_or_after)
        if results == 1:
            return 1
    else:
        results = handle_export_docker_redis_to_redis_dump(before_or_after)
        if results == 1:
            return 1

    return 0
