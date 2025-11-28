import os
import sys
import subprocess
import shutil

def run_cmd(cmd, desc):
    print(f"🔹 {desc}...")
    try:
        # shell=True jest wymagane na Windows dla niektórych komend,
        # ale musimy uważać na spacje w ścieżkach
        subprocess.check_call(cmd, shell=True)
        print("✅ Gotowe.")
    except subprocess.CalledProcessError:
        print(f"❌ Błąd podczas: {desc}")
        sys.exit(1)

def main():
    print("=== INSTALATOR GEMINI AGENT ULTIMATE ===")
    
    # 1. Sprawdzenie Pythona
    if sys.version_info < (3, 8):
        print("❌ Wymagany Python 3.8+")
        sys.exit(1)

    # POPRAWKA: Użycie cudzysłowów wokół sys.executable obsługuje "Program Files"
    python_exe = f'"{sys.executable}"'
    
    # 2. Instalacja zależności Python
    run_cmd(f"{python_exe} -m pip install -r requirements.txt", "Instalacja bibliotek Python")

    # 3. Sprawdzenie Node.js i instalacja CLI
    # npm zazwyczaj jest w PATH, więc nie wymaga pełnej ścieżki
    if not shutil.which("npm"):
        print("❌ Nie znaleziono Node.js/npm. Zainstaluj Node.js ze strony https://nodejs.org/")
        sys.exit(1)
    
    # Na Windows npm.cmd jest bezpieczniejsze
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    run_cmd(f"{npm_cmd} install -g @google/gemini-cli", "Instalacja Google Gemini CLI")

    # 4. Tworzenie pliku .env (opcjonalnie)
    if not os.path.exists(".env"):
        print("\n🔑 Konfiguracja klucza API.")
        key = input("Podaj swój GEMINI_API_KEY (Enter aby pominąć i ustawić ręcznie): ").strip()
        if key:
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"GEMINI_API_KEY={key}\n")
                if os.name != 'nt':
                    print("ℹ️  Na Linux/Mac uruchom: source .env przed startem (lub export w terminalu).")

    print("\n🎉 Instalacja zakończona! Uruchom agenta wpisując:")
    print(f"   python run.py")

if __name__ == "__main__":
    main()