import os
import json
from pathlib import Path

CONVERSIONS_FILE = Path("/Volumes/Extreme_Pro/PS5/CREATE/Video Clips/Marvel Rivals/filename_conversions.txt")
BOOKMARKS_ROOT = Path("/Users/mfb/dev/MFBTech/GameGeniusProject/GameGenius/game-genius-bookmarks/obs_bookmark_saves")
DRY_RUN = False  # Set to False to actually write changes

def load_conversion_map(conversions_file):
    mapping = {}
    with open(conversions_file, "r") as f:
        for line in f:
            if "->" in line:
                old, new = line.strip().split(" -> ")
                mapping[old] = new
    return mapping

def update_json_file(json_path, conversion_map):
    with open(json_path, "r") as f:
        try:
            data = json.load(f)
        except Exception:
            return False  # skip non-JSON or broken files

    changed = False
    changes = []

    # Recursively replace in all string values
    def replace_in_obj(obj, path=""):
        nonlocal changed
        if isinstance(obj, dict):
            return {k: replace_in_obj(v, f"{path}.{k}" if path else k) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_in_obj(x, f"{path}[{i}]") for i, x in enumerate(obj)]
        elif isinstance(obj, str):
            orig = obj
            for old, new in conversion_map.items():
                if old in obj:
                    obj = obj.replace(old, new)
            if obj != orig:
                changed = True
                changes.append((path, orig, obj))
            return obj
        return obj

    new_data = replace_in_obj(data)
    if changed:
        print(f"\nWould update: {json_path}")
        for path, old, new in changes:
            print(f"  {path}:")
            print(f"    - {old}")
            print(f"    + {new}")
        if not DRY_RUN:
            with open(json_path, "w") as f:
                json.dump(new_data, f, indent=2)
            print(f"Updated: {json_path}")
    return changed

def main():
    conversion_map = load_conversion_map(CONVERSIONS_FILE)
    for root, dirs, files in os.walk(BOOKMARKS_ROOT):
        for file in files:
            if file.endswith(".json"):
                json_path = Path(root) / file
                update_json_file(json_path, conversion_map)

if __name__ == "__main__":
    main()
