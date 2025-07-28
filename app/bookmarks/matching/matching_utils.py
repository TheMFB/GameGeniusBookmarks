import os
import re
import difflib

from app.bookmarks_consts import IS_DEBUG
from app.bookmarks.bookmarks import load_bookmarks_from_folder, get_all_live_bookmarks_in_json_format
from app.types.bookmark_types import MatchedBookmarkObj
from app.utils.printing_utils import *
from app.utils.decorators import print_def_name, memoize
from app.utils.bookmark_utils import split_path_into_array, does_path_exist_in_bookmarks, convert_exact_bookmark_path_to_dict

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def stepwise_match(user_parts, all_saved_bookmark_paths):
    """Perform reverse stepwise matching of user_parts against bookmark paths."""
    # Preprocess all bookmarks into tokenized forms
    tokenized_bookmarks = [
        (path, split_path_into_array(path)) for path in all_saved_bookmark_paths
    ]

    # Start by finding matches on the last user input part
    depth = 1  # start from end of user input
    while True:
        matching = []
        for orig_path, tokens in tokenized_bookmarks:
            if len(tokens) < depth:
                continue
            if tokens[-depth].startswith(user_parts[-depth]):
                matching.append((orig_path, tokens))

        if not matching:
            return []  # no matches at this depth — fail
        if depth == len(user_parts):
            return [m[0] for m in matching]  # all user parts matched
        if len(matching) == 1:
            return [matching[0][0]]  # only one left — use it

        # More than one match, keep going deeper
        tokenized_bookmarks = matching
        depth += 1

@print_def_name(IS_PRINT_DEF_NAME)
def find_matching_bookmarks(bookmark_path_rel, root_dir_name):
    """
    Find all matching bookmarks using step-through logic and fallback fuzzy matching.
    Returns a list of (bookmark_path, bookmark_info) tuples.
    """
    all_bookmark_objects = load_bookmarks_from_folder(root_dir_name)
    if not all_bookmark_objects:
        return [(None, None)]

    all_saved_bookmark_paths = list(all_bookmark_objects.keys())
    matches = []

    # First try exact match
    if bookmark_path_rel in all_saved_bookmark_paths:
        if IS_DEBUG:
            print(f"🎯 Found exact bookmark_path_rel match: '{bookmark_path_rel}'")
        return (bookmark_path_rel, all_bookmark_objects[bookmark_path_rel])

    # Normalize user input
    user_cli_input_parts = split_path_into_array(bookmark_path_rel)
    if IS_DEBUG:
        print(f"🔎 Normalized user input: {user_cli_input_parts}")

    # Try stepwise matching
    stepwise_matches = stepwise_match(
        user_cli_input_parts, all_saved_bookmark_paths)
    if stepwise_matches:
        for match in stepwise_matches:
            matches.append((match, all_bookmark_objects[match]))
        return matches

    # Fallback fuzzy match (with scoring)
    normalized_input = bookmark_path_rel.lower()
    scored_matches = []
    for path, info in all_bookmark_objects.items():
        path_lower = path.lower()
        tokens = set(path_lower.replace('/', ' ').replace('-', ' ').split())
        input_tokens = set(normalized_input.replace(
            '/', ' ').replace('-', ' ').split())
        score = len(tokens & input_tokens)
        if score > 0:
            scored_matches.append((score, path, info))
    if scored_matches:
        # Sort by score descending, then path
        scored_matches.sort(key=lambda x: (-x[0], x[1]))
        for _, path, info in scored_matches:
            matches.append((path, info))
        return matches

    # No matches found
    return [(None, None)]


@print_def_name(IS_PRINT_DEF_NAME)
def is_exact_bookmark_path_in_live_bookmarks(bookmark_obj):
    """
    Return exact match path if the normalized bookmark path matches cli_bookmark_string.
    Used during creation to avoid fuzzy fallbacks.

    "active" -> "live"
    """
    cli_bookmark_path_rel = bookmark_obj["bookmark_dir_colon_rel"]
    all_bookmarks_object = get_all_live_bookmarks_in_json_format()

    if not all_bookmarks_object:
        return False

    return does_path_exist_in_bookmarks(all_bookmarks_object, cli_bookmark_path_rel)

# TODO(MFB): Bugfix

@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def token_match_bookmarks(query_string, folder_dir):
    """
    Returns a list of bookmark paths where all cli_bookmark_string tokens appear in the path.
    """
    all_bookmark_objects = load_bookmarks_from_folder(folder_dir)
    if not all_bookmark_objects:
        return []

    query_tokens = set(query_string.lower().replace(
        ":", " ").replace("/", " ").split())
    matches = []

    for path in all_bookmark_objects.keys():
        path_tokens = set(re.split(r"[-_/]", path.lower()))
        if query_tokens.issubset(path_tokens):
            matches.append(path)

    return matches

# TODO(MFB): Bugfix


@print_def_name(IS_PRINT_DEF_NAME)
@memoize
def build_bookmark_token_map(include_tags_and_descriptions=True):
    """
    Return a dict mapping each bookmark path to a token set for matching.

    This should go through all of the live bookmark paths and build a token map for each bookmark. All tags and descriptions of the bookmarks' ancestors should apply to the bookmark.
    """
    bookmark_token_map = {}
    all_bookmarks_json = get_all_live_bookmarks_in_json_format()

    def walk(node, path_parts, ancestor_tags, ancestor_descriptions):
        # Gather tags and description at this node
        tags = set(ancestor_tags)
        descriptions = list(ancestor_descriptions)
        if 'tags' in node:
            tags.update([t.lower() for t in node['tags']])
        if 'description' in node and node['description']:
            descriptions.append(node['description'].lower())

        # If this is a bookmark node
        if node.get('type') == 'bookmark':
            bookmark_path = '/'.join(path_parts)
            tokens = set()
            # Path parts (split on / and -)
            for part in path_parts:
                tokens.update(part.lower().split('-'))
            # Tags
            if include_tags_and_descriptions:
                tokens.update(tags)
                for desc in descriptions:
                    tokens.update(desc.split())
            bookmark_token_map[bookmark_path] = {
                "tokens": tokens,
                "bookmark_name": path_parts[-1] if path_parts else "",
                "folder_name": path_parts[-2] if len(path_parts) > 1 else "",
            }
        else:
            # Recurse into children
            for key, child in node.items():
                if key in ('tags', 'description', 'type', 'timestamp', 'video_filename'):
                    continue
                walk(child, path_parts + [key], tags, descriptions)

    for root_name, root_node in all_bookmarks_json.items():
        walk(root_node, [root_name], set(), [])

    return bookmark_token_map




# @print_def_name(IS_PRINT_DEF_NAME)
# def fuzzy_match_bookmark_tokens(cli_bookmark_string: str, include_tags_and_descriptions: bool = True, top_n: int = 5):
#     token_map = build_bookmark_token_map(include_tags_and_descriptions)
#     query_tokens = set(cli_bookmark_string.lower().split())

#     scored_matches = []

#     for key, data in token_map.items():
#         overlap = data["tokens"].intersection(query_tokens)
#         score = len(overlap)
#         query_lower = cli_bookmark_string.lower()

#     # Boost if bookmark name starts with cli_bookmark_string
#     if data["bookmark_name"].lower().startswith(query_lower):
#         score += 10  # strong boost

#     # Boost if folder name starts with cli_bookmark_string
#     if data["folder_name"].lower().startswith(query_lower):
#         score += 5  # moderate boost

#     if score > 0:
#         print(f"{key} -> match score: {score}, overlap: {overlap}")
#         scored_matches.append((score, key))

#     # Sort by score descending, then alphabetically by key
#     scored_matches.sort(key=lambda x: (-x[0], x[1]))

#     top_matches = [match[1] for match in scored_matches[:top_n]]
#     return top_matches

# TODO(MFB): Not used.
# @print_def_name(IS_PRINT_DEF_NAME)
# def interactive_fuzzy_lookup(cli_bookmark_string: str, top_n: int = 5):
#     """
#     Perform fuzzy matching and ask user to choose a bookmark from the top N matches.
#     Returns the selected bookmark path, or None if cancelled.
#     """
#     matches = fuzzy_match_bookmark_tokens(cli_bookmark_string, top_n=top_n)

#     if not matches:
#         print("❌ No matches found.")
#         return None

#     print(f"🤔 Fuzzy matches for '{cli_bookmark_string}':")
#     for idx, match in enumerate(matches, 1):
#         print(f"  {idx}. {match}")
#     print("  0. Cancel")

#     while True:
#         try:
#             choice = input(f"Enter your choice (1-{len(matches)} or 0 to cancel): ").strip()
#             if choice == "0":
#                 print("❌ Cancelled.")
#                 return None
#             choice_num = int(choice)
#             if 1 <= choice_num <= len(matches):
#                 selected = matches[choice_num - 1]
#                 print(f"✅ Selected: {selected}")
#                 return selected
#             else:
#                 print(f"❌ Invalid input. Choose between 0 and {len(matches)}.")
#         except ValueError:
#             print("❌ Please enter a number.")


@print_def_name(IS_PRINT_DEF_NAME)
def interactive_choose_bookmark(matched_bookmark_strings: list[str]) -> str | None:
    """
    Ask the user to choose a bookmark from a list of matches.
    """
    print("🤔 Multiple results found:")
    for idx, match in enumerate(matched_bookmark_strings):
        print(f"  {idx + 1}. {match}")
    print("  0. Cancel")

    while True:
        try:
            choice = input(f"Enter your choice (1-{len(matched_bookmark_strings)} or 0 to cancel): ").strip()
            if choice == "0":
                print("❌ Cancelled.")
                return None
            choice_num = int(choice)
            if 1 <= choice_num <= len(matched_bookmark_strings):
                selected = matched_bookmark_strings[choice_num - 1]
                print(f"✅ Selected: {selected}")
                return selected
            else:
                print(
                    f"❌ Invalid input. Choose between 0 and {len(matched_bookmark_strings)}.")
        except ValueError:
            print("❌ Please enter a number.")


@print_def_name(IS_PRINT_DEF_NAME)
def handle_bookmark_matches(matched_bookmark_strings: list[str]) -> MatchedBookmarkObj | int | None:
    """
    Handle the results of a bookmark match.
    """
    if not matched_bookmark_strings:
        return 1

    if len(matched_bookmark_strings) == 1:
        return convert_exact_bookmark_path_to_dict(matched_bookmark_strings[0])
    else:
        chosen_bookmark_string = interactive_choose_bookmark(matched_bookmark_strings)
        if chosen_bookmark_string:
            return convert_exact_bookmark_path_to_dict(chosen_bookmark_string)
        else:
            return 1


@print_def_name(IS_PRINT_DEF_NAME)
def find_bookmarks_by_exact_trailing_live_bm_path_parts(cli_bookmark_string, all_live_bookmark_path_slash_rels):
    """
    Find all bookmarks where the last N path parts match the input, in order.
    Example:
      cli_bookmark_string: "PARENT:BOOKMARK"
      all_live_bookmark_path_slash_rels: ["GRANDPARENT/PARENT/BOOKMARK", "OTHER/PARENT/BOOKMARK", "PARENT/BOOKMARK", "GRANDPARENT/BOOKMARK"]
      Returns: ["GRANDPARENT/PARENT/BOOKMARK", "OTHER/PARENT/BOOKMARK", "PARENT/BOOKMARK"]
    """
    # Convert input to list of parts
    cli_input_parts = cli_bookmark_string.replace(":", "/").split("/")
    matches = []
    for path in all_live_bookmark_path_slash_rels:

        live_bm_path_parts = path.split("/")
        if len(live_bm_path_parts) >= len(cli_input_parts) and live_bm_path_parts[-len(cli_input_parts):] == cli_input_parts:
            matches.append(path)
    return matches


@print_def_name(IS_PRINT_DEF_NAME)
def find_bookmarks_by_substring_with_all_live_bm_path_parts(cli_bookmark_string, all_live_bookmark_path_slash_rels):
    """
    Find all bookmarks where the input is a substring of the path.
    Example:
        cli_bookmark_string: "PAR:PAR:MARK"
        all_live_bookmark_path_slash_rels: [
            "GRANDPARENT_1/PARENT_1/BOOKMARK_1",
            "GRANDPARENT_2/PARENT_2/BOOKMARK_2",
            "PARENT_3/PARENT_2/BOOKMARK_2",
            "OTHER_1/PARENT_1/BOOKMARK_1",
            ]

        Returns: [
            "GRANDPARENT_1/PARENT_1/BOOKMARK_1",
            "GRANDPARENT_2/PARENT_2/BOOKMARK_2",
            "PARENT_3/PARENT_2/BOOKMARK_2",
            ]
    """
    # Convert input to list of parts
    cli_input_parts = cli_bookmark_string.replace(":", "/").split("/")
    matches = []
    for live_bm_path in all_live_bookmark_path_slash_rels:
        live_bm_path_parts = live_bm_path.split("/")
        if len(live_bm_path_parts) == len(cli_input_parts):
            if all(cli_input_parts[i] in live_bm_path_parts[i] for i in range(len(live_bm_path_parts))):
                matches.append(live_bm_path)
    return matches

@print_def_name(IS_PRINT_DEF_NAME)
def find_bookmarks_by_substring_with_trailing_live_bm_path_parts(cli_bookmark_string, all_live_bookmark_path_slash_rels):
    """
    Find all bookmarks where the input is a substring of the path.
    Example:
        cli_bookmark_string: "PAR:MARK"
        all_live_bookmark_path_slash_rels: [
            "GRANDPARENT_1/PARENT_1/BOOKMARK_1",
            "GRANDPARENT_2/2_PARENT_2/BOOKMARK_2",
            "PARENT_3/PARENT_2/BOOKMARK_2",
            "OTHER_1/OTHER_2/BOOKMARK_1",
            ]

        Returns: [
            "GRANDPARENT_1/PARENT_1/BOOKMARK_1",
            "GRANDPARENT_2/2_PARENT_2/BOOKMARK_2",
            "PARENT_3/PARENT_2/BOOKMARK_2",
            ]
    """
    # Convert input to list of parts
    cli_input_parts = cli_bookmark_string.replace(":", "/").split("/")
    matches = []


    for live_bm_path in all_live_bookmark_path_slash_rels:
        live_bm_path_parts = live_bm_path.split("/")
        if len(live_bm_path_parts) >= len(cli_input_parts):
            is_match = True
            for i in range(1, len(cli_input_parts) + 1):
                cli_part = cli_input_parts[-i]
                live_part = live_bm_path_parts[-i]

                # Debug prints here if needed
                if cli_part not in live_part:
                    is_match = False
                    break
            if is_match:
                matches.append(live_bm_path)

    return matches


@print_def_name(IS_PRINT_DEF_NAME)
def find_exact_matches_by_bookmark_tokens(
    cli_bookmark_string: str,
    include_tags_and_descriptions: bool = True,
) -> list[str]:
    """
    Find partial matches by bookmark tokens.

    This will look to see if all of the cli_bookmark_string parts are found in any of the bookmark tokens.
    - Bookmark path parts
    - Tags
    - Description
   
    """
    token_map = build_bookmark_token_map(include_tags_and_descriptions)
    # TODO(MFB): Add an option to be case-(in)sensitive

    query_tokens = set(cli_bookmark_string.lower().split(':'))
    matches = []

    for live_bm_path_slash_rel, live_bm_token_data in token_map.items():
        is_match = True
        for query_token in query_tokens:
            if query_token not in live_bm_token_data["tokens"]:
                is_match = False
                break
        if is_match:
            matches.append(live_bm_path_slash_rel)

    return matches

@print_def_name(IS_PRINT_DEF_NAME)
def find_partial_substring_matches_by_bookmark_tokens(
    cli_bookmark_string: str,
    include_tags_and_descriptions: bool = True,
) -> list[str]:
    """
    Find partial matches by bookmark tokens.

    This will look to see if all of the cli_bookmark_string parts are found in any of the bookmark tokens.
    - Bookmark path parts
    - Tags
    - Description

    """
    token_map = build_bookmark_token_map(include_tags_and_descriptions)
        # TODO(MFB): Add an option to be case-(in)sensitive

    query_tokens = set(cli_bookmark_string.lower().split(':'))
    matches = []

    for live_bm_path_slash_rel, live_bm_token_data in token_map.items():
        is_match = True
        for query_token in query_tokens:
            if query_token not in live_bm_token_data["tokens"]:
                is_match = False
                break
        if is_match:
            matches.append(live_bm_path_slash_rel)

    return matches

# @print_def_name(IS_PRINT_DEF_NAME)
# def find_fuzzy_matches_by_bookmark_tokens(
#     cli_bookmark_string: str,
#     include_tags_and_descriptions: bool = True,
#     min_ratio: float = 0.8,  # Tolerance: 0.0 (very fuzzy) to 1.0 (exact)
# ) -> list[str]:
#     """
#     Find fuzzy matches by bookmark tokens, allowing for small typos.
#     """
#     token_map = build_bookmark_token_map(include_tags_and_descriptions)
#     import re
#     query_tokens = set(re.split(r'[:\\s]+', cli_bookmark_string.lower()))
#     matches = []

#     for live_bm_path_slash_rel, live_bm_token_data in token_map.items():
#         is_match = True
#         for query_token in query_tokens:
#             found = any(
#                 difflib.SequenceMatcher(None, query_token, bm_token).ratio() >= min_ratio
#                 for bm_token in live_bm_token_data["tokens"]
#             )
#             if not found:
#                 is_match = False
#                 break
#         if is_match:
#             matches.append(live_bm_path_slash_rel)

#     return matches

