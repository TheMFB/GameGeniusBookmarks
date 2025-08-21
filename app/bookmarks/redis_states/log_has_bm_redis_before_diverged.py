import difflib
import json
import os

from app.bookmarks.navigation.navigation import find_nav_sibling_bookmark_obj_in_folder
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.printing_utils import pprint, print_color

MAX_DIFFS_TO_PRINT = 3


def print_json_diff_with_line_numbers(prev, curr): # type: ignore
    prev_str = json.dumps(prev, indent=2, sort_keys=True)
    curr_str = json.dumps(curr, indent=2, sort_keys=True)
    diff = list(difflib.unified_diff(
        prev_str.splitlines(), curr_str.splitlines(),
        # fromfile='prev_redis_after.json', tofile='current_redis_before.json',
        lineterm=''
    ))

    hunk_count = 0
    printing = False
    for line in diff:
        if line.startswith('@@'):
            hunk_count += 1
            if hunk_count > MAX_DIFFS_TO_PRINT:
                print_color("...(more)", "red")
                break
            printing = True
            print(f"\033[36m{line}\033[0m")  # Cyan for hunk headers
        elif hunk_count == 0:
            # Print file headers and context before first hunk
            print(line)
        elif hunk_count <= MAX_DIFFS_TO_PRINT and printing:
            if line.startswith('-'):
                print(f"\033[31m{line}\033[0m")  # Red for removals
            elif line.startswith('+'):
                print(f"\033[32m{line}\033[0m")  # Green for additions
            else:
                print(line)  # Default color for context


def log_has_bm_redis_before_diverged(matched_bookmark_obj: MatchedBookmarkObj):
    prev_bookmark_obj = find_nav_sibling_bookmark_obj_in_folder(
        matched_bookmark_obj, "previous")

    if not prev_bookmark_obj:
        print("☑️ First bookmark in directory.")
        return


    try:
        current_bookmark_redis_before_path = os.path.join(
            matched_bookmark_obj["bookmark_path_slash_abs"], "redis_before.json")
        prev_bookmark_redis_after_path = os.path.join(
            prev_bookmark_obj["bookmark_path_slash_abs"], "redis_after.json")

        # 2. Load redis state files
        with open(current_bookmark_redis_before_path) as f:
            current_redis = json.load(f)
        with open(prev_bookmark_redis_after_path) as f:
                prev_redis = json.load(f)

        # 3. Deep compare
        if current_redis != prev_redis:
            print("❌ Redis state has diverged from previous bookmark.")
            diff = print_json_diff_with_line_numbers(
                prev_redis, current_redis)
            pprint(diff)
        else:
            print("✅ Redis state matches previous bookmark.")

    except Exception as e:
        print(f"❌ Error logging has_bm_redis_before_diverged: {e}")
        return

