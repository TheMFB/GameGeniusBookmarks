import os
import re
from pathlib import Path
from codename import codename

VIDEO_DIR = Path(
    "/Volumes/Extreme_Pro/PS5/CREATE/Video Clips/Marvel Rivals/friendly")
VIDEO_EXTENSIONS = {".webm", ".mp4", ".mov", ".mkv"}
INDEX_PREFIX_REGEX = re.compile(r"^\d{4}[_-]")


def get_next_index(existing_files):
    indices = []
    for file in existing_files:
        match = re.match(r"(\d{4})[_\-]", file.name)
        if match:
            indices.append(int(match.group(1)))
    return max(indices, default=0) + 1


def generate_friendly_name(index):
    name = codename().replace('-', '_')  # e.g. 'green_dog'
    name = codename().replace(' ', '_')  # e.g. 'green_dog'
    return f"{index:04d}_{name}"         # e.g. '0001_green_dog'


def rename_videos(directory: Path):
    """
    python3 convert_video_filenames.py

    This script will rename all videos in the specified directory to a format like "0001_green_dog.mp4".
    It will also remove any spaces in the filenames.

    The script will print the old and new filenames for each video that is renamed.

    """
    all_videos = sorted(directory.rglob("*"))
    renamed = []

    existing_indexed = [f for f in all_videos if f.is_file(
    ) and INDEX_PREFIX_REGEX.match(f.name)]
    next_index = get_next_index(existing_indexed)

    for file in all_videos:
        if not file.is_file() or file.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if INDEX_PREFIX_REGEX.match(file.name):
            continue

        new_name = generate_friendly_name(next_index) + file.suffix.lower()
        new_path = file.with_name(new_name)

        print(f"Renaming: {file.name} -> {new_name}")
        os.rename(file, new_path)
        renamed.append((file.name, new_name))
        next_index += 1

    print(f"\n✅ Renamed {len(renamed)} files.")
    return renamed

if __name__ == "__main__":
    if not VIDEO_DIR.exists():
        print(f"❌ Directory does not exist: {VIDEO_DIR}")
    else:
        rename_videos(VIDEO_DIR)
