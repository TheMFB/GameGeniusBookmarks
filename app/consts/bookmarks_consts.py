import os

from dotenv import load_dotenv

from app.utils.printing_utils import pprint_dev, print_dev

load_dotenv()

## DEV CONSTANTS ##

# IS_DEBUG = True
IS_DEBUG = False
# IS_DEBUG_FULL = True
IS_DEBUG_FULL = False
IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON = False
# IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS = True
IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS = False
# IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS = True
IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS_ON_LS = False

## CONSTANTS ##

ASYNC_WAIT_TIME = 1
SHOW_HIDDEN_COPY_LINE = True
HIDDEN_COLOR = "\033[38;2;13;42;52m"
RESET_COLOR = "\033[0m"
SCREENSHOT_SAVE_SCALE = 0.5

# EXCLUDED_DIRS = {"archive", "archive_temp", "temp"}
EXCLUDED_DIRS = {"archive", "archive_temp", "temp", "videos"} # # TODO(MFB): DELETE AFTER TESTING
# EXCLUDED_DIRS = {"archive", "archive_temp", "temp", "videos", "grand-parent", "grand-parent-2"}


NON_NAME_BOOKMARK_KEYS = ["tags", "description", "video_filename", "timestamp", "type"]
# TODO(KERCH): On creation, we should not allow these to be used as directory names. If they exist, we should raise an error.
# TODO(KERCH): Create this list from the NAVIGATION_COMMANDS and NON_NAME_DIR_KEYS, instead of hardcoding it.
RESERVED_BOOKMARK_NAMES = [
    "tags",
    "description",
    "video_filename",
    "timestamp",
    "type",
    "previous",
    "next",
    "first",
    "last",
    "last_used",
    "create_new_bookmark"
]


## ABS PATHS ##

# TODO(MFB): There's a better way to grab the repo abs root than defining it in the .env file.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print_dev('---- REPO_ROOT:')
pprint_dev(REPO_ROOT)
ABS_OBS_BOOKMARKS_DIR = os.path.join(REPO_ROOT, "obs_bookmark_saves")

print_dev('---- ABS_OBS_BOOKMARKS_DIR:')
pprint_dev(ABS_OBS_BOOKMARKS_DIR)

# REDIS #
INITIAL_REDIS_STATE_DIR = os.path.join(REPO_ROOT, "app", "bookmarks", "redis_states")

IS_LOCAL_REDIS_DEV = os.environ.get('IS_LOCAL_REDIS_DEV', False)
LOCAL_REDIS_SESSIONS_HOST = "localhost"
LOCAL_REDIS_SESSIONS_PORT = 6379
LOCAL_REDIS_SESSIONS_DB = 0

if IS_LOCAL_REDIS_DEV:
    REDIS_DUMP_DIR = os.path.join(REPO_ROOT, "standalone_utils", "redis", "redis_dump")
else:
    GAME_GENIUS_DIR = os.environ.get('GAME_GENIUS_DIRECTORY', '')
    REDIS_DUMP_DIR = os.path.join(GAME_GENIUS_DIR, "game-genius/services/session_manager/utils/standalone/redis_dump")
