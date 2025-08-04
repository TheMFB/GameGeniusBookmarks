# import os
# import sys

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from app.bookmarks import find_matching_bookmark


# def test_exact_match():
#     print("Testing exact match...")
#     result = find_matching_bookmark("mock-folder:mock-sub-folder:mock-bookmark-1", "obs_bookmark_saves")
#     print(f"Result: {result}")
#     expected = "mock-folder:mock-sub-folder:mock-bookmark-1"
#     actual = result[0].replace('/', ':')
#     assert actual == expected
#     print("✅ PASSED")


# def test_partial_match():
#     print("Testing partial match...")
#     result = find_matching_bookmark("mock-f:mock-s:mock-bookmark-1", "obs_bookmark_saves")
#     print(f"Result: {result}")
#     expected = "mock-folder:mock-sub-folder:mock-bookmark-1"
#     actual = result[0].replace('/', ':')
#     assert actual == expected
#     print("✅ PASSED")

# if __name__ == "__main__":
#     test_exact_match()
#     test_partial_match()
