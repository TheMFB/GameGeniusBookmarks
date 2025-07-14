# README
`python -m venv .venv`
`source .venv/bin/activate`
`pip install -r requirements.txt`

# Run

`python ./runonce_redis_integration.py --help`

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
    python ./runonce_redis_integration.py "$@"
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

# Requirements
- loading in an existing bookmark should load that bookmark's redis_before.json into redis, open the video in OBS and then seek to the timestamp, where it will be shown paused.

