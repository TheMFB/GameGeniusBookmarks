from app.utils.bookmark_utils import convert_exact_bookmark_path_to_dict

def handle_bookmark_match_results(matches: str | list[str] | None):
    """Handle the results of a bookmark match."""
    if not matches:
        return None




    if isinstance(matches, str):
        return convert_exact_bookmark_path_to_dict(matches)

    print('Handling bookmark match results:')
    print(matches)


    #         # We have an exact match, prompt the user what to do with the Redis saves
    #         print(
    #             f"⚠️ Bookmark already exists: {cli_bookmark_obj["bookmark_dir_colon_rel"]}")
    #         print("What would you like to do?")
    #         print("  1. Load existing")
    #         print("  2. Overwrite before redis")
    #         print("  3. Overwrite after redis")
    #         print("  4. Overwrite both")
    #         print("  5. Cancel")
    #         while True:
    #             choice = input("Enter choice (1–5): ").strip()
    #             if choice == "1":
    #                 matched_bookmark_obj = get_bookmark_info(cli_bookmark_obj)
    #                 break
    #             elif choice == "2":
    #                 matched_bookmark_obj = cli_bookmark_obj
    #                 current_run_settings_obj["is_overwrite_redis_before"] = True
    #                 break
    #             elif choice == "3":
    #                 matched_bookmark_obj = cli_bookmark_obj
    #                 current_run_settings_obj["is_overwrite_redis_after"] = True
    #                 break
    #             elif choice == "4":
    #                 matched_bookmark_obj = cli_bookmark_obj
    #                 current_run_settings_obj["is_overwrite_redis_after"] = True
    #                 current_run_settings_obj["is_overwrite_redis_before"] = True
    #                 break
    #             elif choice == "5":
    #                 print("❌ Cancelled.")
    #                 return 1
    #             else:
    #                 print("❌ Invalid choice. Please enter 1–5.")
