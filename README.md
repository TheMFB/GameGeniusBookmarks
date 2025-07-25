# README

`python -m venv .venv`
`source .venv/bin/activate`
`pip install -r requirements.txt`

# Run

`python ./main.py --help`

# .ENV File

Be sure to add the following as a '.env' file in the root of GameGeniusBookmarks:

```
VIDEO_PATH="/Volumes/GG_SSD/PS5/CREATE/Video Clips/Marvel Rivals"
GAME_GENIUS_DIRECTORY="/Users/kerch/dev/GameGenius"
```

# Aliases:

```
# Bookmark and Run Once
bookmark() {
    printf "\033]1;runonce-redis\a"
    printf "\033]1337;SetUserVar=ggsession=runonce-redis\a"
    # clear
    # printf "\033c"
    printf "\033]50;ClearScrollback\a"
    last_cmd=$(fc -ln -1)
    echo -e "\033[1;36m> bookmark $@\033[0m"
    cd ~/dev/MFBTech/GameGeniusProject/GameGenius/game-genius-bookmarks/
    source .venv/bin/activate
    python ./main.py "$@"
}
bm() { bookmark "$@"; }

# Add Bookmark
addbm() { bookmark "$@" --add; }
bmadd() { bookmark "$@" --add; }

# List Bookmarks
bmls() { bookmark -ls; }
lsbm() { bookmark -ls; }

# Load Bookmark / Dry Run
loadbm() { bookmark "$@" -d; }
bmload() { bookmark "$@" -d; }
drybm() { bookmark "$@" -d; }
bmdry() { bookmark "$@" -d; }

# Save the results of Bookmark (redis after processing)
bmsave() { bookmark "$@" -s; }

# Open Video's Path in OBS
obsload() { bookmark "$@" -v; }
obsopen() { bookmark "$@" -v; }
openobs() { bookmark "$@" -v; }

```

# Glossary
- `bookmark_dir` -> the entire path except for the bookmark name
- `bookmark_tail_name` -> the bookmark name that is found at the end of the path
- `bookmark_path` -> the whole directory including the name
- `hoist` -> siblings that all share the same tag will just be displayed in the parent as a "grouped tag".


# Features





## Searching

- `ls` (and all other bookmark matching) will support the following in order:
Example: `GRANDPARENT:PARENT:BOOKMARK -t comp domination`

-- exact matches
`GRANDPARENT:PARENT:BOOKMARK`

-- exact matches (but with parent directories removed)
`PARENT:BOOKMARK`

-- substring matching
`GRAND:PAR:MARK`

-- substring matching (but with parent directories removed)
`PAR:MARK`

-- tag searching (Searches through all names, directories, tags and descriptions -- and does not take order into consideration)
`comp:domination:boo`

-- all of the above, but with fuzzy matching across names, directories, tags and descriptions.
`GPARENT:DARENT:BOKKMARK`

If there is a single hit on any of these, we stop. If there is none, we go to the next step. If there are multiple, we list the options and prompt the user for action.


## Flags

Note that anything with "routed" here will only do what is asked of it and will not run anything else.

### Help (routed)

Will list out the current bookmark tree as we do with a blank ls and also show the help text showing the potential flags


### ls/which (routed)

- Lists all of the current bookmarks in the system. (ignoring excluded directories)
- tree system of the parent dir, sub-dir, etc. ending with bookmark (folder)
- All of the dirs will be prefaced with a "📁" icon, and all bookmarks with a "📖".
- All tags will be displayed appropriately. More info on logic below.
    - If all siblings of a bookmark/dir contain the same tag, that tag will be "grouped" by not being displayed on the siblings, but will be displayed on the parent. This also applies to grouped tags, so if all dirs have the same tag/grouped tag, it will continue to be promoted to the next level.
- For each bookmark, we will display in "invisible ink" the full colon-separated relative directory.
- Each bookmark and folder also include hidden within the emoji, which will allow the user to cmd+click to open that file in VSCode/Cursor (when set-up properly)
- The currently selected (or last selected) bookmark will be displayed at the bottom of the screen with the full colon-separated relative path.
- When being displayed in the tree-view, if the directory/bookmark matches the current/last selected bookmark (or is included in it's direct folder-tree), those directories/bookmark will be color-coded appropriately, with the final bookmark name being tagged with "(current)"

- When ls or which is followed by a bookmark string, we will display the matches that the system would show. Nothing will be run other than this.

### open-video (routed)

- will be followed by a video-name or the absolute video path. This will load this video into OBS and will not do anything else.

### navigation

When a bookmark name is expected, but instead any of the reserved words are used -- first, last, previous, next.
- if the cli bookmark is not given, but rather one of the above, we will find the respective sibling for the last-selected-bookmark.
- if a cli bookmark is given, and one of these reserved words are used, these words will be with respect to the cli-bookmark (and not the last-selected-bookmark) e.g. `bm test:TEST:03 -p first` will use the first bookmark of `test:TEST` as a base for the selected bookmark's redis-before.

### Add

(Is this used? - I think this is to default to creating a new bookmark with what is given to the terminal. Maybe an exact match.)

### Use Preceding

If just this is used, we will find the selected sibling's bookmark that comes directly before it, take it's redis_afters and use that as the selected sibling's redis_before (and saving them). If a bookmark string comes after this flag, we will use the bookmark found there's redis_afters to populate our selected bookmark's redis_before(s).

### Blank Slate

Instead of pulling from the current redis state, we will load in the default initial redis state for the redis before.

### Dry Run

Runs everything except for Docker (gg-engine)

### Super Dry Run

Runs everything except for Docker (gg-engine) and Redis ()

### No OBS

Does not interact with OBS - Does not load video, seek to position, nor does it access the screenshot. Often used with dry-run to just do tagging.

### Save last redis (save redis after)

Updates the save-redis-after after running the process. Default is to keep the original.

### Save Redis before

Updates the redis-before. This is akin to just re-creating the bookmark, but does not update the redis-after if it exists.

### Save Updates

Does both the save before and after updates -- basically recreates the bookmark from scratch ( -- should it overwrite the image too?)

### Show Image

Option to show the thumbnail screenshot of the bookmarks when displaying. Might need tweaks to when we display them, as displaying ALL of them might take a ton of terminal display.

### Tags

* We will have different levels of tags, but at the moment it is just the bottom level (--tags / -t)

When defined, it will add that tag to the selected bookmark when run.


## Tag Logic

During the get_all_valid_bookmarks_in_json_format() step, we hoist all grouped tags so that they appear to belong to the top-most applicable parent (where all descendants share that tag). Note that this will only go up to the root level - if ALL bookmarks in the system has a bookmark, it will be displayed in each root folder.

📁 videos
   📁 0001_green_dog
      Marvel Rivals_20250103230835-disconnect but no startup copy
      📁 g01
         📁 m01
            • 10:04 📖 00-main-menu   videos:0001_green_dog:g01:m01:00-main-menu
               🏷️ •main_menu
            • 10:18 📖 01-np   videos:0001_green_dog:g01:m01:01-np
               🏷️ •test
            • 10:49 📖 02-css   videos:0001_green_dog:g01:m01:02-css
            • 11:11 📖 03-in-spawn   videos:0001_green_dog:g01:m01:03-in-spawn
            • 11:39 📖 04-about-to-leave-spawn   videos:0001_green_dog:g01:m01:04-about-to-leave-spawn
