import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

## DEV CONSTANTS ##

# IS_DEBUG = True
IS_DEBUG = False
# IS_DEBUG_FULL = True
# TODO(): Rename this -- no idea what it does without researching it.
IS_DEBUG_FULL = False
IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON = False
# IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS = True
IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS = False
# IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS = True
IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS = False
IS_APPLY_AUTOTAGS = True
# IS_APPLY_AUTOTAGS = False

TagType = Literal["user_tags", "auto_tags", "both"]
ACTIVE_TAG_TYPE: TagType = "both"

## CONSTANTS ##

ASYNC_WAIT_TIME = 1
SHOW_HIDDEN_COPY_LINE = True
HIDDEN_COLOR = "\033[38;2;13;42;52m"
RESET_COLOR = "\033[0m"
SCREENSHOT_SAVE_SCALE = 0.5

EXCLUDED_DIRS = {"archive", "archive_temp", "temp"}

NON_NAME_BOOKMARK_KEYS = [
    "tags",
    "description",
    "video_filename",
    "timestamp",
    "type",
    "auto_tags_t1",
    "auto_tags_t2",
    "auto_tags_t3",
]
# TODO(KERCH): On creation, we should not allow these to be used as directory names. If they exist, we should raise an error.
# TODO(KERCH): Create this list from the NAVIGATION_COMMANDS and NON_NAME_DIR_KEYS, instead of hardcoding it.
RESERVED_BOOKMARK_NAMES = [
    "tags",
    "description",
    "video_filename",
    "type",
    "previous",
    "next",
    "first",
    "last",
    "last_used",
    "current",
    "again",
    "create_new_bookmark",
]


## ABS PATHS ##

REPO_ROOT = str(Path(__file__).resolve().parents[2])

ABS_OBS_BOOKMARKS_DIR = os.path.join(REPO_ROOT, "obs_bookmark_saves")

# REDIS #
INITIAL_REDIS_STATE_DIR = os.path.join(REPO_ROOT, "app", "bookmarks", "redis_states")

IS_LOCAL_REDIS_DEV = (
    os.environ.get("IS_LOCAL_REDIS_DEV", False) == "True"
    or os.environ.get("IS_LOCAL_REDIS_DEV", False) == "true"
)
LOCAL_REDIS_SESSIONS_HOST = "localhost"
LOCAL_REDIS_SESSIONS_PORT = 6379
LOCAL_REDIS_SESSIONS_DB = 0

GAME_GENIUS_PARENT_DIR = str(Path(REPO_ROOT).resolve().parents[0])
REDIS_DUMP_DIR = (
    os.path.join(REPO_ROOT, "standalone_utils", "redis", "redis_dump")
    if IS_LOCAL_REDIS_DEV
    else os.path.join(
        GAME_GENIUS_PARENT_DIR,
        "game-genius/services/session_manager/utils/standalone/redis_dump",
    )
)
