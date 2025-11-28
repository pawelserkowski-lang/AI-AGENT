import os
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
