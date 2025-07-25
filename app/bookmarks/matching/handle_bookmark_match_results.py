from app.utils.bookmark_utils import convert_exact_bookmark_path_to_dict

def handle_bookmark_match_results(matches: str | list[str] | None):
    """Handle the results of a bookmark match."""
    if not matches:
        return None
    

    
    if isinstance(matches, str):
        return convert_exact_bookmark_path_to_dict(matches)

    print('Handling bookmark match results:')
    print(matches)