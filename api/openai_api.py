class OpenAIModel:
    def __init__(self, model): self.model=model
    def ask(self,p): return f"(OpenAI:{self.model}) odpowiedź na: {p}"
