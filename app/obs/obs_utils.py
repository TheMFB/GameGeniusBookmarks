import base64
import io
import os
import time

import obsws_python as obs
from PIL import Image

from app.bookmarks.bookmarks_meta import (
    patch_bookmark_meta,
    update_missing_bookmark_meta_fields,
)
from app.consts.bookmarks_consts import IS_DEBUG, SCREENSHOT_SAVE_SCALE
from app.obs.videos import construct_full_video_file_path
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.decorators import print_def_name
from app.utils.printing_utils import print_color

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
        print("⏸️  Status: Paused")
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
        file_path = settings.input_settings.get(  # type: ignore
            "local_file", "")

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
                    timestamp = media_status.media_cursor  # type: ignore
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
                    print("❌ No media_cursor attribute in media_status")
                    raise Exception("No media_cursor attribute in media_status")

            except Exception as cursor_error:
                print(f"❌ Failed to get media cursor position: {cursor_error}")
                print(f"   File path: {file_path}")
                print(f"   File exists: {os.path.exists(file_path)}")
                raise cursor_error
        else:
            print("❌ No valid media file loaded")
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
def load_bookmark_into_obs(matched_bookmark_obj: MatchedBookmarkObj) -> int:
    # TODO(MFB): Look into me and see if this is the bookmark name or the whole bookmark (path+name)
    """Load OBS bookmark directly without using the bookmark manager script"""

    bookmark_info = matched_bookmark_obj.get("bookmark_info", {})
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
            return 1

        cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)

        # Load the media file if different
        current_settings = cl.send(
            "GetInputSettings", {"inputName": "Media Source"})
        current_file = current_settings.input_settings.get("local_file", "") # type: ignore

        # Construct the full video file path from env variable
        video_filename = bookmark_info.get('video_filename', '')
        video_file_path = construct_full_video_file_path(video_filename)

        if not video_filename:
            print("❌ No file path found in bookmark_path_slash_rel metadata")
            if IS_DEBUG:
                print(
                    f"🔍 Debug - Available keys in bookmark_info: {list(bookmark_info.keys())}")
            return 1

        if current_file != video_file_path:
            print(f"📁 Loading video file: {video_file_path}")
            cl.send("SetInputSettings", {
                "inputName": "Media Source",
                "inputSettings": {
                    "local_file": video_file_path
                }
            })
            # Wait longer for the media to load before trying to set cursor
            time.sleep(2)  # Increased from 1 to 2 seconds

        # Start playing the media first
        cl.send("TriggerMediaInputAction", {
            "inputName": "Media Source",
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY"
        })

        # Wait a moment for playback to start
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
        return 0

    except Exception as e:
        print(f"❌ Failed to load OBS bookmark directly: {e}")
        return 1


@print_def_name(IS_PRINT_DEF_NAME)
def save_obs_screenshot_to_bookmark_path(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):
    matched_bookmark_path_rel = matched_bookmark_obj["bookmark_path_slash_rel"]
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]

    is_save_updates = current_run_settings_obj["is_save_updates"]

    screenshot_path = os.path.join(matched_bookmark_path_abs, "screenshot.jpg")
    if os.path.exists(screenshot_path) and not is_save_updates:
        if IS_DEBUG:
            print(
                f"📸 Screenshot already exists, preserving: {screenshot_path}")
        print(
            f"📸 Using existing screenshot: {matched_bookmark_path_rel}/screenshot.jpg")
    else:
        try:
            cl = obs.ReqClient(
                host="localhost", port=4455, password="", timeout=3)

            response = cl.send("GetSourceScreenshot", {
                "sourceName": "Media Source",
                "imageFormat": "png"
            })

            image_data = response.image_data  # type: ignore
            if image_data.startswith("data:image/png;base64,"):
                image_data = image_data.replace(
                    "data:image/png;base64,", "")
            decoded_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(decoded_bytes))

            # Resize using SCREENSHOT_SAVE_SCALE
            width = int(image.width * SCREENSHOT_SAVE_SCALE)
            height = int(image.height * SCREENSHOT_SAVE_SCALE)
            resized_image = image.resize((width, height))

            # Save resized image
            if resized_image.mode in ("RGBA", "LA"):
                # Convert image to RGB to remove alpha channel for JPEG compatibility
                resized_image = resized_image.convert("RGB")
            resized_image.save(screenshot_path, format="JPEG", quality=85)

            if IS_DEBUG:
                print(f"📋 Screenshot saved to: {screenshot_path}")
            print(
                f"📸 Screenshot saved to: {matched_bookmark_path_rel}/screenshot.jpg")

        except Exception as e:
            print(f"⚠️  1 Could not take screenshot: {e}")
            print("   Please ensure OBS is running and WebSocket server is enabled")

# TODO(MFB): Debug and destroy
# Backup of a duplicate of the above:
# @print_def_name(IS_PRINT_DEF_NAME)
# def save_obs_screenshot(bookmark_path_slash_abs: str, is_overwrite: bool = False):
#     """Takes screenshot from OBS and saves it to screenshot.jpg in the bookmark directory."""

#     screenshot_path = os.path.join(bookmark_path_slash_abs, "screenshot.jpg")

#     if not is_overwrite and os.path.exists(screenshot_path):
#         print(f"📸 Screenshot already exists: {screenshot_path}")
#         return

#     try:
#         cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)
#         # Always request PNG from OBS for compatibility and lossless quality.
#         # We'll convert to JPEG afterward to reduce file size and standardize format.
#         response = cl.send("GetSourceScreenshot", {
#             "sourceName": "Media Source",
#             "imageFormat": "png"
#         })
#         image_data = response.image_data

#         if image_data.startswith("data:image/png;base64,"):
#             image_data = image_data.replace("data:image/png;base64,", "")

#         decoded_bytes = base64.b64decode(image_data)
#         image = Image.open(io.BytesIO(decoded_bytes))

#         # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
#         if image.mode == 'RGBA':
#             # Create a white background
#             rgb_image = Image.new('RGB', image.size, (255, 255, 255))
#             # Paste the RGBA image onto the white background
#             rgb_image.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
#             image = rgb_image

#         width = int(image.width * SCREENSHOT_SAVE_SCALE)
#         height = int(image.height * SCREENSHOT_SAVE_SCALE)
#         resized_image = image.resize((width, height))

#         resized_image.save(screenshot_path, format="JPEG", quality=85)

#         if IS_DEBUG:
#             print(f"📋 Screenshot saved to: {screenshot_path}")
#         print(f"📸 Screenshot saved to screenshot.jpg")

#     except Exception as e:
#         print(f"⚠️  2 Could not take screenshot: {e}")
#         print(f"   Please ensure OBS is running and WebSocket server is enabled")


@print_def_name(IS_PRINT_DEF_NAME)
def save_obs_media_info_to_bookmark_meta(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
) -> int:
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]

    is_save_updates = current_run_settings_obj["is_save_updates"]

    if not os.path.exists(matched_bookmark_path_abs):
        print_color(
            f"❌ Could not create bookmark metadata - bookmark directory doesn't exist: {matched_bookmark_path_abs}", 'red')
        return 1

    if current_run_settings_obj["is_no_obs"]:
        # Create minimal metadata without OBS info
        minimal_media_info = {
            'file_path': '',
            'video_filename': '',
            'timestamp': 0,
            'timestamp_formatted': '00:00:00'
        }
        patch_bookmark_meta(
            matched_bookmark_obj,
            minimal_media_info,
            current_run_settings_obj["tags"]
        )

        if IS_DEBUG:
            print("📋 Created minimal bookmark metadata (no OBS info)")
    else:
        media_info = get_media_source_info()
        if media_info:
            if is_save_updates:
                patch_bookmark_meta(
                    matched_bookmark_obj,
                    media_info,
                    current_run_settings_obj["tags"]
                )
                if IS_DEBUG:
                    print(
                        f"📋 Patched bookmark obs metadata with tags: {current_run_settings_obj['tags']}")

            else:
                update_missing_bookmark_meta_fields(
                    matched_bookmark_obj,
                    media_info,
                    current_run_settings_obj["tags"]
                )
                if IS_DEBUG:
                    print(
                        f"📋 Updated missing bookmark obs metadata with tags: {current_run_settings_obj['tags']}")

    return 0
