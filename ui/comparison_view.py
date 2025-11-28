class ComparisonView:
    def __init__(self, root, engine):
        import customtkinter as ctk
        self.engine = engine
        self.window = ctk.CTkToplevel(root)
        self.window.title("Porównanie modeli")
        self.text = ctk.CTkTextbox(self.window, width=800, height=500)
        self.text.pack(fill="both", expand=True)
    def compare(self, prompt):
        results={}
        for m in self.engine.registry.list():
            results[m] = self.engine.send(prompt, m)
        self.text.insert("end","=== PORÓWNANIE ===\n")
        for m,r in results.items():
            self.text.insert("end", f"[{m}] {r}\n\n")
