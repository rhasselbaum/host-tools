#!/usr/bin/env python3

"""
Runs in the background and automatically reboots the host if it detects Intertnet connectivity is lost for
an extended period of time, which could indicate a network interface failure due to...reasons.
"""

import signal
import subprocess
import sys
from threading import Event

CHECK_INTERVAL = 60  # seconds
MAX_FAILURES = 10    # 10 minutes if interval is 60 seconds
PING_HOST = "8.8.8.8"

shutdown_event = Event()

def signal_handler(signum, frame):
    print(f"Received signal {signum}, exiting.")
    shutdown_event.set()

def has_internet():
    try:
        subprocess.check_output(["ping", "-c", "1", "-W", "2", PING_HOST], stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    failure_count = 0

    print("Connectivity watchdog started.")
    while not shutdown_event.is_set():
        if has_internet():
            failure_count = 0
        else:
            failure_count += 1
            print(f"Internet unreachable. Failure count: {failure_count}/{MAX_FAILURES}")
            if failure_count >= MAX_FAILURES:
                print("Connectivity lost. Rebooting...")
                subprocess.run(["systemctl", "reboot"], check=False)

        shutdown_event.wait(CHECK_INTERVAL)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        main()
    except Exception as e:
        print(f"Unhandled exception: {e}")
        sys.exit(1)
