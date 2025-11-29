# Local AI Agent KivyMD

Lokalny agent AI z UI w KivyMD, backendem w Pythonie i LLM-em przez Ollama.

## Wymagania
- Python 3.10+
- Zainstalowana Ollama i pobrany model, np. `ollama pull llama3`

## Instalacja

```bash
pip install -r requirements.txt
```

## Konfiguracja

Ustaw zmienne w `.env`:
- `MODEL_NAME` – nazwa modelu w Ollama (np. `llama3`)
- `DB_PATH` – ścieżka do bazy SQLite z historią (domyślnie `history.db`)
- `HISTORY_LIMIT` – maksymalna liczba wiadomości w kontekście
- `SYSTEM_PROMPT` – prompt systemowy dla agenta

## Uruchomienie

```bash
python main.py
```
