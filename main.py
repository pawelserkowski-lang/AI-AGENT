"""
Entry point for Chat Atom Modular.
Initializes UI, logging, and model registry.
"""
from core.engine import ChatEngine
from ui.app import ChatApp

def main():
    engine = ChatEngine()
    app = ChatApp(engine)
    app.run()

if __name__ == "__main__":
    main()
