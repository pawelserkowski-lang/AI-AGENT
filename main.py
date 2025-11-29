import threading

from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from agent.brain import AgentService
from ui.widgets import ChatBubble


class MainScreen(MDScreen):
    '''Główny ekran czatu z lokalnym agentem AI.'''

    def __init__(self, agent, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent
        self.thinking = False
        self.current_ai_bubble = None

        # historia ładowana po zbudowaniu KV
        Clock.schedule_once(self.load_history, 0)

    def load_history(self, dt):
        try:
            history = self.agent.memory.get_history(limit=50)
            for msg in history:
                role = msg.get('role')
                if role == 'system':
                    continue
                content = msg.get('content', '')
                is_user = role == 'user'
                self.add_bubble(content, is_user, scroll=False)
            self.scroll_to_bottom()
        except Exception as e:
            print(f'Błąd ładowania historii: {e}')

    def send_message(self):
        if self.thinking:
            return

        text = self.ids.user_input.text.strip()
        if not text:
            return

        self.ids.user_input.text = ''
        self.add_bubble(text, is_user=True)
        self.thinking = True
        self.ids.loading_spinner.active = True

        thread = threading.Thread(
            target=self._run_agent_task,
            args=(text,),
            daemon=True,
        )
        thread.start()

    def _run_agent_task(self, text: str):
        # przygotuj placeholder na odpowiedź AI
        self.create_ai_bubble_placeholder()
        try:
            stream = self.agent.think_stream(text)
            full_text = ''
            for chunk in stream:
                full_text += chunk
                self.update_ai_bubble(full_text)
        except Exception as e:
            self.update_ai_bubble(f'Error: {e}')
        finally:
            self.finish_agent_task()

    @mainthread
    def add_bubble(self, text: str, is_user: bool, scroll: bool = True):
        bubble = ChatBubble(text=text, is_user=is_user)
        self.ids.chat_list.add_widget(bubble)
        if scroll:
            self.scroll_to_bottom()

    @mainthread
    def create_ai_bubble_placeholder(self):
        self.current_ai_bubble = ChatBubble(text='...', is_user=False)
        self.ids.chat_list.add_widget(self.current_ai_bubble)
        self.scroll_to_bottom()

    @mainthread
    def update_ai_bubble(self, text: str):
        if self.current_ai_bubble is not None:
            self.current_ai_bubble.update_text(text)
            self.scroll_to_bottom()

    @mainthread
    def finish_agent_task(self):
        self.thinking = False
        self.ids.loading_spinner.active = False
        self.current_ai_bubble = None

    @mainthread
    def scroll_to_bottom(self):
        # przewiń na dół po następnym cyklu, gdy layout się przeliczy
        def _scroll(_dt):
            self.ids.scroll_view.scroll_y = 0
        Clock.schedule_once(_scroll, 0)


class LocalAIAgentApp(MDApp):
    def build(self):
        self.title = 'Local AI Agent (KivyMD + Ollama)'
        self.theme_cls.primary_palette = 'BlueGray'
        self.theme_cls.theme_style = 'Light'

        Builder.load_file('ui/layout.kv')

        self.agent = AgentService()
        return MainScreen(agent=self.agent)

    def on_stop(self):
        # grzecznie zamknij połączenie z bazą
        memory = getattr(self.agent, 'memory', None)
        if memory is not None:
            try:
                memory.close()
            except Exception as e:
                print(f'Błąd zamykania bazy: {e}')


if __name__ == '__main__':
    LocalAIAgentApp().run()
