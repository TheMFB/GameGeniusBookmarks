
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def compute_hoistable_tags(list_of_tag_sets):
    """Given a list of tag sets (one per bookmark), return the set of tags shared by all -- in order to bring them up to the next parent folder"""
    if not list_of_tag_sets:
        return set()
    return set.intersection(*list_of_tag_sets)


# # Not Currently Used
# # This is loaded for all bookmarks to create a tree of bookmarks and tags.
# @print_def_name(False)
# def collect_all_bookmark_tags_recursive(node):
#     """
#     Recursively gather all tags from bookmarks inside a folder.
#     This is loaded for all bookmarks to create a tree of bookmarks and tags.
#     """
#     all_tags = []

#     for _key, value in node.items():
#         if isinstance(value, dict):
#             if value.get('type') == 'bookmark':
#                 all_tags.append(set(value.get('tags', [])))
#             else:
#                 # Recurse into sub_dir
#                 all_tags.extend(collect_all_bookmark_tags_recursive(value))

#     return all_tags
