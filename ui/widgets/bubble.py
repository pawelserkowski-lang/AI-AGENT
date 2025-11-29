from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty, BooleanProperty
from kivy.core.clipboard import Clipboard
from kivymd.toast import toast

class ChatBubble(MDBoxLayout):
    text = StringProperty("")
    is_user = BooleanProperty(True)
    
    def copy_content(self):
        Clipboard.copy(self.text)
        toast("Skopiowano")
