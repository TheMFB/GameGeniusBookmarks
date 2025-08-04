import os
import re
from pathlib import Path

from codename import codename

VIDEO_DIR = Path(
    "/Volumes/Extreme_Pro/PS5/CREATE/Video Clips/Marvel Rivals")
VIDEO_EXTENSIONS = {".webm", ".mp4", ".mov", ".mkv"}
INDEX_PREFIX_REGEX = re.compile(r"^\d{4}[_-]")


def get_next_index(existing_files):
    indices = []
    for file in existing_files:
        match = re.match(r"(\d{4})[_\-]", file.name)
        if match:
            indices.append(int(match.group(1)))
    return max(indices, default=0) + 1


MARVEL_PREFIX = "Marvel Rivals_"
DATE_ID_REGEX = re.compile(r"^(\d{14})(?:_([^.]+))?$")  # 14 digits, optional _text

def generate_friendly_name(index, file: Path):
    name = file.stem
    # Remove Marvel prefix if present
    if name.startswith(MARVEL_PREFIX):
        name = name[len(MARVEL_PREFIX):]
    # Check for date id and optional text
    match = DATE_ID_REGEX.match(name)
    if match:
        _date_id, extra = match.groups()
        if extra:
            friendly = extra.replace(' ', '_')
        else:
            friendly = codename().replace('-', '_').replace(' ', '_')
    else:
        # Use the rest of the filename, spaces to underscores
        friendly = name.replace(' ', '_')
    return f"{index:04d}_{friendly}"


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
        if file.name.startswith("._"):  # <-- skip AppleDouble files
            continue
        if INDEX_PREFIX_REGEX.match(file.name):
            continue

        new_name = generate_friendly_name(next_index, file) + file.suffix.lower()
        new_path = file.with_name(new_name)

        print(f"Renaming: {file.name} -> {new_name}")
        os.rename(file, new_path)
        renamed.append((file.name, new_name))
        next_index += 1

    # Save conversions to file
    conversions_file = directory / "filename_conversions.txt"
    # Read existing conversions if file exists
    # TODO(?): These lines were unused...
    # existing_lines = []
    # if conversions_file.exists():
    #     with open(conversions_file, "r") as f:
    #         existing_lines = f.readlines()
    # Prepare new lines
    new_lines = [f"{old} -> {new}\n" for old, new in renamed]
    # Write all lines back (existing + new)
    with open(conversions_file, "a") as f:
        f.writelines(new_lines)

    print(f"\n✅ Renamed {len(renamed)} files.")
    print(f"📝 Conversion log updated: {conversions_file}")
    return renamed

if __name__ == "__main__":
    if not VIDEO_DIR.exists():
        print(f"❌ Directory does not exist: {VIDEO_DIR}")
    else:
        rename_videos(VIDEO_DIR)
