#!/usr/bin/env python3

import os
import sys

# Add the project root to the Python path so we can import from app/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.bookmarks import load_bookmarks_from_folder
from app.bookmarks_folders import get_all_valid_root_dir_names

print("Testing folder detection fix...")
print("=" * 50)

# Test folder detection
active_folders = get_all_valid_root_dir_names()
print(f"Found {len(active_folders)} active folders:")
for folder in active_folders:
    print(f"  📁 {folder}")

print("\n" + "=" * 50)
print("Testing bookmark loading from each folder:")
print("=" * 50)

# Test bookmark loading from each folder
for folder in active_folders:
    folder_name = os.path.basename(folder)
    print(f"\n📁 Loading bookmarks from: {folder_name}")

    bookmarks = load_bookmarks_from_folder(folder)
    print(f"  Found {len(bookmarks)} bookmarks:")

    for bookmark_name, bookmark_info in sorted(bookmarks.items()):
        timestamp = bookmark_info.get('timestamp_formatted', 'unknown')
        print(f"    • {timestamp} - {bookmark_name}")

print("\n" + "=" * 50)
print("Test complete!")