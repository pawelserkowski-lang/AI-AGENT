import sys
import os

# Dodajemy src do ścieżki systemowej
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.core.agent import main
except ImportError as e:
    print(f"❌ Błąd importu: {e}")
    print("Upewnij się, że uruchomiłeś 'python install.py'")
    sys.exit(1)

def load_dotenv():
    # Wczytuje .env tylko jeśli zmienna nie istnieje w systemie.
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        # WAŻNE: Nie nadpisujemy, jeśli system już ma tę zmienną!
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            print(f"⚠️ Ostrzeżenie: Problem z plikiem .env: {e}")

if __name__ == "__main__":
    # 1. Najpierw sprawdzamy, czy system już ma klucz (np. z Windows Environment Variables)
    if not os.getenv("GEMINI_API_KEY"):
        # 2. Jeśli nie ma, próbujemy wczytać z pliku .env
        load_dotenv()

    # 3. Ostateczne sprawdzenie
    if not os.getenv("GEMINI_API_KEY"):
        print("\n❌ BŁĄD KRYTYCZNY: Nie znaleziono 'GEMINI_API_KEY'.")
        print("---------------------------------------------------")
        print("🔍 Skrypt sprawdził:")
        print("   1. Zmienne środowiskowe systemu (Environment Variables).")
        print("   2. Plik .env w folderze projektu.")
        print("\n💡 ROZWIĄZANIE:")
        print("   A) Jeśli dodałeś zmienną w ustawieniach Windows -> ZRESTARTUJ TERMINAL.")
        print("   B) Wpisz w terminalu (tymczasowo): $env:GEMINI_API_KEY='twoj_klucz'")
        sys.exit(1)

    # Uruchomienie głównej aplikacji
    main()
