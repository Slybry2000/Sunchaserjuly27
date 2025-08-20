"""Run pytest for specified files with a hard timeout and live output.

Usage:
  python scripts/run_pytest_timeout.py [timeout_seconds] [pytest_args...]

Defaults:
  timeout_seconds=60
  pytest_args=['Backend/tests/test_cache_inproc.py', '-q']

Behavior:
  - Streams pytest stdout/stderr live (no buffering), so you see progress.
  - Prints a heartbeat every 10s: "[pytest running… Ns elapsed]".
  - Enforces a hard timeout; on timeout sends terminate, then kill if needed.

Exit codes: returns pytest exit code, or 124 on timeout.
"""
import subprocess
import sys
import time

def main():
    args = sys.argv[1:]
    timeout = 60
    if args and args[0].isdigit():
        timeout = int(args[0])
        args = args[1:]

    if not args:
        args = ['Backend/tests/test_cache_inproc.py', '-q']

    cmd = [sys.executable, '-m', 'pytest'] + args
    print(f"Running: {' '.join(cmd)} (timeout={timeout}s)")

    # Launch pytest without capturing, so output streams directly to console
    proc = subprocess.Popen(cmd)

    start = time.monotonic()
    last_heartbeat = 0.0
    heartbeat_interval = 10.0
    try:
        while True:
            rc = proc.poll()
            if rc is not None:
                return rc

            elapsed = time.monotonic() - start
            if elapsed - last_heartbeat >= heartbeat_interval:
                print(f"[pytest running… {int(elapsed)}s elapsed]", flush=True)
                last_heartbeat = elapsed

            if elapsed >= timeout:
                print(f"ERROR: test run timed out after {timeout} seconds", file=sys.stderr, flush=True)
                # Try graceful terminate first
                try:
                    proc.terminate()
                except Exception:
                    pass
                # Give it a moment to exit
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass
                if proc.poll() is None:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    try:
                        proc.wait(timeout=5)
                    except Exception:
                        pass
                return 124

            time.sleep(0.2)
    finally:
        # Ensure process is not left around if we exit unexpectedly
        if proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
