from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.properties import StringProperty, NumericProperty

class SessionItem(OneLineAvatarIconListItem):
    session_id = NumericProperty(0)
    title = StringProperty("")
