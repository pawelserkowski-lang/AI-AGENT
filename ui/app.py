class ChatApp:
    def __init__(self, engine):
        import customtkinter as ctk
        self.engine = engine
        self.root = ctk.CTk()
        self.root.title("Chat Atom Modular")
        from ui.chat_window import ChatWindow
        self.chat = ChatWindow(self.root, engine)
    def run(self):
        self.root.mainloop()
