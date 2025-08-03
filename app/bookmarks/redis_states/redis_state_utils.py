from typing import Literal

IS_PRINT_DEF_NAME = True


def get_temp_redis_state_name(before_or_after: Literal["before", "after"]) -> Literal["bookmark_temp", "bookmark_temp_after"]:
    # TODO(): I don't like "bookmark_temp" and "bookmark_temp_after" -> "redis_temp_state_before" and "redis_temp_state_after"
    if before_or_after == "before":
        return "bookmark_temp"
    return "bookmark_temp_after"
