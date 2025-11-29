import sys
import os
# Dodajemy bieżący katalog do ścieżki (naprawia importy)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.app import DebugDruidApp

if __name__ == "__main__":
    DebugDruidApp().run()
