import subprocess
from typing import Literal

from app.bookmarks.redis_states.redis_state_utils import get_temp_redis_state_name
from app.consts.bookmarks_consts import IS_DEBUG
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_export_docker_redis_to_redis_dump(
    before_or_after: Literal["before", "after"]
) -> int:
    """
    This function is used to export the redis state from the redis database to the redis dump directory.
    """
    temp_redis_state_name = get_temp_redis_state_name(before_or_after)

    try:
        # Docker mode
        cmd = f"docker exec -it session_manager python -m utils.standalone.redis_export {temp_redis_state_name}"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=False)

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
        print("❌ Error running Redis Export to Redis Dump")
        print(f"   Exception: {e}")
        return 1
