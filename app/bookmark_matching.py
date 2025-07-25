from app.bookmarks.finder_utils import token_match_bookmarks, fuzzy_match_bookmark_tokens


def find_best_bookmark_match(query, all_bookmarks, folder_dirs):
    """
    Example Target: `GRANDPARENT:PARENT:BOOKMARK -t comp domination`

    """
    # 1. Exact match (full path)
    # Match: `GRANDPARENT:PARENT:BOOKMARK`
    if query in all_bookmarks:
        return [query]

    # 2. Exact match (without some parents)
    # Match: `PARENT:BOOKMARK`
    tail = query.split(":")[-2:]
    for path in all_bookmarks:
        if path.split(":")[-2:] == tail:
            return [path]

    # 3. Substring match (with full path)
    # Match: `GRAND:PAR:MARK`
    substring_matches = [p for p in all_bookmarks if query in p]
    if substring_matches:
        return substring_matches

    # 4. Substring match (without some parents)
    # Match: `PAR:MARK`
    substring_matches = [p for p in all_bookmarks if ":".join(tail) in p]
    if substring_matches:
        return substring_matches

    # 5. Tag/description match
    # (Searches through all names, directories, tags and descriptions -- and does not take order into consideration)
    # Match: `comp:domination:boo`
    tag_matches = token_match_bookmarks(query, folder_dirs)
    if tag_matches:
        return tag_matches

    # 6. Fuzzy match across names, directories, tags and descriptions
    # Match: `GPARENT:DARENT:BOKKMARK`
    fuzzy_matches = fuzzy_match_bookmark_tokens(query)
    if fuzzy_matches:
        return fuzzy_matches


    return []
