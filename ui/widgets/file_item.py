import os
from kivymd.uix.card import MDCard
from kivy.properties import StringProperty, BooleanProperty

class FileItem(MDCard):
    filename = StringProperty("")
    filepath = StringProperty("")
    is_image = BooleanProperty(False)
    icon_name = StringProperty("file")
    
    def __init__(self, filepath, remove_func, **kwargs):
        super().__init__(**kwargs)
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.remove_func = remove_func
        
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']:
            self.is_image = True
            self.icon_name = "image"
        elif ext in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.json']:
            self.icon_name = "code-tags"
        else:
            self.icon_name = "file-document-outline"
