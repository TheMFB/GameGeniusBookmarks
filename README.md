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
