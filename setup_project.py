import os
import sys
import subprocess
import shutil

# Nazwa projektu
PROJECT_NAME = "GeminiAgent"

# ==========================================
# DEFINICJE ZAWARTOŚCI PLIKÓW
# ==========================================

# 1. requirements.txt
REQ_TXT = """google-generativeai
pexpect
pillow
rich
duckduckgo-search
requests
"""

# 2. install.py
INSTALL_PY = r"""import os
import sys
import subprocess
import shutil

def run_cmd(cmd, desc):
    print(f"🔹 {desc}...")
    try:
        subprocess.check_call(cmd, shell=True)
        print("✅ Gotowe.")
    except subprocess.CalledProcessError:
        print(f"❌ Błąd podczas: {desc}")
        sys.exit(1)

def main():
    print("=== INSTALATOR GEMINI AGENT ULTIMATE ===")
    
    if sys.version_info < (3, 8):
        print("❌ Wymagany Python 3.8+")
        sys.exit(1)

    run_cmd(f"{sys.executable} -m pip install -r requirements.txt", "Instalacja bibliotek Python")

    if not shutil.which("npm"):
        print("❌ Nie znaleziono Node.js/npm. Zainstaluj Node.js: https://nodejs.org/")
        sys.exit(1)
    
    run_cmd("npm install -g @google/gemini-cli", "Instalacja Google Gemini CLI")

    if not os.path.exists(".env"):
        print("\n🔑 Konfiguracja klucza API.")
        key = input("Podaj GEMINI_API_KEY (Enter aby pominąć): ").strip()
        if key:
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"GEMINI_API_KEY={key}\n")

    print("\n🎉 Gotowe! Uruchom agenta: python run.py")

if __name__ == "__main__":
    main()
"""

# 3. run.py
RUN_PY = r"""import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.core.agent import main
except ImportError as e:
    print(f"❌ Błąd importu: {e}")
    print("Upewnij się, że uruchomiłeś 'python install.py'")
    sys.exit(1)

if __name__ == "__main__":
    if os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

    if not os.getenv("GEMINI_API_KEY"):
        print("❌ BŁĄD: Brak zmiennej GEMINI_API_KEY.")
        sys.exit(1)

    main()
"""

# 4. src/config.py
CONFIG_PY = r"""from rich.console import Console
import logging

console = Console()
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger("GeminiAgent")
"""

# 5. src/core/state.py
STATE_PY = r"""import os
import threading
import http.server
import socketserver
import webbrowser
import time
from src.config import console

class SessionState:
    def __init__(self):
        self.cwd = os.getcwd()
    
    def set_cwd(self, path):
        self.cwd = os.path.abspath(path)
        console.print(f"[bold yellow]📂 Zmiana katalogu na: {self.cwd}[/bold yellow]")
        if LiveServer.is_running():
            LiveServer.restart()

    def get_cwd(self):
        return self.cwd

    def resolve(self, filename):
        if os.path.isabs(filename): return filename
        return os.path.join(self.cwd, filename)

STATE = SessionState()

class LiveServer:
    _thread = None
    _httpd = None
    _running = False
    _port = 8000

    @staticmethod
    def is_running(): return LiveServer._running

    @staticmethod
    def start():
        if LiveServer._running: return
        LiveServer._running = True
        
        def serve():
            try:
                os.chdir(STATE.get_cwd())
                handler = http.server.SimpleHTTPRequestHandler
                handler.log_message = lambda *args: None
                
                LiveServer._httpd = socketserver.TCPServer(("", LiveServer._port), handler)
                LiveServer._httpd.timeout = 1 
                console.print(f"[bold green]🟢 LIVE SERVER: http://localhost:{LiveServer._port}[/bold green]")
                
                while LiveServer._running:
                    LiveServer._httpd.handle_request()
            except OSError:
                console.print(f"[red]Port {LiveServer._port} zajęty.[/red]")
                LiveServer._running = False
            finally:
                if LiveServer._httpd: LiveServer._httpd.server_close()

        LiveServer._thread = threading.Thread(target=serve, daemon=True)
        LiveServer._thread.start()
        time.sleep(1)
        webbrowser.open(f"http://localhost:{LiveServer._port}")

    @staticmethod
    def stop():
        LiveServer._running = False
        if LiveServer._thread: LiveServer._thread.join(timeout=2)

    @staticmethod
    def restart():
        LiveServer.stop()
        time.sleep(0.5)
        LiveServer.start()
"""

# 6. src/core/models.py
MODELS_PY = r"""import os
import google.generativeai as genai
from src.config import console

class ModelSelector:
    TARGET_VISION = "gemini-3.0-pro-image-preview" 
    TARGET_CHAT_FALLBACK = "gemini-3.0-pro-preview"
    TARGET_FAST = "gemini-1.5-flash"

    @staticmethod
    def _init():
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    @staticmethod
    def get_chat_model():
        ModelSelector._init()
        try:
            models = genai.list_models()
            candidates = [m for m in models if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
            if not candidates: return ModelSelector.TARGET_CHAT_FALLBACK
            best = sorted(candidates, key=lambda m: (1000 if 'pro' in m.name else 0) + (50 if '1.5' in m.name else 0), reverse=True)[0]
            return best.name.replace("models/", "")
        except: return ModelSelector.TARGET_CHAT_FALLBACK

    @staticmethod
    def get_vision_model():
        ModelSelector._init()
        try:
            models = list(genai.list_models())
            if any(ModelSelector.TARGET_VISION in m.name for m in models): return ModelSelector.TARGET_VISION
            candidates = [m for m in models if 'gemini' in m.name and not ('1.0' in m.name and 'vision' not in m.name)]
            best = sorted(candidates, key=lambda m: 100 if 'pro' in m.name else 80, reverse=True)[0]
            return best.name.replace("models/", "")
        except: return "gemini-1.5-pro-latest"

class PromptAlchemy:
    @staticmethod
    def optimize(user_input):
        ModelSelector._init()
        model = genai.GenerativeModel(ModelSelector.get_chat_model())
        meta_prompt = f"Jesteś inżynierem promptów. Przepisz to zapytanie na precyzyjną instrukcję techniczną dla AI: '{user_input}'"
        with console.status("[bold magenta]✨ Alchemia Promptu...[/bold magenta]"):
            response = model.generate_content(meta_prompt)
        return response.text.strip()
"""

# 7. src/core/agent.py
AGENT_PY = r"""import sys
import shutil
import pexpect
import re
import subprocess
import os

from src.config import console
from src.core.models import ModelSelector, PromptAlchemy
from src.core.state import STATE, LiveServer
from src.ui.loader import CyberLoader

from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.prompt import Confirm

from src.tools.devops import GitAutoTool
from src.tools.web import WebSearch, WebAutoPilot, APITool
from src.tools.system import FileIO, DBTool
from src.tools.vision import VisionTool

class AgentEngine:
    def __init__(self, chat_m, vision_m):
        self.vision_m = vision_m
        if not shutil.which("gemini"): 
            console.print("[red]Brak @google/gemini-cli. Uruchom install.py[/red]")
            sys.exit(1)
        
        console.print(f"[bold blue]🚀 SYSTEM ONLINE: {chat_m}[/bold blue]")
        try:
            self.child = pexpect.spawn(f"gemini chat --model {chat_m}", encoding='utf-8')
            self.child.expect(['>', 'User:', 'Ty:'], timeout=20)
            
            prompt = (
                "Jesteś Autonomicznym Inżynierem Full-Stack (v16.0 Modular). "
                "PROTOKOŁY NARZĘDZI (Używaj ich samodzielnie): "
                "1. FILES: >>> READ: path | >>> SAVE: path (kod w bloku markdown) "
                "2. DEVOPS: >>> GIT_CLONE: url | >>> GIT_PUSH: branch "
                "3. WEB DEV: >>> SQL: db|query | >>> API: METHOD|url|json "
                "4. AUTOMATION: >>> MAGIC_DESIGN: Name|Theme "
                "5. SYSTEM: >>> RUN: cmd | >>> WEB: query | >>> STACK: error "
                "6. PREVIEW: >>> SERVER: START (start live server) "
                "Zasada: Pracujesz w katalogu CWD. Bądź samodzielny."
            )
            self.child.sendline(prompt)
            self.child.expect(['>', 'User:', 'Ty:'], timeout=20)
        except: sys.exit("Błąd inicjalizacji CLI")

    def query(self, text):
        cwd_info = f"[SYSTEM: CWD={STATE.get_cwd()}]\n"
        self.child.sendline(cwd_info + text)
        
        ldr = CyberLoader(); ldr.start()
        try:
            self.child.expect(['>', 'User:', 'Ty:'], timeout=300)
            raw = self.child.before
            # Bezpieczne usuwanie ANSI
            resp = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', "\n".join(raw.splitlines()[1:]).strip())
            ldr.stop()
            
            if m := re.search(r">>> (?:WEB|STACK): (.*?)(?:\n|$)", resp):
                return self.query(f"WYNIK: {WebSearch.search(m.group(1))} \nKontynuuj.")
            
            if m := re.search(r">>> READ: (.*?)(?:\n|$)", resp):
                return self.query(FileIO.read(m.group(1).strip()))
                
            if m := re.search(r">>> GIT_CLONE: (.*?)(?:\n|$)", resp):
                return self.query(GitAutoTool.clone(m.group(1).strip()))

            if m := re.search(r">>> SQL: (.*?)(?:\n|$)", resp):
                p = m.group(1).split('|', 1)
                return self.query(f"WYNIK SQL: {DBTool.query(p[0], p[1])}")

            self._actions(resp)
            return resp
        except: ldr.stop(); return "⚠️ Timeout."

    def _actions(self, text):
        for n, c in re.findall(r">>> SAVE: (.*?)\n+```(?:\w+)?\n(.*?)```", text, re.DOTALL):
            self._do("SAVE", n, c, lambda p=STATE.resolve(n.strip()), d=c: open(p, 'w', encoding='utf-8').write(d))
        
        for c in re.findall(r">>> RUN: (.*?)(?:\n|$)", text):
            self._do("RUN", c, None, lambda cmd=c.strip(): subprocess.run(cmd, shell=True, cwd=STATE.get_cwd()))

        for b in re.findall(r">>> GIT_PUSH: (.*?)(?:\n|$)", text):
            self._do("PUSH", b, None, lambda: console.print(GitAutoTool.smart_push(b.strip())))

        for a in re.findall(r">>> API: (.*?)(?:\n|$)", text):
            p = a.split('|'); self._do("API", p[1], None, lambda: console.print(APITool.req(p[0], p[1], p[2] if len(p)>2 else None)))

        for m in re.findall(r">>> MAGIC_DESIGN: (.*?)(?:\n|$)", text):
            p = m.split('|')
            self._do("DESIGN", p[0], None, lambda: WebAutoPilot.magic_design(p[0], p[1] if len(p)>1 else "modern"))

        if ">>> SERVER: START" in text:
            LiveServer.start()

        for p in re.findall(r">>> PREVIEW: (.*?)(?:\n|$)", text):
            webbrowser.open(STATE.resolve(p.strip()))

    def _do(self, type, target, code, func):
        col = "green" if type in ["SAVE", "PUSH", "DESIGN"] else "red"
        if code: console.print(Panel(Syntax(code, "python"), title=f"{type}: {target}", border_style=col))
        else: console.print(Panel(f"[bold]{target}[/bold]", title=f"{type}", border_style=col))
        
        if Confirm.ask(f"[bold {col}]Wykonać?[/bold {col}]", default=True):
            try: func(); console.print(f"[bold green]OK[/bold green]")
            except Exception as e: console.print(f"[bold red]Błąd: {e}[/bold red]")
    
    def close(self):
        try: self.child.sendline('exit'); self.child.close()
        except: pass

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print(Panel.fit("[bold cyan]GEMINI MODULAR v16.0[/bold cyan]", border_style="blue"))
    
    c_mod = ModelSelector.get_chat_model()
    v_mod = ModelSelector.get_vision_model()
    agent = AgentEngine(c_mod, v_mod)
    
    console.print("[white]Gotowy. Użyj /opt <pomysł>, przeciągnij plik lub pisz.[/white]")

    while True:
        try:
            u = console.input("\n[bold cyan]USER[/bold cyan] > ")
            if u.lower() in ['exit', '/exit', 'q']: break
            if not u.strip(): continue

            if u.startswith("/opt"):
                idea = u.replace("/opt", "").strip()
                if idea:
                    u = PromptAlchemy.optimize(idea)
                    console.print(Panel(u, title="✨ Optimized Prompt", border_style="yellow"))
                    if not Confirm.ask("Użyć?", default=True): continue

            path = u.strip().strip("'").strip('"')
            if os.path.exists(path) and os.path.isfile(path):
                import mimetypes
                mt, _ = mimetypes.guess_type(path)
                if mt and mt.startswith('image'):
                    resp = VisionTool.analyze(path, v_mod)
                    agent.child.sendline(f"Oto obraz: {resp}")
                    resp = agent.query("Opisz to.")
                else:
                    resp = agent.query(f"Plik: {path}. {FileIO.read(path)}")
            else:
                resp = agent.query(u)
            
            console.print(Panel(Markdown(resp), title="Gemini", border_style="magenta"))
        except KeyboardInterrupt: break
    
    LiveServer.stop()
    agent.close()
"""

# 8. src/tools/devops.py
DEVOPS_PY = r"""import subprocess
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
"""

# 9. src/tools/web.py
WEB_PY = r"""import os
import requests
import json
from duckduckgo_search import DDGS
from src.config import console
from src.core.state import STATE, LiveServer

class WebSearch:
    @staticmethod
    def search(q):
        try:
            res = DDGS().text(q, max_results=3)
            return "\n".join([f"- {r['title']}: {r['body']}" for r in res])
        except: return "Błąd sieci."

class WebAutoPilot:
    @staticmethod
    def magic_design(project_name, theme):
        console.print(f"[bold magenta]🎨 Generowanie strony: {project_name} ({theme})[/bold magenta]")
        
        html = f"<h1>{project_name}</h1><p>Theme: {theme}</p>"
        css = "body { font-family: sans-serif; text-align: center; padding: 50px; background: #f0f0f0; }"
        
        target_dir = os.path.join(STATE.get_cwd(), project_name)
        os.makedirs(target_dir, exist_ok=True)
        with open(os.path.join(target_dir, "index.html"), "w", encoding="utf-8") as f: f.write(html)
        with open(os.path.join(target_dir, "style.css"), "w", encoding="utf-8") as f: f.write(css)
        
        STATE.set_cwd(target_dir)
        LiveServer.start()
        return os.path.join(target_dir, "index.html")

class APITool:
    @staticmethod
    def req(method, url, data=None):
        try:
            console.print(f"[blue]📡 API {method}: {url}[/blue]")
            resp = requests.request(method, url, json=json.loads(data) if data else None, timeout=5)
            return f"Status: {resp.status_code}\n{resp.text[:600]}"
        except Exception as e: return f"API Error: {e}"
"""

# 10. src/tools/system.py
SYSTEM_PY = r"""import os
import sqlite3
from rich.table import Table
from src.config import console
from src.core.state import STATE

class FileIO:
    @staticmethod
    def read(path):
        p = STATE.resolve(path)
        try:
            with open(p, 'r', encoding='utf-8') as f: return f"PLIK ({path}):\n```\n{f.read()}\n```"
        except Exception as e: return f"Błąd: {e}"

class DBTool:
    @staticmethod
    def query(db_path, sql):
        path = STATE.resolve(db_path)
        try:
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                rows = cur.fetchall()
                if not rows: return "Brak wyników."
                return str(rows) 
            else:
                conn.commit(); chg = conn.total_changes; conn.close()
                return f"Zmodyfikowano: {chg}"
        except Exception as e: return f"SQL Error: {e}"
"""

# 11. src/tools/vision.py
VISION_PY = r"""from PIL import Image
import google.generativeai as genai

class VisionTool:
    @staticmethod
    def analyze(path, model_name):
        try:
            img = Image.open(path)
            m = genai.GenerativeModel(model_name)
            return f"[VISION]: {m.generate_content(['Analyze code/UI details', img]).text}"
        except Exception as e: return f"Błąd Vision: {e}"
"""

# 12. src/ui/loader.py
LOADER_PY = r"""import threading
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
"""

# ==========================================
# GENERATOR PLIKÓW
# ==========================================

FILES = {
    "requirements.txt": REQ_TXT,
    "install.py": INSTALL_PY,
    "run.py": RUN_PY,
    "src/config.py": CONFIG_PY,
    "src/core/state.py": STATE_PY,
    "src/core/models.py": MODELS_PY,
    "src/core/agent.py": AGENT_PY,
    "src/tools/devops.py": DEVOPS_PY,
    "src/tools/web.py": WEB_PY,
    "src/tools/system.py": SYSTEM_PY,
    "src/tools/vision.py": VISION_PY,
    "src/ui/loader.py": LOADER_PY,
    "src/__init__.py": "",
    "src/core/__init__.py": "",
    "src/tools/__init__.py": "",
    "src/ui/__init__.py": ""
}

def create_project():
    print(f"🚀 Generowanie struktury {PROJECT_NAME}...")
    
    if not os.path.exists(PROJECT_NAME):
        os.makedirs(PROJECT_NAME)

    for path, content in FILES.items():
        full_path = os.path.join(PROJECT_NAME, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        # Zapis binarny (utf-8) dla pewności
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   + {path}")

    print(f"\n✅ SUKCES! Projekt utworzony w folderze: {PROJECT_NAME}")
    print(f"1. cd {PROJECT_NAME}")
    print(f"2. python install.py")
    print(f"3. python run.py")

if __name__ == "__main__":
    create_project()