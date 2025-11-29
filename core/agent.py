import threading
import logging
import os
import re
from kivy.clock import Clock

genai = None
PIL_Image = None

class Agent:
    def __init__(self, db_manager, app_instance):
        self.db = db_manager
        self.app = app_instance
        self.base_prompt = """
        ROLE: Gemini Code Assist (CLI Backend).
        TASK: High-performance code generation & Visual Analysis.
        RULES:
        1. Markdown for code.
        2. Analyze provided files/images thoroughly.
        3. Production-ready output.
        """
        self.cached_model = None

    def _init_google(self):
        global genai, PIL_Image
        if genai is None:
            try:
                import google.generativeai as genai
                from PIL import Image as PIL_Image
                return True
            except ImportError:
                logging.critical("Brak bibliotek: google-generativeai lub Pillow!")
                return False
        return True

    def discover_best_model(self, api_key):
        """Pobiera listę i wybiera najlepszy dostępny model."""
        if not self._init_google() or not api_key: return None
        try:
            genai.configure(api_key=api_key)
            # Pobieramy modele obsługujące content generation
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Priorytety
            priorities = [
                "models/gemini-1.5-pro-002",
                "models/gemini-1.5-pro-latest",
                "models/gemini-1.5-pro",
                "models/gemini-1.5-flash",
                "models/gemini-pro"
            ]
            
            for p in priorities:
                if p in models:
                    self.cached_model = p.replace("models/", "")
                    return self.cached_model
            
            # Fallback
            if models:
                self.cached_model = models[0].replace("models/", "")
                return self.cached_model
                
        except Exception as e:
            logging.error(f"Model Discovery Error: {e}")
        return None

    def _build_system_prompt(self):
        instructions = [self.base_prompt]
        if self.app.param_polish: instructions.append("LANG: Polish.")
        if self.app.param_comments: instructions.append("Add docstrings.")
        if self.app.param_expert: instructions.append("MODE: Expert.")
        if self.app.param_concise: instructions.append("MODE: Concise.")
        if self.app.param_stackoverflow: instructions.append("STYLE: StackOverflow.")
        if self.app.param_custom_text.strip():
            instructions.append(f"\nUSER_OVERRIDES:\n{self.app.param_custom_text}\n")
        return "\n".join(instructions)

    def _check_and_save_html(self, text):
        if not self.app.param_auto_save_files: return None
        match = re.search(r'```html(.*?)```', text, re.DOTALL)
        if match:
            html_content = match.group(1).strip()
            preview_dir = "preview"
            if not os.path.exists(preview_dir): os.makedirs(preview_dir)
            file_path = os.path.join(preview_dir, "index.html")
            try:
                with open(file_path, "w", encoding="utf-8") as f: f.write(html_content)
                logging.info("HTML saved.")
                return file_path
            except Exception as e: logging.error(f"Save Error: {e}")
        return None

    def send_message(self, session_id, message, file_contents, images, callback_success, callback_error):
        if not self.app.api_key:
            callback_error("Brak klucza API!")
            return

        def _thread_target():
            if not self._init_google():
                Clock.schedule_once(lambda dt: callback_error("Brak bibliotek"), 0)
                return
            
            # Użyj wykrytego modelu lub domyślnego
            target_model = self.cached_model if self.cached_model else "gemini-1.5-pro"
            logging.info(f"[ENGINE] Target: {target_model}")

            tools = [{"google_search_retrieval": {}}] if self.app.use_google_search else []
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            gen_config = {
                "temperature": self.app.param_temperature,
                "max_output_tokens": int(self.app.param_max_tokens),
                "top_p": 0.95,
                "top_k": 40
            }
            
            full_text_content = message
            if file_contents:
                full_text_content += "\n\n[CONTEXT FILES]:\n"
                for fname, fcontent in file_contents.items():
                    full_text_content += f"--- FILE: {fname} ---\n{fcontent}\n"
            
            db_content = full_text_content
            if images: db_content += f"\n\n[ATTACHED {len(images)} IMAGES]"
            self.db.add_message(session_id, "user", db_content)
            
            try:
                genai.configure(api_key=self.app.api_key)
                
                model = genai.GenerativeModel(
                    model_name=target_model,
                    system_instruction=self._build_system_prompt(),
                    generation_config=gen_config,
                    safety_settings=safety_settings,
                    tools=tools
                )
                
                content_parts = [full_text_content]
                for img_path in images:
                    try:
                        img = PIL_Image.open(img_path)
                        content_parts.append(img)
                    except: pass

                history_data = self.db.get_context_messages(session_id, 10)
                chat_history = []
                for msg in history_data[:-1]:
                     role = "user" if msg['role'] == "user" else "model"
                     chat_history.append({"role": role, "parts": [msg['content']]})
                
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(content_parts)
                bot_reply = response.text
                
                preview_file = self._check_and_save_html(bot_reply)
                if preview_file:
                    Clock.schedule_once(lambda dt: self.app.open_web_preview(preview_file), 0)

                self.db.add_message(session_id, "assistant", bot_reply)
                Clock.schedule_once(lambda dt: callback_success(bot_reply), 0)

            except Exception as e:
                err_msg = str(e)
                logging.error(f"Gemini Error: {err_msg}")
                Clock.schedule_once(lambda dt: callback_error(f"Błąd API: {err_msg}"), 0)

        threading.Thread(target=_thread_target, daemon=True).start()
