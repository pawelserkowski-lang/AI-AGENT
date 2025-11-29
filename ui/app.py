import os
import sys
import json
import threading
import logging
import webbrowser
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.toast import toast
from dotenv import load_dotenv

from core.database import DatabaseManager
from core.agent import Agent
from core.logger import KivyLogHandler

# Importy
from ui.screens.chat import ChatScreenLogic
from ui.screens.notepad import NotepadLogic
from ui.widgets.session_item import SessionItem
from ui.widgets.file_item import FileItem

load_dotenv()
CONFIG_FILE = "config.json"

# Fix EXE path
def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- KLASY WIDGETÓW DLA KV ---
class MainLayout(MDBoxLayout): pass
class RightControlPanel(MDBoxLayout): pass
class ModelListItem(OneLineListItem): pass

class DebugDruidApp(MDApp):
    logs_text = StringProperty("--- DEBUG DRUID v42.0 ---\n")
    
    current_main_model = StringProperty("Szukam modelu...")
    current_session_title = StringProperty("Nowa Sesja")
    current_session_id = NumericProperty(-1)
    
    api_key = StringProperty(os.getenv("API_KEY", ""))
    use_google_search = BooleanProperty(True)
    
    # Parametry
    param_polish = BooleanProperty(True)
    param_comments = BooleanProperty(False)
    param_expert = BooleanProperty(False)
    param_concise = BooleanProperty(False)
    param_stackoverflow = BooleanProperty(False)
    param_docs = BooleanProperty(False)
    param_custom_text = StringProperty("")
    param_temperature = NumericProperty(0.2)
    param_max_tokens = NumericProperty(8192)
    param_auto_save_files = BooleanProperty(True)
    
    # Theme
    is_dark_mode = BooleanProperty(False)
    available_models = ListProperty([]) # Dodano brakującą listę

    # Zmienne wymagane przez UI, choć nieużywane w logice hardlocka (dla kompatybilności)
    current_analysis_model = StringProperty("Wybierz...")
    current_image_model = StringProperty("Wybierz...")

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        try: self.icon = resource_path("ikona.webp")
        except: pass
        self.title = "DebugDruid"
        
        # Logger Setup
        log_handler = KivyLogHandler(self)
        log_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)

        self.load_config()
        self.apply_theme()
        self.db = DatabaseManager()
        self.agent = Agent(self.db, self)

        # Ładujemy KV i zwracamy MainLayout
        Builder.load_file(resource_path(os.path.join("ui", "layout.kv")))
        return MainLayout()

    def on_start(self):
        if self.api_key:
            threading.Thread(target=self.init_agent_model, daemon=True).start()
        Clock.schedule_once(lambda dt: self.refresh_sessions_list(), 0.5)

    def init_agent_model(self):
        logging.info("Auto-Discovery: Szukam modelu...")
        model = self.agent.discover_best_model(self.api_key)
        if model:
            Clock.schedule_once(lambda dt: setattr(self, 'current_main_model', model), 0)
            logging.info(f"Ustawiono: {model}")
        else:
            Clock.schedule_once(lambda dt: setattr(self, 'current_main_model', "Błąd / Brak"), 0)

    def on_stop(self): self.save_config()

    def update_api_key(self, text):
        self.api_key = text
        self.save_config()
        threading.Thread(target=self.init_agent_model, daemon=True).start()

    def toggle_theme(self, is_dark):
        self.is_dark_mode = is_dark
        self.apply_theme()
        self.save_config()

    def apply_theme(self):
        if self.is_dark_mode:
            self.theme_cls.theme_style = "Dark"
            self.theme_cls.primary_palette = "Teal"
        else:
            self.theme_cls.theme_style = "Light"
            self.theme_cls.primary_palette = "Blue"

    def close_right_drawer(self):
        self.root.ids.nav_drawer_right.set_state("close")
        self.save_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.param_temperature = data.get("temperature", 0.2)
                    self.param_max_tokens = data.get("max_tokens", 8192)
                    self.use_google_search = data.get("use_google_search", True)
                    self.param_stackoverflow = data.get("stackoverflow", False)
                    self.param_custom_text = data.get("custom_text", "")
                    self.param_auto_save_files = data.get("auto_save_files", True)
                    self.is_dark_mode = data.get("dark_mode", False)
                    if not self.api_key: self.api_key = data.get("api_key", "")
            except: pass

    def save_config(self):
        data = {
            "temperature": self.param_temperature,
            "max_tokens": self.param_max_tokens,
            "use_google_search": self.use_google_search,
            "stackoverflow": self.param_stackoverflow,
            "custom_text": self.param_custom_text,
            "auto_save_files": self.param_auto_save_files,
            "dark_mode": self.is_dark_mode,
            "api_key": self.api_key
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
        except: pass

    # --- SESSION ---
    def refresh_sessions_list(self):
        try:
            history_list = self.root.ids.history_list
            history_list.clear_widgets()
            sessions = self.db.get_sessions()
            for sess_id, title in sessions:
                item = SessionItem(text=title, session_id=sess_id, title=title)
                history_list.add_widget(item)
        except: pass

    def start_new_chat(self):
        self.current_session_id = -1
        self.current_session_title = "Nowa Sesja"
        self.root.ids.chat_screen.clear_view()
        self.root.ids.nav_drawer_left.set_state("close")

    def load_session(self, session_id):
        self.current_session_id = session_id
        sessions = self.db.get_sessions()
        for sid, title in sessions:
            if sid == session_id:
                self.current_session_title = title
                break
        self.root.ids.chat_screen.clear_view()
        messages = self.db.get_messages(session_id)
        for msg in messages:
            content = msg['content']
            if "[CONTEXT FILES]" in content: content = content.split("[CONTEXT FILES]")[0] + "... [Pliki]"
            self.root.ids.chat_screen.add_bubble(content, msg['role'] == 'user')
        self.root.ids.nav_drawer_left.set_state("close")

    def delete_session(self, session_id):
        self.db.delete_session(session_id)
        if self.current_session_id == session_id: self.start_new_chat()
        self.refresh_sessions_list()

    def transfer_to_chat(self, text):
        self.root.ids.chat_screen.ids.message_input.text = text
        toast("Przeniesiono do czatu")

    def open_web_preview(self, file_path):
        try:
            abs_path = os.path.abspath(file_path)
            webbrowser.open(f'file://{abs_path}')
            toast("Otwarto podgląd")
        except: pass

    # --- METODA, KTÓREJ BRAKOWAŁO ---
    def append_log(self, msg):
        self.logs_text += msg + "\n"

    def clear_logs(self): self.logs_text = ""
