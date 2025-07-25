# type: ignore
from pprint import pprint
from typing import Literal
import obsws_python as obs
import os
import base64

from app.bookmarks_consts import IS_DEBUG
from app.videos import construct_full_video_file_path
from app.types import MatchedBookmarkObj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def open_video_in_obs(video_path: str, source_name: str = "Media Source"):
    """Open a video file in OBS with it paused"""

    try:
        # Check if video file exists
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return False

        # Convert to absolute path
        video_path = os.path.abspath(video_path)

        cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)

        # Set the media source to the video file
        cl.send("SetInputSettings", {
            "inputName": source_name,
            "inputSettings": {
                "local_file": video_path
            }
        })

        # Pause the media
        cl.send("TriggerMediaInputAction", {
            "inputName": source_name,
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE"
        })

        print(f"✅ Opened video in OBS: {video_path}")
        print(f"📺 Source: {source_name}")
        print(f"⏸️  Status: Paused")
        return True

    except Exception as e:
        print(f"❌ Error opening video in OBS: {e}")
        return False


@print_def_name(IS_PRINT_DEF_NAME)
def get_media_source_info():
    """Get media source information from OBS."""
    try:
        cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)

        # Get current media source settings
        settings = cl.send("GetInputSettings", {"inputName": "Media Source"})
        file_path = settings.input_settings.get("local_file", "")

        # Initialize with default values
        timestamp = 0
        timestamp_formatted = "00:00:00"

        # Only try to get cursor position if we have a valid file path
        if file_path and os.path.exists(file_path):
            try:
                # Get media status which includes cursor position
                media_status = cl.send("GetMediaInputStatus", {"inputName": "Media Source"})

                # Get cursor position from media_status
                if hasattr(media_status, 'media_cursor'):
                    timestamp = media_status.media_cursor
                    print(f"🔍 Raw timestamp: {timestamp}")

                    # Convert timestamp to seconds if it's in milliseconds
                    if timestamp > 3600:  # If timestamp is more than 1 hour, it's likely in milliseconds
                        timestamp = timestamp / 1000
                        print(f"🔍 Converted timestamp from ms to seconds: {timestamp}")

                    # Format timestamp
                    hours = int(timestamp // 3600)
                    minutes = int((timestamp % 3600) // 60)
                    seconds = int(timestamp % 60)

                    # Only show hours if they exist
                    if hours > 0:
                        timestamp_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        timestamp_formatted = f"{minutes:02d}:{seconds:02d}"

                    print(f"🔍 Formatted timestamp: {timestamp_formatted}")
                else:
                    print(f"❌ No media_cursor attribute in media_status")
                    raise Exception("No media_cursor attribute in media_status")

            except Exception as cursor_error:
                print(f"❌ Failed to get media cursor position: {cursor_error}")
                print(f"   File path: {file_path}")
                print(f"   File exists: {os.path.exists(file_path)}")
                raise cursor_error
        else:
            print(f"❌ No valid media file loaded")
            print(f"   File path: {file_path}")
            print(f"   Exists: {os.path.exists(file_path) if file_path else 'No file path'}")
            raise Exception("No valid media file loaded in OBS")

        return {
            'file_path': file_path,  # Keep for backward compatibility
            'video_filename': os.path.basename(file_path) if file_path else '',
            'timestamp': timestamp,
            'timestamp_formatted': timestamp_formatted
        }
    except Exception as e:
        print(f"❌ Failed to get media source info: {e}")
        raise e


@print_def_name(IS_PRINT_DEF_NAME)
def load_bookmark_into_obs(matched_bookmark_obj: MatchedBookmarkObj):
    # TODO(MFB): Look into me and see if this is the bookmark name or the whole bookmark (path+name)
    """Load OBS bookmark directly without using the bookmark manager script"""

    bookmark_info = matched_bookmark_obj["bookmark_info"]
    bookmark_path_slash_rel = matched_bookmark_obj["bookmark_path_slash_rel"]

    try:
        if IS_DEBUG:
            print(f"🔍 Debug - Loading bookmark_path_slash_rel: {bookmark_path_slash_rel}")
            print(
                f"🔍 Debug - Bookmark info keys: {list(bookmark_info.keys())}")
            print(
                f"🔍 Debug - video_filename: {bookmark_info.get('video_filename', 'NOT_FOUND')}")
            print(
                f"🔍 Debug - timestamp: {bookmark_info.get('timestamp', 'NOT_FOUND')}")
            print(
                f"🔍 Debug - timestamp_formatted: {bookmark_info.get('timestamp_formatted', 'NOT_FOUND')}")

        if not bookmark_info:
            print(
                f"❌ No file path found in {bookmark_path_slash_rel} metadata")
            return False

        cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)

        # Load the media file if different
        current_settings = cl.send(
            "GetInputSettings", {"inputName": "Media Source"})
        current_file = current_settings.input_settings.get("local_file", "")

        # Construct the full video file path from env variable
        video_filename = bookmark_info.get('video_filename', '')
        video_file_path = construct_full_video_file_path(video_filename)

        if not video_filename:
            print(f"❌ No file path found in bookmark_path_slash_rel metadata")
            if IS_DEBUG:
                print(
                    f"🔍 Debug - Available keys in bookmark_info: {list(bookmark_info.keys())}")
            return False

        if current_file != video_file_path:
            print(f"📁 Loading video file: {video_file_path}")
            cl.send("SetInputSettings", {
                "inputName": "Media Source",
                "inputSettings": {
                    "local_file": video_file_path
                }
            })
            # Wait longer for the media to load before trying to set cursor
            import time
            time.sleep(2)  # Increased from 1 to 2 seconds

        # Start playing the media first
        cl.send("TriggerMediaInputAction", {
            "inputName": "Media Source",
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY"
        })

        # Wait a moment for playback to start
        import time
        time.sleep(0.5)

        # Set the timestamp
        cl.send("SetMediaInputCursor", {
            "inputName": "Media Source",
            # Convert seconds to milliseconds
            "mediaCursor": int(bookmark_info['timestamp'] * 1000)
        })

        # Pause the media
        cl.send("TriggerMediaInputAction", {
            "inputName": "Media Source",
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE"
        })

        print(
            f"✅ Loaded OBS to timestamp from bookmark: {bookmark_info['timestamp_formatted']}")
        return True

    except Exception as e:
        print(f"❌ Failed to load OBS bookmark directly: {e}")
        return False
