import subprocess
from rich.panel import Panel
import google.generativeai as genai
from src.config import console
from src.core.state import STATE
from src.core.models import ModelSelector

class GitAutoTool:
    @staticmethod
    def clone(url):
        name = url.split("/")[-1].replace(".git", "")
        target = os.path.join(STATE.get_cwd(), name)
        try:
            subprocess.run(["git", "clone", url, target], check=True, capture_output=True)
            STATE.set_cwd(target)
            return f"Sklonowano. Nowy CWD: {target}"
        except Exception as e: return f"Błąd: {e}"

    @staticmethod
    def smart_push(branch="main"):
        cwd = STATE.get_cwd()
        try:
            if not os.path.exists(os.path.join(cwd, ".git")): return "To nie repozytorium Git."
            subprocess.run(["git", "add", "."], cwd=cwd, check=True)
            diff = subprocess.check_output(["git", "diff", "--cached"], cwd=cwd, text=True)
            if not diff: return "Brak zmian."
            
            model = genai.GenerativeModel(ModelSelector.TARGET_FAST)
            msg = model.generate_content(f"Git commit message (1 line) for:\n{diff}").text.strip().replace('"','')
            console.print(Panel(f"[green]{msg}[/green]", title="Auto-Commit"))
            
            subprocess.run(["git", "commit", "-m", msg], cwd=cwd, check=True)
            subprocess.run(["git", "push", "origin", branch], cwd=cwd, check=True)
            return f"Push OK: {msg}"
        except Exception as e: return f"Błąd Git: {e}"
