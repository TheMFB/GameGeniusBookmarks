import redis
import pickle
import json
import os
import sys
import glob
from app.bookmarks_consts import LOCAL_REDIS_SESSIONS_HOST, LOCAL_REDIS_SESSIONS_PORT, LOCAL_REDIS_SESSIONS_DB

filename = sys.argv[1] if len(sys.argv) > 1 else "redis_backup"
redis_dump_dir = "./standalone_utils/redis/redis_dump"

# Check if the parameter is "clear" to delete all .json files
if filename == "clear":
    if os.path.exists(redis_dump_dir):
        # Find all .json files in the redis_dump directory (not in subdirectories)
        json_files = glob.glob(os.path.join(redis_dump_dir, "*.json"))

        if json_files:
            print(f"Found {len(json_files)} JSON files to delete:")
            for json_file in json_files:
                print(f"  - {os.path.basename(json_file)}")

            # Delete each JSON file
            for json_file in json_files:
                try:
                    os.remove(json_file)
                    print(f"Deleted: {os.path.basename(json_file)}")
                except Exception as e:
                    print(f"Error deleting {os.path.basename(json_file)}: {e}")

            print(f"Cleared {len(json_files)} JSON files from redis_dump directory")
        else:
            print("No JSON files found in redis_dump directory")
    else:
        print("redis_dump directory does not exist")

    # Exit after clearing files
    sys.exit(0)

# Check if the parameter is "ls" to list all files
if filename == "ls":
    if os.path.exists(redis_dump_dir):
        # Get all files in the redis_dump directory (not in subdirectories)
        all_files = []
        for item in os.listdir(redis_dump_dir):
            item_path = os.path.join(redis_dump_dir, item)
            if os.path.isfile(item_path):
                all_files.append(item)

        if all_files:
            print(f"Files in redis_dump directory ({len(all_files)} total):")

            # Separate and sort by file type
            json_files = sorted([f for f in all_files if f.endswith('.json')])
            pkl_files = sorted([f for f in all_files if f.endswith('.pkl')])
            other_files = sorted([f for f in all_files if not f.endswith('.json') and not f.endswith('.pkl')])

            if json_files:
                print(f"  JSON files ({len(json_files)}):")
                for json_file in json_files:
                    print(f"    - {json_file}")

            if pkl_files:
                print(f"  PKL files ({len(pkl_files)}):")
                for pkl_file in pkl_files:
                    print(f"    - {pkl_file}")

            if other_files:
                print(f"  Other files ({len(other_files)}):")
                for other_file in other_files:
                    print(f"    - {other_file}")
        else:
            print("No files found in redis_dump directory")
    else:
        print("redis_dump directory does not exist")

    # Exit after listing files
    sys.exit(0)

json_filepath = f"{redis_dump_dir}/{filename}.json"
pkl_filepath = f"{redis_dump_dir}/{filename}.pkl"

r = redis.Redis(host=LOCAL_REDIS_SESSIONS_HOST, port=LOCAL_REDIS_SESSIONS_PORT, db=LOCAL_REDIS_SESSIONS_DB)


def safe_decode(value):
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except Exception:
            return value  # fallback to bytes
    return value


def try_json_load(value):
    # Try to decode a string as JSON, otherwise return as-is
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value

data = {}
for key in r.scan_iter('*'):
    key_type = r.type(key)
    if key_type == b'string':
        value = r.get(key)
        if value is not None:
            decoded = safe_decode(value)
            data[key.decode("utf-8")] = try_json_load(decoded)
    else:
        print(
            f"Skipping key {key.decode('utf-8')} of type {key_type.decode('utf-8')}")

os.makedirs("./utils/standalone/redis_dump", exist_ok=True)

# Try to save as JSON, fallback to pickle if it fails
try:
    with open(json_filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Backup saved as {json_filepath} (JSON)")
except Exception as e:
    with open(pkl_filepath, "wb") as f:
        pickle.dump(data, f)
    print(f"Backup saved as {pkl_filepath} (Pickle, reason: {e})")
