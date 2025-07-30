import os
import subprocess
import sys

SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "runonce_redis_integration.py"))

def run_command(args):
    """Run the CLI with a timeout and capture stdout/stderr"""
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH] + args,
            capture_output=True,
            text=True,
            timeout=10  # seconds
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "❌ Command timed out!"

def test_super_dry_run_message():
    output = run_command(["-s", "kerch/comp/m02:00-main-menu", "--super-dry-run"])
    assert "💧 SUPER DRY RUN" in output
    print("✅ test_super_dry_run_message passed.")

def test_ls_lists_folder():
    output = run_command(["-ls", "kerch/comp/m02", "--super-dry-run"])
    assert "00-main-menu" in output
    assert "01-np" in output
    print("✅ test_ls_lists_folder passed.")

def test_which_flag_matches_bookmark():
    output = run_command(["--which", "mock-folder:mock-sub-folder:mock-bookmark-1", "--super-dry-run"])
    assert "mock-folder/mock-sub-folder/mock-bookmark-1" in output
    assert "Please be more specific" in output
    print("✅ test_which_flag_matches_bookmark passed.")

if __name__ == "__main__":
    test_super_dry_run_message()
    test_ls_lists_folder()
    test_which_flag_matches_bookmark()

def test_which_collision_warning():
    output = run_command(["--which", "main", "--super-dry-run"])
    assert "Multiple bookmarks matched" in output
    print("✅ test_which_collision_warning passed.")
