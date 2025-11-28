class ChatWindow:
    def __init__(self, root, engine):
        import customtkinter as ctk
        self.engine = engine
        self.frame = ctk.CTkFrame(root)
        self.frame.pack(fill="both", expand=True)
        self.text = ctk.CTkTextbox(self.frame, width=600, height=400)
        self.text.pack(padx=10, pady=10, fill="both", expand=True)
        self.entry = ctk.CTkEntry(self.frame, placeholder_text="Napisz wiadomość...")
        self.entry.pack(fill="x", padx=10)
        btn = ctk.CTkButton(self.frame, text="Wyślij", command=self.send)
        btn.pack(pady=10)
    def send(self):
        prompt=self.entry.get()
        if not prompt: return
        response=self.engine.send(prompt,"openai:gpt-4.1")
        self.text.insert("end", f"Ty: {prompt}\nAI: {response}\n\n")
        self.entry.delete(0,"end")
