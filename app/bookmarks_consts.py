IS_DEBUG = False
# IS_DEBUG = True
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

# Keep GAME_GENIUS_BASE_DIR for backward compatibility if needed elsewhere
GAME_GENIUS_BASE_DIR = "/Users/mfb/dev/MFBTech/GameGeniusProject/GameGenius"
