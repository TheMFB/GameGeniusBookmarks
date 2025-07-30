import base64
import io
import os

import obsws_python as obs
from PIL import Image

from app.bookmarks_meta import patch_bookmark_meta, update_missing_bookmark_meta_fields
from app.consts.bookmarks_consts import IS_DEBUG, SCREENSHOT_SAVE_SCALE
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.obs_utils import get_media_source_info
from app.utils.printing_utils import print_color


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
                "sourceName": "Media Source",  # TODO: Make configurable if needed
                "imageFormat": "png"
            })
            image_data = response.image_data
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
            jpeg_path = os.path.join(
                matched_bookmark_path_abs, "screenshot.jpg")
            resized_image.save(jpeg_path, format="JPEG", quality=85)

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


def save_obs_media_info_to_bookmark_meta(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]

    is_save_updates = current_run_settings_obj["is_save_updates"]

    if not os.path.exists(matched_bookmark_path_abs):
        print_color(f"❌ Could not create bookmark metadata - bookmark directory doesn't exist: {matched_bookmark_path_abs}", 'red')
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