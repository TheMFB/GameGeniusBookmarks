from app.bookmarks import fuzzy_match_bookmark_tokens

matches = fuzzy_match_bookmark_tokens("domination")
print("Matches for 'domination':")
for m in matches:
    print(f"  • {m}")
