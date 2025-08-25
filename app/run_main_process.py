import subprocess
import time

from app.bookmarks.bookmarks_meta import load_bookmark_meta_from_abs
from app.consts.bookmarks_consts import ASYNC_WAIT_TIME, IS_DEBUG
from app.types.bookmark_types import CurrentRunSettings, MatchedBookmarkObj
from app.utils.decorators import print_def_name

IS_PRINT_DEF_NAME = True


@print_def_name(IS_PRINT_DEF_NAME)
def handle_main_process(
    matched_bookmark_obj: MatchedBookmarkObj,
    current_run_settings: CurrentRunSettings | None = None
    ) -> int: # TODO(?): Why would there be no current_run_settings?
    """
    Handle the running main process.
    """

    # Handle dry and no docker, no redis modes
    is_no_docker_no_redis = (current_run_settings.get(
        "is_no_docker_no_redis")) if current_run_settings else False
    if is_no_docker_no_redis:
        print("🛑 Skipping all processing (no docker, no redis)")
        return 0

    is_no_docker_no_redis = current_run_settings.get(
        "is_no_docker") if current_run_settings else False
    if is_no_docker_no_redis:
        print("🛑 Skipping Docker")
        return 0

    # Dry Mode
    is_dry = current_run_settings.get(
        "is_no_saving_dry_run") if current_run_settings else False
    if is_dry:
        print("💧 Skipping main process (dry mode)")
        return 0

    print('')
    print("🚀 Running main process...")

    if matched_bookmark_obj.get("bookmark_info", {}).get("timestamp"):
        time_override = matched_bookmark_obj.get("bookmark_info", {}).get("timestamp")
    else:
        # TODO(): We should probably find a way to pass around the matched bookmark obj to obs so that we can save the meta to it when created, but this is a quick fix for now.
        bookmark_meta = load_bookmark_meta_from_abs(matched_bookmark_obj["bookmark_path_slash_abs"])
        time_override = ''
        if bookmark_meta and bookmark_meta.get("timestamp"):
            time_override = bookmark_meta.get("timestamp")

    cmd = f'docker exec -e GG_TIME_OVERRIDE={time_override} -it game_processor_backend python ./main.py --run-once --gg_user_id="DEV_GG_USER_ID"'

    try:
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
