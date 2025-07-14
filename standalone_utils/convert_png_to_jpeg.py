import os
from PIL import Image

# Path to the root directory containing bookmark folders
ROOT_DIR = "/Users/kerch/dev/GameGeniusBookmarks/obs_bookmark_saves"
SCREENSHOT_FILENAME = "screenshot.png"
JPEG_QUALITY = 85

def convert_png_to_jpeg(root_folder):
    converted = 0
    for dirpath, _, filenames in os.walk(root_folder):
        if SCREENSHOT_FILENAME in filenames:
            png_path = os.path.join(dirpath, SCREENSHOT_FILENAME)
            jpg_path = os.path.join(dirpath, "screenshot.jpg")

            try:
                with Image.open(png_path) as img:
                    # Ensure RGB mode for JPEG
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    # Save as JPEG (same size as existing PNG)
                    img.save(jpg_path, format="JPEG", quality=JPEG_QUALITY)
                    print(f"✅ Converted: {png_path} → {jpg_path}")

                # Delete original PNG
                os.remove(png_path)
                print(f"🗑️ Deleted: {png_path}")
                converted += 1
            except Exception as e:
                print(f"❌ Failed to convert {png_path}: {e}")

    print(f"\n✅ Done. Converted {converted} PNG screenshot(s) to JPEG.")

if __name__ == "__main__":
    convert_png_to_jpeg(ROOT_DIR)
