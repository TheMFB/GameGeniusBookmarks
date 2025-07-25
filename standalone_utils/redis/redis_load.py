import pickle
import json
import sys
import os
import redis
from app.bookmarks_consts import LOCAL_REDIS_SESSIONS_HOST, LOCAL_REDIS_SESSIONS_PORT, LOCAL_REDIS_SESSIONS_DB


filename = sys.argv[1] if len(sys.argv) > 1 else "redis_backup"
json_filepath = f"./standalone_utils/redis/redis_dump/{filename}.json"
pkl_filepath = f"./standalone_utils/redis/redis_dump/{filename}.pkl"

r = redis.Redis(host=LOCAL_REDIS_SESSIONS_HOST,
                port=LOCAL_REDIS_SESSIONS_PORT, db=LOCAL_REDIS_SESSIONS_DB)

# Wipe the database before restoring
r.flushdb()
print("Redis database wiped.")

data = None
if os.path.exists(json_filepath):
    try:
        with open(json_filepath, "r") as f:
            data = json.load(f)
        print(f"Loaded backup from {json_filepath} (JSON)")
    except Exception as e:
        print(f"Failed to load JSON: {e}")

if data is None and os.path.exists(pkl_filepath):
    with open(pkl_filepath, "rb") as f:
        data = pickle.load(f)
    print(f"Loaded backup from {pkl_filepath} (Pickle)")

if data is None:
    print("No backup file found or failed to load.")
    sys.exit(1)

session_ids = set()

for key, value in data.items():
    if key.startswith('user_session'):
        session_ids.add(value)
    # If value is a dict or list, encode as JSON string
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    # If value is not bytes, encode as utf-8
    if not isinstance(value, bytes):
        value = str(value).encode('utf-8')
    r.set(key, value)
    # TODO(MFB): Loop through all of these and publish each...?


print("Redis data restored!")
