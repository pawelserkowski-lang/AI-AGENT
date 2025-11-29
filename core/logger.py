import logging
from kivy.clock import Clock

class KivyLogHandler(logging.Handler):
    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance
    def emit(self, record):
        msg = self.format(record)
        if self.app: Clock.schedule_once(lambda dt: self.app.append_log(msg), 0)
