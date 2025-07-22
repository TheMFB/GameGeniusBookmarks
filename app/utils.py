# type: ignore
from pprint import pprint
from typing import Literal
import obsws_python as obs
import os
import base64


from app.bookmarks_consts import IS_DEBUG, BOOKMARKS_DIR

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


def get_embedded_file_link(colon_separated_path, text):
    slash_separated_path = colon_separated_path.replace(':', '/')
    if text == "📁":
        file_path = BOOKMARKS_DIR + '/' + slash_separated_path + "/folder_meta.json"
    else:
        file_path = BOOKMARKS_DIR + '/' + slash_separated_path + "/bookmark_meta.json"

    # Ensure three slashes after file:
    uri = f"file://{file_path}" if file_path.startswith(
        '/') else f"file:///{file_path}"
    return f"\033]8;;{uri}\033\\{text}\033]8;;\033\\"


def get_iterm_image_code(image_path, width="auto", height="auto"):
    try:
        with open(image_path, "rb") as f:
            img_data = f.read()
        b64_img = base64.b64encode(img_data).decode("utf-8")
        return f"\033]1337;File=inline=1;width={width};height={height};preserveAspectRatio=1:{b64_img}\a"
    except Exception:
        return None

def print_image(image_path, width="auto", height="auto"):
    """
    Print an image to the iTerm2 terminal using ANSI escape codes.
    """
    image_code = get_iterm_image_code(image_path, width, height)
    if image_code:
        print(image_code)

IS_PRINT_FILE_LINK= True
IS_ADJUST_TO_STACK = True

def print_def_name(should_print=True):
    """
    This will print the function name and the file path.
    It will also print the file path in a clickable link.
    It will also print the function name and the file path in a clickable link.
    It will also print the function name and the file path in a clickable link.

    Args:
        should_print (bool): Whether to actually print the function name. Default is True.
                           Can be used like @print_def_name(not IS_DEBUG) to conditionally disable.

    Note that if you want to get it to open through Cursor, you may need to `brew install duti`, and select Cursor as the default app for .py files.
    """
    def decorator(func):
        if not should_print:
            # If we shouldn't print, just return the original function unchanged
            return func

        if IS_ADJUST_TO_STACK:
            import functools
            import inspect

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Subtract 1 to not count the wrapper itself
                depth = max(1, len(inspect.stack()) - 9)
                print('')
                if IS_PRINT_FILE_LINK:
                    print(
                        f"{'_' * depth * 2} {get_embedded_file_link(func)} {'_' * depth * 2}")
                else:
                    print(f"{'_' * depth * 2} {func.__name__} {'_' * depth * 2}")

                return func(*args, **kwargs)
            return wrapper
        else:
            def wrapper(*args, **kwargs):
                print('')
                if IS_PRINT_FILE_LINK:
                    print(f"______ {get_embedded_file_link(func)} ______")
                else:
                    print(f"______ {func.__name__} ______")
                return func(*args, **kwargs)
            return wrapper

    # Handle the case where the decorator is used without parentheses
    # e.g., @print_def_name instead of @print_def_name()
    if callable(should_print):
        # In this case, should_print is actually the function being decorated
        func = should_print
        should_print = True  # Default behavior
        return decorator(func)

    return decorator

def print_main_def_name(func):
    def wrapper(*args, **kwargs):
        print('')
        print('')
        if IS_PRINT_FILE_LINK:
            print(f"========= {get_embedded_file_link(func)} ==========")
        else:
            print(f"========= {func.__name__} ==========")
        print('')
        return func(*args, **kwargs)
    return wrapper

def print_def_args(func):
    def wrapper(*args, **kwargs):
        print(f"-- Args:")
        pprint(args)
        print(f"-- Kwargs:")
        pprint(kwargs)
        return func(*args, **kwargs)
    return wrapper
