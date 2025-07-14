# type: ignore
from pprint import pprint
from typing import Literal
import obsws_python as obs
import os

from app.bookmarks_consts import IS_DEBUG

ColorTypes = Literal['black', 'red', 'green',
                     'yellow', 'blue', 'magenta', 'cyan', 'white']


def print_color(text: str, color: ColorTypes):
    color_codes = {
        'black': 30,
        'red': 31,
        'green': 32,
        'yellow': 33,
        'blue': 34,
        'magenta': 35,
        'cyan': 36,
        'white': 37
    }

    print(f"\033[{color_codes[color]}m{text}\033[0m")


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
                print(f"🔍 Debug - media_status: ")
                pprint(media_status)

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
