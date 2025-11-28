import os
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
