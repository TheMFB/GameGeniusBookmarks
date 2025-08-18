# TODO(MFB): Update the usage help and options.
USAGE_HELP = """
Usage: main.py <bookmark_string> [--save-updates] [-s] [--use-preceding-bookmark <folder:bookmark>] [-p <folder:bookmark>] [--blank-slate] [-b] [-v <video_path>] [--open-video <video_path>] [--tags <tag1> <tag2> ...]

Navigation commands:
  next, previous, first, last, last_used/current/again    Navigate to adjacent bookmarks in the same directory
"""

# TODO(MFB): Add an option to show redis before and after diffs.
OPTIONS_HELP = (
    USAGE_HELP
    + """

Options:
  -h, --help, -ls                            Show this help message and exit
    (bmls / lsbm)
  -s, --save-updates                         Save redis state updates (before and after)
    (bmsave / savebm)
  -p <bookmark>, --use-preceding-bookmark    Use redis_after.json from preceding or specified bookmark as redis_before.json
  -d, --dry-run                              Dry run, Load bookmark only (no main process)
  --no-obs                                   No OBS mode, Create bookmarks without OBS connection (for tagging only)
  -b, --blank-slate                          Use initial blank slate Redis state
  --save-last-redis                          Save current Redis state as redis_after.json
  -v <video_path>, --open-video <video_path> Open video file in OBS (paused) without saving or running anything
  -t, --tags <tag1> <tag2> ...              Add tags to bookmark metadata

Navigation:
  next, previous, first, last                Navigate to adjacent bookmarks in the same directory
  last_used                                  (requires a last used bookmark to be set)

Examples:
  main.py my-bookmark
  main.py my-bookmark
  main.py my-bookmark folder:other-bookmark
  main.py my-bookmark --blank-slate
  main.py next -p -s
  main.py previous
  main.py first
  main.py last
  main.py -v /path/to/video.mp4
  main.py --open-video /path/to/video.mp4
  main.py --tags tag1 tag2
  main.py my-bookmark -sd
  main.py my-bookmark --no-obs -t important highlight
"""
)
