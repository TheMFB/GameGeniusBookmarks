import os
from PIL import Image

# Constants
NEW_SCREENSHOT_FILENAME = "screenshot.jpeg"
OLD_SCREENSHOT_FILENAME = "screenshot.png"
JPEG_QUALITY = 85


# Dynamically resolve the root directory relative to this script
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(PROJECT_ROOT, "obs_bookmark_saves")

def convert_png_to_jpeg(root_folder):
    converted = 0
    for dirpath, _, filenames in os.walk(root_folder):
        if OLD_SCREENSHOT_FILENAME in filenames:
            png_path = os.path.join(dirpath, OLD_SCREENSHOT_FILENAME)
            jpg_path = os.path.join(dirpath, NEW_SCREENSHOT_FILENAME)

            try:
                with Image.open(png_path) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(jpg_path, format="JPEG", quality=JPEG_QUALITY)
                    print(f"✅ Converted: {png_path} → {jpg_path}")
                os.remove(png_path)
                print(f"🗑️ Deleted: {png_path}")
                converted += 1
            except Exception as e:
                print(f"❌ Failed to convert {png_path}: {e}")

    print(f"\n✅ Done. Converted {converted} PNG screenshot(s) to JPEG.")

if __name__ == "__main__":
    convert_png_to_jpeg(ROOT_DIR)
