"""
Universal Database Manager for Personal AI Agent
Supports zero-config local SQLite (default) and cloud PostgreSQL (Supabase, Neon, Render).
"""

import os
import json
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

BASE_DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
SQLITE_DB_PATH = os.path.join(BASE_DATA_DIR, "agent.db")


class DatabaseManager:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "")
        self.is_postgres = bool(self.db_url and (self.db_url.startswith("postgres://") or self.db_url.startswith("postgresql://")))
        
        if not self.is_postgres:
            os.makedirs(BASE_DATA_DIR, exist_ok=True)
            self.sqlite_path = SQLITE_DB_PATH
        
        self._init_db()

    def _get_connection(self):
        if self.is_postgres:
            try:
                import psycopg2
                import psycopg2.extras
                conn = psycopg2.connect(self.db_url, cursor_factory=psycopg2.extras.RealDictCursor)
                return conn
            except Exception as e:
                print(f"PostgreSQL connection error: {e}. Falling back to local SQLite.")
                self.is_postgres = False
                os.makedirs(BASE_DATA_DIR, exist_ok=True)
                self.sqlite_path = SQLITE_DB_PATH
        
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _fmt(self, query: str) -> str:
        if self.is_postgres:
            return query.replace("?", "%s")
        return query

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        pk_type = "SERIAL PRIMARY KEY" if self.is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id {pk_type},
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id TEXT PRIMARY KEY,
            task TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            description TEXT,
            location TEXT,
            google_calendar_link TEXT,
            source TEXT DEFAULT 'local',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS whatsapp_messages (
            id {pk_type},
            to_number TEXT NOT NULL,
            from_number TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id {pk_type},
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()
        conn.close()

    def save_chat_message(self, role: str, content: str, session_id: str = "default", tool_calls: Optional[List[Any]] = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        tools_json = json.dumps(tool_calls) if tool_calls else None
        cursor.execute(
            self._fmt("INSERT INTO chat_messages (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)"),
            (session_id, role, content, tools_json)
        )
        conn.commit()
        conn.close()

    def get_chat_history(self, session_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            self._fmt("SELECT id, session_id, role, content, tool_calls, created_at FROM chat_messages WHERE session_id = ? ORDER BY id ASC LIMIT ?"),
            (session_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()

        history = []
        for r in rows:
            tools = None
            if r["tool_calls"]:
                try:
                    tools = json.loads(r["tool_calls"])
                except Exception:
                    pass
            history.append({
                "id": r["id"],
                "session_id": r["session_id"],
                "role": r["role"],
                "content": r["content"],
                "tool_calls": tools,
                "created_at": str(r["created_at"])
            })
        return history

    def clear_chat_history(self, session_id: str = "default"):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("DELETE FROM chat_messages WHERE session_id = ?"), (session_id,))
        conn.commit()
        conn.close()

    def add_activity_log(self, log_type: str, message: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("INSERT INTO activity_logs (type, message) VALUES (?, ?)"), (log_type, message))
        conn.commit()
        conn.close()

    def get_activity_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("SELECT id, type, message, timestamp FROM activity_logs ORDER BY id DESC LIMIT ?"), (limit,))
        rows = cursor.fetchall()
        conn.close()

        logs = []
        for r in rows:
            logs.append({
                "id": r["id"],
                "type": r["type"],
                "message": r["message"],
                "timestamp": str(r["timestamp"])[:19]
            })
        return logs

    def set_setting(self, key: str, value: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("""
        INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """), (key, value))
        conn.commit()
        conn.close()

    def get_setting(self, key: str) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("SELECT value FROM settings WHERE key = ?"), (key,))
        row = cursor.fetchone()
        conn.close()
        return row["value"] if row else None

    def delete_setting(self, key: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("DELETE FROM settings WHERE key = ?"), (key,))
        conn.commit()
        conn.close()

    def save_note(self, note_id: str, title: str, content: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("""
        INSERT INTO notes (id, title, content, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET title = excluded.title, content = excluded.content
        """), (note_id, title, content))
        conn.commit()
        conn.close()

    def get_notes(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("SELECT id, title, content, created_at FROM notes ORDER BY created_at DESC"))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r["id"], "title": r["title"], "content": r["content"], "created_at": str(r["created_at"])[:16]} for r in rows]

    def delete_note(self, note_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("DELETE FROM notes WHERE id = ?"), (note_id,))
        conn.commit()
        conn.close()
        return True

    def save_todo(self, todo_id: str, task: str, completed: bool = False):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("""
        INSERT INTO todos (id, task, completed, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET task = excluded.task, completed = excluded.completed
        """), (todo_id, task, int(completed)))
        conn.commit()
        conn.close()

    def get_todos(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("SELECT id, task, completed, created_at FROM todos ORDER BY created_at DESC"))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r["id"], "task": r["task"], "completed": bool(r["completed"]), "created_at": str(r["created_at"])[:16]} for r in rows]

    def delete_todo(self, todo_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("DELETE FROM todos WHERE id = ?"), (todo_id,))
        conn.commit()
        conn.close()
        return True

    def save_calendar_event(self, event_data: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("""
        INSERT INTO calendar_events (id, title, start_time, end_time, description, location, google_calendar_link, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET title=excluded.title, start_time=excluded.start_time, end_time=excluded.end_time,
                                      description=excluded.description, location=excluded.location, google_calendar_link=excluded.google_calendar_link, source=excluded.source
        """), (
            event_data.get("id"),
            event_data.get("title"),
            event_data.get("start"),
            event_data.get("end"),
            event_data.get("description", ""),
            event_data.get("location", ""),
            event_data.get("google_calendar_link", ""),
            event_data.get("source", "local")
        ))
        conn.commit()
        conn.close()

    def get_calendar_events(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("SELECT id, title, start_time as start, end_time as end, description, location, google_calendar_link, source FROM calendar_events ORDER BY start_time ASC"))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_calendar_event(self, event_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("DELETE FROM calendar_events WHERE id = ?"), (event_id,))
        conn.commit()
        conn.close()
        return True

    def save_whatsapp_message(self, to_num: str, from_num: str, msg: str, status: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            self._fmt("INSERT INTO whatsapp_messages (to_number, from_number, message, status) VALUES (?, ?, ?, ?)"),
            (to_num, from_num, msg, status)
        )
        conn.commit()
        conn.close()

    def get_whatsapp_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(self._fmt("""SELECT id, to_number as "to", from_number as "from", message, status, timestamp FROM whatsapp_messages ORDER BY id DESC LIMIT ?"""), (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r["id"], "to": r["to"], "from": r["from"], "message": r["message"], "status": r["status"], "timestamp": str(r["timestamp"])[:19]} for r in rows]

db = DatabaseManager()
