# Base directory is now the current repo root
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# TODO(KERCH): Organize.

## DEV CONSTANTS ##

# IS_DEBUG = True
IS_DEBUG = False
# IS_DEBUG_FULL = True
IS_DEBUG_FULL = False
IS_DEBUG_PRINT_ALL_BOOKMARKS_JSON = True
IS_PRINT_DEV = True
IS_PRINT_JUST_CURRENT_DIRECTORY_BOOKMARKS = True

# LOCAL REDIS DEV
IS_LOCAL_REDIS_DEV = os.environ.get('IS_LOCAL_REDIS_DEV', False)

LOCAL_REDIS_SESSIONS_HOST = "localhost"
LOCAL_REDIS_SESSIONS_PORT = 6379
LOCAL_REDIS_SESSIONS_DB = 0

## CONSTANTS ##

ASYNC_WAIT_TIME = 1
SHOW_HIDDEN_COPY_LINE = True
HIDDEN_COLOR = "\033[38;2;13;42;52m"
RESET_COLOR = "\033[0m"
SCREENSHOT_SAVE_SCALE = 0.5

# EXCLUDED_DIRS = {"archive", "archive_temp", "temp"}
# EXCLUDED_DIRS = {"archive", "archive_temp", "temp", "videos"} # # TODO(MFB): DELETE AFTER TESTING
EXCLUDED_DIRS = {"archive", "archive_temp", "temp", "videos", "grand-parent", "grand-parent-2"}

NAVIGATION_COMMANDS = ["next", "previous", "first", "last"]

NON_NAME_BOOKMARK_KEYS = ["tags", "description", "video_filename", "timestamp", "type"]
# TODO(KERCH): On creation, we should not allow these to be used as directory names. If they exist, we should raise an error.
# TODO(KERCH): Create this list from the NAVIGATION_COMMANDS and NON_NAME_DIR_KEYS, instead of hardcoding it.
RESERVED_DIR_KEYS = ["tags", "description", "video_filename", "timestamp", "type", "previous", "next", "first", "last"]


## ABS PATHS ##

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Bookmarks directory is now in the repo root
ABS_OBS_BOOKMARKS_DIR = os.path.join(REPO_ROOT, "obs_bookmark_saves")
# Redis dump directory - use the GameGenius directory from environment variable
GAME_GENIUS_DIR = os.environ.get('GAME_GENIUS_DIRECTORY', '')

INITIAL_REDIS_STATE_DIR = os.path.join(REPO_ROOT, "app")
if IS_LOCAL_REDIS_DEV:
    REDIS_DUMP_DIR = os.path.join(REPO_ROOT, "standalone_utils", "redis", "redis_dump")
else:
    REDIS_DUMP_DIR = os.path.join(GAME_GENIUS_DIR, "game-genius/services/session_manager/utils/standalone/redis_dump")


# TODO(MFB): Move these to a print-help constants file.

USAGE_HELP = """
Usage: main.py <bookmark_string> [--save-updates] [-s] [--use-preceding-bookmark <folder:bookmark>] [-p <folder:bookmark>] [--blank-slate] [-b] [-v <video_path>] [--open-video <video_path>] [--tags <tag1> <tag2> ...]

Navigation commands:
  next, previous, first, last    Navigate to adjacent bookmarks in the same directory
"""

# TODO(MFB): Add an option to show redis before and after diffs.
OPTIONS_HELP = USAGE_HELP + """

Options:
  -h, --help, -ls                            Show this help message and exit
    (bmls / lsbm)
  -s, --save-updates                         Save redis state updates (before and after)
    (bmsave / savebm)
  -p <bookmark>, --use-preceding-bookmark    Use redis_after.json from preceding or specified bookmark as redis_before.json
  -d, --dry-run                              Dry run, Load bookmark only (no main process)
  -sd, --super-dry-run                       Super dry run, Load bookmark only (no main process, no Redis operations)
  --no-obs                                   No OBS mode, Create bookmarks without OBS connection (for tagging only)
  -b, --blank-slate                          Use initial blank slate Redis state
  --save-last-redis                          Save current Redis state as redis_after.json
  -v <video_path>, --open-video <video_path> Open video file in OBS (paused) without saving or running anything
  -t, --tags <tag1> <tag2> ...              Add tags to bookmark metadata

Navigation:
  next, previous, first, last                Navigate to adjacent bookmarks in the same directory
                                             (requires a last used bookmark to be set)

Examples:
  main.py my-bookmark
  main.py my-bookmark
  main.py my-bookmark folder:other-bookmark
  main.py my-bookmark --blank-slate
  main.py next -p -s
  main.py previous
  main.py first
  main.py last
  main.py -v /path/to/video.mp4
  main.py --open-video /path/to/video.mp4
  main.py --tags tag1 tag2
  main.py my-bookmark -sd
  main.py my-bookmark --no-obs -t important highlight
"""


