from app.bookmarks_consts import IS_DEBUG, OPTIONS_HELP

def open_video(args):
    # Find the index of the open_video flag
    video_flags = ["--open-video", "-v"]
    video_path = None
    for flag in video_flags:
        if flag in args:
            flag_index = args.index(flag)
            # Check if there's an argument after the flag that's not another flag
            if flag_index + 1 < len(args) and not args[flag_index + 1].startswith("-"):
                video_path = args[flag_index + 1]
                if IS_DEBUG:
                    print(f"🔍 Found video path argument: '{video_path}'")
            break

    if not video_path:
        print(f"❌ Video path required for --open-video flag")
        print(OPTIONS_HELP)
        return 1

    print(f"🎬 Opening video in OBS: {video_path}")

    # Import the open_video_in_obs function
    from app.utils import open_video_in_obs

    if open_video_in_obs(video_path):
        print(f"✅ Video opened successfully!")
        return 0
    else:
        print(f"❌ Failed to open video in OBS")
        return 1

    return video_path
