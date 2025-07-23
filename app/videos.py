"""
Integration script that coordinates OBS bookmarks with Redis state management
"""
from pprint import pprint
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from app.bookmarks_consts import IS_DEBUG, IS_DEBUG_FULL

# Load environment variables
load_dotenv()


def get_video_path_from_env():
    """Get the VIDEO_PATH from environment variables."""
    # TODO(MFB): This is being called for each bookmark when we are assembling the bookmarks. This should really only be called once.
    video_path = os.getenv('VIDEO_PATH_2')
    if not video_path:
        print("⚠️  VIDEO_PATH not found in environment variables")
        return None
    return video_path


def construct_full_video_file_path(video_filename):
    """Construct the full file path from VIDEO_PATH and filename."""
    video_path = get_video_path_from_env()
    if not video_path:
        return None

    # Ensure the video path ends with a separator
    if not video_path.endswith('/') and not video_path.endswith('\\'):
        video_path += '/'

    return os.path.join(video_path, video_filename)
