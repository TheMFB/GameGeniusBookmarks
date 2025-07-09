# type: ignore
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

        # Try to get current cursor position, but handle errors gracefully
        timestamp = 0
        timestamp_formatted = "00:00:00"

        try:
            cursor_info = cl.send("GetMediaInputCursor", {"inputName": "Media Source"})
            timestamp = cursor_info.media_cursor

            # Format timestamp
            hours = int(timestamp // 3600)
            minutes = int((timestamp % 3600) // 60)
            seconds = int(timestamp % 60)
            timestamp_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception as cursor_error:
            # If we can't get the cursor position, use default values
            if IS_DEBUG:
                print(f"⚠️  Could not get media cursor position: {cursor_error}")
                print(f"   Using default timestamp (00:00:00)")

        return {
            'file_path': file_path,
            'video_filename': os.path.basename(file_path) if file_path else '',
            'timestamp': timestamp,
            'timestamp_formatted': timestamp_formatted
        }
    except Exception as e:
        print(f"❌ Failed to connect to OBS: {e}")
        print(f"   Please ensure:")
        print(f"   1. OBS is running")
        print(f"   2. WebSocket server is enabled in OBS (Tools > WebSocket Server Settings)")
        print(f"   3. Port 4455 is set in WebSocket settings")
        print(f"   4. No password is set (or update the code to use your password)")
        # Return a minimal info structure so the bookmark can still be created
        return {
            'file_path': '',
            'video_filename': '',
            'timestamp': 0,
            'timestamp_formatted': '00:00:00'
        }
