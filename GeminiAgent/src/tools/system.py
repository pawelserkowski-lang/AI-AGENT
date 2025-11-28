import os
import sqlite3
from rich.table import Table
from src.config import console
from src.core.state import STATE

class FileIO:
    @staticmethod
    def read(path):
        p = STATE.resolve(path)
        try:
            with open(p, 'r', encoding='utf-8') as f: return f"PLIK ({path}):\n```\n{f.read()}\n```"
        except Exception as e: return f"Błąd: {e}"

class DBTool:
    @staticmethod
    def query(db_path, sql):
        path = STATE.resolve(db_path)
        try:
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                rows = cur.fetchall()
                if not rows: return "Brak wyników."
                return str(rows) 
            else:
                conn.commit(); chg = conn.total_changes; conn.close()
                return f"Zmodyfikowano: {chg}"
        except Exception as e: return f"SQL Error: {e}"
