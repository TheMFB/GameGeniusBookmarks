import os
import io
import base64
from PIL import Image
import obsws_python as obs
from app.bookmarks_consts import IS_DEBUG, SCREENSHOT_SAVE_SCALE
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def save_obs_screenshot(bookmark_path_slash_abs: str, is_overwrite: bool = False):
    """Takes screenshot from OBS and saves it to screenshot.jpg in the bookmark directory."""

    screenshot_path = os.path.join(bookmark_path_slash_abs, "screenshot.jpg")

    if not is_overwrite and os.path.exists(screenshot_path):
        print(f"📸 Screenshot already exists: {screenshot_path}")
        return

    try:
        cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)
        # Always request PNG from OBS for compatibility and lossless quality.
        # We'll convert to JPEG afterward to reduce file size and standardize format.
        response = cl.send("GetSourceScreenshot", {
            "sourceName": "Media Source",
            "imageFormat": "png"
        })
        image_data = response.image_data

        if image_data.startswith("data:image/png;base64,"):
            image_data = image_data.replace("data:image/png;base64,", "")

        decoded_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(decoded_bytes))

        # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
        if image.mode == 'RGBA':
            # Create a white background
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            # Paste the RGBA image onto the white background
            rgb_image.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
            image = rgb_image

        width = int(image.width * SCREENSHOT_SAVE_SCALE)
        height = int(image.height * SCREENSHOT_SAVE_SCALE)
        resized_image = image.resize((width, height))

        resized_image.save(screenshot_path, format="JPEG", quality=85)

        if IS_DEBUG:
            print(f"📋 Screenshot saved to: {screenshot_path}")
        print(f"📸 Screenshot saved to screenshot.jpg")

    except Exception as e:
        print(f"⚠️  2 Could not take screenshot: {e}")
        print(f"   Please ensure OBS is running and WebSocket server is enabled")
