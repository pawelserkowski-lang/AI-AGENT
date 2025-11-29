import os
import sqlite3
from threading import Lock


class Memory:
    '''Prosta pamięć rozmów oparta o SQLite z lockiem pod użycie wielowątkowe.'''

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv('DB_PATH', 'history.db')
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.lock = Lock()
        self._create_table()

    def _create_table(self) -> None:
        query = '''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        '''
        with self.lock:
            self.conn.execute(query)
            self.conn.commit()

    def add_message(self, role: str, content: str) -> None:
        with self.lock:
            self.conn.execute(
                'INSERT INTO messages (role, content) VALUES (?, ?)',
                (role, content),
            )
            self.conn.commit()

    def get_history(self, limit: int | None = None) -> list[dict]:
        if limit is None:
            try:
                limit = int(os.getenv('HISTORY_LIMIT', '50'))
            except ValueError:
                limit = 50

        with self.lock:
            cursor = self.conn.execute(
                'SELECT role, content FROM messages ORDER BY id DESC LIMIT ?',
                (limit,),
            )
            rows = cursor.fetchall()

        return [
            {'role': r[0], 'content': r[1]}
            for r in reversed(rows)
        ]

    def clear(self) -> None:
        with self.lock:
            self.conn.execute('DELETE FROM messages')
            self.conn.commit()

    def close(self) -> None:
        with self.lock:
            try:
                self.conn.close()
            except Exception:
                pass
