import threading
import itertools
import time
import sys

class CyberLoader(threading.Thread):
    def __init__(self):
        super().__init__(target=self._run)
        self.evt = threading.Event()
    def _run(self):
        # Używamy bezpiecznych znaków dla Windows/UTF
        chars = itertools.cycle(['|', '/', '-', '\\'])
        while not self.evt.is_set():
            sys.stdout.write(f"\r{next(chars)} Agent pracuje...")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " "*30 + "\r")
    def stop(self): self.evt.set(); self.join()
