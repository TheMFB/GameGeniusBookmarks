IS_DEBUG = False
# IS_DEBUG = False
ASYNC_WAIT_TIME = 1

SHOW_HIDDEN_COPY_LINE = True
HIDDEN_COLOR = "\033[38;2;13;42;52m"
RESET_COLOR = "\033[0m"

# Base directory is now the current repo root
import os
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Bookmarks directory is now in the repo root
BOOKMARKS_DIR = os.path.join(REPO_ROOT, "obs_bookmark_saves")

# Redis dump directory - you may want to adjust this path for your new setup
REDIS_DUMP_DIR = "/Users/mfb/dev/MFBTech/GameGeniusProject/GameGenius/game-genius/services/session_manager/utils/standalone/redis_dump"
INITIAL_REDIS_STATE_DIR = os.path.join(REPO_ROOT, "app")

IS_PRINT_JUST_CURRENT_SESSION_BOOKMARKS = True

USAGE_HELP = """
Usage: runonce_redis_integration.py <bookmark_name> [--save-updates] [-s] [--use-preceding-bookmark <session:bookmark>] [-p <session:bookmark>] [--blank-slate] [-b] [-v <video_path>] [--open-video <video_path>]

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
  -b, --blank-slate                          Use initial blank slate Redis state
  --save-last-redis                          Save current Redis state as redis_after.json
  -v <video_path>, --open-video <video_path> Open video file in OBS (paused) without saving or running anything

Navigation:
  next, previous, first, last                Navigate to adjacent bookmarks in the same directory
                                             (requires a last used bookmark to be set)

Examples:
  runonce_redis_integration.py my-bookmark
  runonce_redis_integration.py my-bookmark
  runonce_redis_integration.py my-bookmark session:other-bookmark
  runonce_redis_integration.py my-bookmark --blank-slate
  runonce_redis_integration.py next -p -s
  runonce_redis_integration.py previous
  runonce_redis_integration.py first
  runonce_redis_integration.py last
  runonce_redis_integration.py -v /path/to/video.mp4
  runonce_redis_integration.py --open-video /path/to/video.mp4
"""
