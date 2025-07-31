# #!/usr/bin/env python3
# """
# Test script to verify the fixes for the bookmark system issues.
# """
# import os
# import sys

# # Add the app directory to the path
# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, project_root)

# from app.bookmarks import find_matching_bookmark
# from app.bookmarks_folders import find_folder_by_name, parse_cli_bookmark_args
# from app.consts.bookmarks_consts import BOOKMARKS_DIR


# def test_parse_folder_args_for_run_bookmarks():
#     """Test the folder:bookmark parsing function."""
#     print("🧪 Testing parse_cli_bookmark_args...")

#     test_cases = [
#         ("respawn-allies:ra-00-main-screen", ("respawn-allies", "ra-00-main-screen")),
#         ("kerch:comp:m01:01-np", ("kerch", "comp:m01:01-np")),
#         ("test-bookmark", (None, "test-bookmark")),
#         ("folder:sub:book", ("folder", "sub:book")),
#     ]

#     for input_arg, expected in test_cases:
#         result = parse_cli_bookmark_args(input_arg)
#         print(f"  Input: '{input_arg}'")
#         print(f"  Expected: {expected}")
#         print(f"  Got: {result}")
#         print(f"  {'✅ PASS' if result == expected else '❌ FAIL'}")
#         print()

# def test_find_folder_by_name():
#     """Test the folder finding function."""
#     print("🧪 Testing find_folder_by_name...")

#     if not os.path.exists(BOOKMARKS_DIR):
#         print(f"❌ Bookmarks directory not found: {BOOKMARKS_DIR}")
#         return

#     # Get all folders
#     from app.bookmarks_folders import get_all_valid_root_dir_names
#     active_folders = get_all_valid_root_dir_names()

#     print(f"📁 Active folders: {[os.path.basename(f) for f in active_folders]}")

#     test_cases = [
#         "respawn-allies",
#         "kerch",
#         "respawn",  # Should match respawn-allies
#         "nonexistent"
#     ]

#     for folder_name in test_cases:
#         result = find_folder_by_name(folder_name)
#         if result:
#             print(f"  '{folder_name}' -> '{os.path.basename(result)}' ✅")
#         else:
#             print(f"  '{folder_name}' -> Not found ❌")
#     print()

# def test_fuzzy_matching():
#     """Test the fuzzy matching for bookmarks."""
#     print("🧪 Testing fuzzy matching...")

#     if not os.path.exists(BOOKMARKS_DIR):
#         print(f"❌ Bookmarks directory not found: {BOOKMARKS_DIR}")
#         return

#     # Test with a specific folder
#     test_folder = os.path.join(BOOKMARKS_DIR, "respawn-allies")
#     if os.path.exists(test_folder):
#         test_cases = [
#             "ra-00",
#             "ra-00-main-screen",
#             "main-screen",
#             "nonexistent"
#         ]

#         for bookmark_name in test_cases:
#             result, info = find_matching_bookmark(bookmark_name, test_folder)
#             if result:
#                 print(f"  '{bookmark_name}' -> '{result}' ✅")
#             else:
#                 print(f"  '{bookmark_name}' -> Not found ❌")
#     else:
#         print(f"❌ Test folder not found: {test_folder}")
#     print()

# def test_redis_dump_path():
#     """Test the Redis dump directory path resolution."""
#     print("🧪 Testing Redis dump directory path...")

#     from app.consts.bookmarks_consts import REDIS_DUMP_DIR
#     print(f"📁 REDIS_DUMP_DIR: {REDIS_DUMP_DIR}")
#     print(f"📁 Exists: {os.path.exists(REDIS_DUMP_DIR)}")
#     print(f"📁 Is absolute: {os.path.isabs(REDIS_DUMP_DIR)}")
#     print()

# if __name__ == "__main__":
#     print("🔧 Testing bookmark system fixes...")
#     print("=" * 50)

#     test_parse_folder_args_for_run_bookmarks()
#     test_find_folder_by_name()
#     test_fuzzy_matching()
#     test_redis_dump_path()

#     print("✅ Tests completed!")
