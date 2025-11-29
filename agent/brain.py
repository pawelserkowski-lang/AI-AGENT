import os
from typing import Generator

import ollama
from dotenv import load_dotenv

from agent.memory import Memory

load_dotenv()


class AgentService:
    '''Serwis agenta: spina LLM z pamięcią rozmów.'''

    def __init__(self, memory: Memory | None = None):
        self.model = os.getenv('MODEL_NAME', 'llama3')
        self.memory = memory or Memory()
        self.system_prompt = os.getenv('SYSTEM_PROMPT', '')

    def _build_messages(self) -> list[dict]:
        history = self.memory.get_history()
        messages: list[dict] = []

        if self.system_prompt:
            messages.append({
                'role': 'system',
                'content': self.system_prompt,
            })

        messages.extend(history)
        return messages

    def think_stream(self, user_text: str) -> Generator[str, None, None]:
        '''Zapisuje wiadomość użytkownika, woła Ollamę i streamuje odpowiedź.'''

        self.memory.add_message('user', user_text)
        messages = self._build_messages()

        try:
            stream = ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
            )

            full_response = ''
            for chunk in stream:
                content = chunk.get('message', {}).get('content', '')
                if not content:
                    continue
                full_response += content
                yield content

            if full_response.strip():
                self.memory.add_message('assistant', full_response)

        except Exception as e:
            error_msg = f'[Błąd połączenia z modelem: {e}]'
            yield error_msg
