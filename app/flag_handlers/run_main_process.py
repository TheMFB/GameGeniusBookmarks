import subprocess
import time

from app.consts.bookmarks_consts import ASYNC_WAIT_TIME, IS_DEBUG
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_main_process(current_run_settings=None):
    """
    Handle the running main process.
    """

    # Handle dry and no docker, no redis modes
    is_no_docker_no_redis = (current_run_settings.get(
        "is_no_docker_no_redis") or current_run_settings.get("is_no_docker")) if current_run_settings else False
    if is_no_docker_no_redis:
        print("🛑 Skipping all processing (no docker, no redis)")
        return 0

    # Dry Mode
    is_dry = current_run_settings.get(
        "is_no_saving_dry_run") if current_run_settings else False
    if is_dry:
        print("💧 Skipping main process (dry mode)")
        return 0

    print('')
    print("🚀 Running main process...")

    try:
        cmd = 'docker exec -it game_processor_backend python ./main.py --run-once --gg_user_id="DEV_GG_USER_ID"'
        result = subprocess.run(cmd, shell=True, check=False)
        if result.returncode != 0:
            print("❌ Main process failed")
            return 1

        if IS_DEBUG:
            print("⏳ Waiting for async processes to complete...")
        time.sleep(ASYNC_WAIT_TIME)

        return 0
    except Exception as e:
        print(f"❌ Error running main process: {e}")
        return 1
