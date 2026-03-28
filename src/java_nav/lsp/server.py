"""Manage jdtls lifecycle via multilspy — on-demand or persistent daemon."""

import os
import signal
import subprocess
import sys
import time

from java_nav.classpath import CACHE_DIR

PID_FILE = "jdtls.pid"
PORT_FILE = "jdtls.port"


def _state_dir(project_dir: str) -> str:
    return os.path.join(project_dir, CACHE_DIR)


def _pid_path(project_dir: str) -> str:
    return os.path.join(_state_dir(project_dir), PID_FILE)


def is_running(project_dir: str) -> bool:
    """Check if a jdtls daemon is alive for this project."""
    pid_path = _pid_path(project_dir)
    if not os.path.isfile(pid_path):
        return False
    with open(pid_path) as f:
        pid = int(f.read().strip())
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        # Stale PID file
        os.remove(pid_path)
        return False


def start_daemon(project_dir: str) -> int:
    """Start a jdtls daemon subprocess. Returns the PID."""
    if is_running(project_dir):
        with open(_pid_path(project_dir)) as f:
            return int(f.read().strip())

    state = _state_dir(project_dir)
    os.makedirs(state, exist_ok=True)

    # Start the daemon subprocess
    daemon_script = os.path.join(os.path.dirname(__file__), "_daemon_proc.py")
    proc = subprocess.Popen(
        [sys.executable, daemon_script, project_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    # Wait for the daemon to signal readiness via port file
    port_path = os.path.join(state, PORT_FILE)
    for _ in range(120):  # up to 120s for large projects
        if os.path.isfile(port_path):
            break
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode() if proc.stderr else ""
            print(f"jdtls daemon failed to start:\n{stderr}", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)
    else:
        proc.kill()
        print("jdtls daemon timed out during startup.", file=sys.stderr)
        sys.exit(1)

    # Write PID file
    with open(_pid_path(project_dir), "w") as f:
        f.write(str(proc.pid))

    return proc.pid


def stop_daemon(project_dir: str) -> bool:
    """Stop the jdtls daemon. Returns True if it was running."""
    pid_path = _pid_path(project_dir)
    if not os.path.isfile(pid_path):
        return False
    with open(pid_path) as f:
        pid = int(f.read().strip())
    import contextlib

    with contextlib.suppress(OSError):
        os.kill(pid, signal.SIGTERM)

    # Cleanup state files
    for name in [PID_FILE, PORT_FILE]:
        path = os.path.join(_state_dir(project_dir), name)
        if os.path.isfile(path):
            os.remove(path)
    return True


def get_port(project_dir: str) -> int | None:
    """Get the daemon's communication port, or None if not running."""
    port_path = os.path.join(_state_dir(project_dir), PORT_FILE)
    if not os.path.isfile(port_path):
        return None
    with open(port_path) as f:
        return int(f.read().strip())
