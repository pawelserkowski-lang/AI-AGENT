import os
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
