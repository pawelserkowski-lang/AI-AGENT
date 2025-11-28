from PIL import Image
import google.generativeai as genai

class VisionTool:
    @staticmethod
    def analyze(path, model_name):
        try:
            img = Image.open(path)
            m = genai.GenerativeModel(model_name)
            return f"[VISION]: {m.generate_content(['Analyze code/UI details', img]).text}"
        except Exception as e: return f"Błąd Vision: {e}"
