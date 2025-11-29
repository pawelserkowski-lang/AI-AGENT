import os
import sys
import time
import subprocess

WATCH_DIRS = ["core", "ui"]
WATCH_FILES = ["main.py"]
POLL_INTERVAL = 1.0

def get_mtimes():
    mtimes = {}
    for f in WATCH_FILES:
        if os.path.exists(f): mtimes[f] = os.path.getmtime(f)
    for d in WATCH_DIRS:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith(".py") or f.endswith(".kv"):
                        path = os.path.join(root, f)
                        mtimes[path] = os.path.getmtime(path)
    return mtimes

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "main.py")
    python_exe = sys.executable
    
    print("[DRUID] Uruchamiam aplikacje...")
    process = subprocess.Popen([python_exe, main_script], cwd=script_dir)
    last_mtimes = get_mtimes()

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            if process.poll() is not None: break
            
            curr_mtimes = get_mtimes()
            if curr_mtimes != last_mtimes:
                print("[DRUID] Wykryto zmiany! Restart...")
                process.terminate()
                try: process.wait(timeout=1)
                except: process.kill()
                process = subprocess.Popen([python_exe, main_script], cwd=script_dir)
                last_mtimes = curr_mtimes
    except KeyboardInterrupt:
        process.terminate()

if __name__ == "__main__":
    main()
