from PIL import Image
import os

# Path to your test screenshot
path = "obs_bookmark_saves/test-compression-folder/test-compression-bookmark/screenshot.png"

# Load the image
image = Image.open(path)

# Resize it to 25%
new_width = int(image.width * 0.25)
new_height = int(image.height * 0.25)
resized = image.resize((new_width, new_height))

# Save it back
resized.save(path)

print(f"✅ Resized and saved: {path}")
print(f"📏 New size: {new_width} x {new_height}")
