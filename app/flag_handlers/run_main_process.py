from app.bookmarks_consts import IS_DEBUG, ASYNC_WAIT_TIME
import subprocess
import time

def handle_main_process():
    if IS_DEBUG:
        print(f"🚀 Running main process...")
    print('')
    try:
        cmd = 'docker exec -it game_processor_backend python ./main.py --run-once --gg_user_id="DEV_GG_USER_ID"'
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print("❌ Main process failed")
            return 1

        if IS_DEBUG:
            print(f"⏳ Waiting for async processes to complete...")
        time.sleep(ASYNC_WAIT_TIME)

        return 0
    except Exception as e:
        print(f"❌ Error running main process: {e}")
        return 1
