from pprint import pprint
import os
import json
import subprocess
import shutil
import base64
import io
from datetime import datetime
from PIL import Image
import obsws_python as obs

from app.utils.obs_utils import load_bookmark_into_obs, get_media_source_info
from app.bookmarks_meta import create_bookmark_meta
from redis_friendly_converter import convert_file as convert_redis_to_friendly
from app.bookmark_dir_processes import get_all_valid_root_dir_names
from app.bookmarks_redis import run_redis_command, copy_initial_redis_state
# copy_preceding_bookmark_redis_state, copy_specific_bookmark_redis_state
from app.consts.bookmarks_consts import IS_DEBUG, IS_LOCAL_REDIS_DEV, REDIS_DUMP_DIR, SCREENSHOT_SAVE_SCALE
from app.types.bookmark_types import MatchedBookmarkObj, CurrentRunSettings
from app.utils.printing_utils import *


def handle_matched_bookmark(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings_obj: CurrentRunSettings,
):

    ## MATCHED BOOKMARK ##
    matched_bookmark_path_rel = matched_bookmark_obj["bookmark_path_slash_rel"]
    matched_bookmark_path_abs = matched_bookmark_obj["bookmark_path_slash_abs"]


    # EXISTING BOOKMARK WORKFLOW
    # print(f"📖 Bookmark '{matched_bookmark_path_rel}' exists - loading OBS state...")

    # Load the OBS bookmark using the matched name
    is_obs_loaded = load_bookmark_into_obs(matched_bookmark_obj)
    if not is_obs_loaded:
        print("❌ Failed to load OBS bookmark")
        return 1

    # Sanity check that the bookmark exists
    if not matched_bookmark_path_rel or not os.path.exists(matched_bookmark_path_abs):
        print(f"❌ Bookmark does not exist: '{matched_bookmark_path_rel}'")
        return 1

    if not current_run_settings_obj["is_no_docker_no_redis"]:
        handle_bookmark_redis_states(matched_bookmark_obj, current_run_settings_obj)


    # Take screenshot only if it doesn't exist (skip if no-obs mode)
    print(f"🧪 DEBUG: is_no_obs={current_run_settings_obj['is_no_obs']}, matched_bookmark_path_rel={matched_bookmark_path_rel}, bookmark_dir={matched_bookmark_path_abs}")
    print("🧪 DEBUG: Reached screenshot check for existing bookmark")
    if current_run_settings_obj["is_no_obs"]:
        print(f"📷 No-OBS mode: Skipping screenshot capture")
    else:
        screenshot_path = os.path.join(matched_bookmark_path_abs, "screenshot.jpg")
        if os.path.exists(screenshot_path):
            if IS_DEBUG:
                print(f"📸 Screenshot already exists, preserving: {screenshot_path}")
            print(f"📸 Using existing screenshot: {matched_bookmark_path_rel}/screenshot.jpg")
        else:
            try:
                cl = obs.ReqClient(host="localhost", port=4455, password="", timeout=3)
                response = cl.send("GetSourceScreenshot", {
                    "sourceName": "Media Source",  # TODO: Make configurable if needed
                    "imageFormat": "png"
                })
                image_data = response.image_data
                if image_data.startswith("data:image/png;base64,"):
                    image_data = image_data.replace("data:image/png;base64,", "")

                decoded_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(decoded_bytes))

                # Resize using SCREENSHOT_SAVE_SCALE
                width = int(image.width * SCREENSHOT_SAVE_SCALE)
                height = int(image.height * SCREENSHOT_SAVE_SCALE)
                resized_image = image.resize((width, height))

                # Save resized image
                jpeg_path = os.path.join(matched_bookmark_path_abs, "screenshot.jpg")
                resized_image.save(jpeg_path, format="JPEG", quality=85)

                if IS_DEBUG:
                    print(f"📋 Screenshot saved to: {screenshot_path}")
                print(f"📸 Screenshot saved to: {matched_bookmark_path_rel}/screenshot.jpg")

            except Exception as e:
                print(f"⚠️  1 Could not take screenshot: {e}")
                print(f"   Please ensure OBS is running and WebSocket server is enabled")


    # Get media source info and create bookmark metadata (only if it doesn't exist)
    bookmark_meta_path = os.path.join(matched_bookmark_path_abs, "bookmark_meta.json")
    if not os.path.exists(bookmark_meta_path):
        if current_run_settings_obj["is_no_obs"]:
            # Create minimal metadata without OBS info
            minimal_media_info = {
                'file_path': '',
                'video_filename': '',
                'timestamp': 0,
                'timestamp_formatted': '00:00:00'
            }
            create_bookmark_meta(matched_bookmark_path_abs, matched_bookmark_path_rel, minimal_media_info, current_run_settings_obj["tags"])
            if IS_DEBUG:
                print(f"📋 Created minimal bookmark metadata (no OBS info)")
        else:
            media_info = get_media_source_info()
            if media_info:
                if os.path.exists(matched_bookmark_path_abs):
                    create_bookmark_meta(matched_bookmark_path_abs, matched_bookmark_path_rel, media_info, current_run_settings_obj["tags"])
                    if IS_DEBUG:
                        print(f"📋 Created bookmark metadata with tags: {current_run_settings_obj['tags']}")
                else:
                    print(f"❌ Could not create bookmark metadata - bookmark directory doesn't exist: {matched_bookmark_path_abs}")
                    return 1
    else:
        # If metadata exists and tags were provided, update the tags
        if current_run_settings_obj["tags"]:
            try:
                with open(bookmark_meta_path, 'r') as f:
                    meta_data = json.load(f)

                # Add new tags (avoid duplicates)
                existing_tags = meta_data.get('tags', [])
                for tag in current_run_settings_obj["tags"]:
                    if tag not in existing_tags:
                        existing_tags.append(tag)

                meta_data['tags'] = existing_tags
                meta_data['last_modified'] = datetime.now().isoformat()

                with open(bookmark_meta_path, 'w') as f:
                    json.dump(meta_data, f, indent=2)

                if IS_DEBUG:
                    print(f"📋 Updated existing bookmark metadata with tags: {current_run_settings_obj['tags']}")
            except Exception as e:
                print(f"⚠️  Could not update bookmark metadata with tags: {e}")
        else:
            if IS_DEBUG:
                print(f"📋 Bookmark metadata already exists, skipping creation")

    # Don't update folder metadata for existing bookmarks - only for new ones
    if IS_DEBUG:
        print(f"📋 Skipping folder metadata update for existing bookmark")

    return matched_bookmark_obj
