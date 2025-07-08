# type: ignore
from typing import Literal
import obsws_python as obs

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


def get_media_source_info(source_name="Media Source"):
    """Get current media source information from OBS"""
    try:
        # This would need to be implemented to get current OBS state
        # For now, we'll need to extract this from the OBS command output
        # or call OBS directly
        cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)

        # Get source settings to find the file path
        source_settings = cl.send(
            "GetInputSettings", {"inputName": source_name})

        # Get source status
        source_status = cl.send("GetMediaInputStatus", {
                                "inputName": source_name})

        return {
            "source_name": source_name,
            "file_path": source_settings.input_settings.get("local_file", "Unknown"),
            "media_state": source_status.media_state,
            "media_duration": source_status.media_duration,
            "media_cursor": source_status.media_cursor
        }
    except Exception as e:
        print(f"⚠️  Could not get media source info: {e}")
        return None
