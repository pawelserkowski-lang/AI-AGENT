"""
ChatEngine – central routing hub.
"""
class ChatEngine:
    def __init__(self):
        self.history = []
        from api.model_registry import ModelRegistry
        self.registry = ModelRegistry()

    def send(self, prompt, model_name):
        model = self.registry.get(model_name)
        if not model:
            return "Model not found."
        response = model.ask(prompt)
        self.history.append((prompt, response))
        return response
