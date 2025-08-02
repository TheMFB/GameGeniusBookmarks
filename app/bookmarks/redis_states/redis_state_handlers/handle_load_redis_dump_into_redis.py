import subprocess

from app.bookmarks.redis_states.redis_state_handlers.local_load_redis_dump_into_redis import (
    local_load_redis_dump_into_redis,
)
from app.consts.bookmarks_consts import IS_DEBUG, IS_LOCAL_REDIS_DEV
from app.utils.decorators import print_def_name
from app.utils.printing_utils import print_dev

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_load_redis_dump_into_redis() -> int:
    """
    This function is used to load the redis state from the redis dump directory into the redis database.
    """
    try:
        if IS_LOCAL_REDIS_DEV:
            print_dev('running local redis load', 'magenta')
            print_dev(str(IS_LOCAL_REDIS_DEV))
            print_dev(str(type(IS_LOCAL_REDIS_DEV)))

            return local_load_redis_dump_into_redis("bookmark_temp")

        # Docker mode
        cmd = "docker exec -it session_manager python -m utils.standalone.redis_load bookmark_temp"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            print(f"❌ Redis command failed: {cmd}")
            print(f"   Error: {result.stderr}")
            print(f"   Output: {result.stdout}")
            return 1

        if IS_DEBUG:
            print(
                f"✅ Redis command succeeded: {cmd}")
        return 0

    except Exception as e:
        print("❌ Error running Redis Load from Redis Dump")
        print(f"   Exception: {e}")
        return 1

