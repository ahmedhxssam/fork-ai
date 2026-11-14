"""Run the two local development processes and stop them together."""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    processes = []
    def stop(*_):
        for process in processes:
            if process.poll() is None:
                process.terminate()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        processes.append(subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1",
             "--port", "8000", "--reload"], cwd=ROOT))
        processes.append(subprocess.Popen(["npm", "run", "dev"], cwd=ROOT / "frontend"))
        print("FORK development: http://127.0.0.1:5173 · API http://127.0.0.1:8000", flush=True)
        while all(process.poll() is None for process in processes):
            time.sleep(.3)
    except KeyboardInterrupt:
        pass
    finally:
        stop()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    return max((process.returncode or 0 for process in processes), default=0)


if __name__ == "__main__":
    raise SystemExit(main())
