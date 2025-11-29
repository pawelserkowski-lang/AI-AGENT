import os
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.core.clipboard import Clipboard
from kivymd.toast import toast
from kivymd.app import MDApp

class NotepadLogic(MDBoxLayout):
    def on_kv_post(self, base_widget):
        if os.path.exists("scratchpad.txt"):
            with open("scratchpad.txt", "r", encoding="utf-8") as f: self.ids.notepad_field.text = f.read()
    def auto_save(self):
        with open("scratchpad.txt", "w", encoding="utf-8") as f: f.write(self.ids.notepad_field.text)
    def copy_to_clipboard(self):
        Clipboard.copy(self.ids.notepad_field.text)
        toast("Skopiowano")
    def clear_text(self):
        self.ids.notepad_field.text = ""
        self.auto_save()
    def send_to_chat(self):
        text = self.ids.notepad_field.text
        if not text: return
        app = MDApp.get_running_app()
        app.transfer_to_chat(text)
    def save_to_file(self):
        if not os.path.exists("notes"): os.makedirs("notes")
        import time
        fname = f"notes/note_{int(time.time())}.txt"
        with open(fname, "w", encoding="utf-8") as f: f.write(self.ids.notepad_field.text)
        toast(f"Zapisano w {fname}")
