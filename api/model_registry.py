class ModelRegistry:
    def __init__(self):
        from api.openai_api import OpenAIModel
        from api.gemini_api import GeminiModel
        from api.anthropic_api import AnthropicModel
        from api.cohere_api import CohereModel
        self.models = {
            "openai:gpt-4.1": OpenAIModel("gpt-4.1"),
            "openai:gpt-4.1-mini": OpenAIModel("gpt-4.1-mini"),
            "gemini:pro": GeminiModel(),
            "anthropic:claude-3": AnthropicModel(),
            "cohere:command-r": CohereModel(),
        }
    def list(self):
        return list(self.models.keys())
    def get(self, name):
        return self.models.get(name)
