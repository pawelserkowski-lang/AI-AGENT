import sys
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
