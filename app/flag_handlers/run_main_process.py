from app.consts.bookmarks_consts import IS_DEBUG, ASYNC_WAIT_TIME
import subprocess
import time
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True

@print_def_name(IS_PRINT_DEF_NAME)
def handle_main_process(current_run_settings=None):
    if IS_DEBUG:
        print(f"🚀 Running main process...")
    print('')

    # Handle dry and super-dry modes
    is_dry = current_run_settings.get("is_no_docker") if current_run_settings else False
    is_super_dry = current_run_settings.get("is_no_docker_no_redis") if current_run_settings else False

    if is_super_dry:
        print("🛑 Skipping all processing (super-dry mode)")
        return 0

    if is_dry:
        print("💧 Skipping main process (dry mode)")
        return 0

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
