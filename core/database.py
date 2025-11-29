import sqlite3

class DatabaseManager:
    def __init__(self, db_path="druid_history.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA synchronous = NORMAL;")
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(session_id) REFERENCES sessions(id))""")
        self.conn.commit()
    def create_session(self, title):
        cursor = self.conn.execute("INSERT INTO sessions (title) VALUES (?)", (title,))
        self.conn.commit()
        return cursor.lastrowid
    def delete_session(self, session_id):
        self.conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()
    def get_sessions(self):
        cursor = self.conn.execute("SELECT id, title FROM sessions ORDER BY id DESC")
        return cursor.fetchall()
    def add_message(self, session_id, role, content):
        self.conn.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
        self.conn.commit()
    def get_messages(self, session_id):
        cursor = self.conn.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
        return [{"role": r[0], "content": r[1]} for r in cursor.fetchall()]
    def get_context_messages(self, session_id, limit=20):
        cursor = self.conn.execute(f"SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT {limit}", (session_id,))
        rows = cursor.fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
