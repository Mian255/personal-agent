"""
Notes, Todos, and Reminders Tool
Powered by Universal DatabaseManager
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from database import db


class NotesManager:
    def __init__(self, file_path: str = None):
        pass

    def add_note(self, title: str, content: str, tag: str = "general") -> Dict[str, Any]:
        note_id = str(uuid.uuid4())[:8]
        db.save_note(note_id, title, content)
        return {
            "id": note_id,
            "title": title,
            "content": content,
            "tag": tag,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    def list_notes(self) -> List[Dict[str, Any]]:
        return db.get_notes()

    def delete_note(self, note_id: str) -> bool:
        return db.delete_note(note_id)

    def add_todo(self, task: str) -> Dict[str, Any]:
        todo_id = str(uuid.uuid4())[:8]
        db.save_todo(todo_id, task, completed=False)
        return {
            "id": todo_id,
            "task": task,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    def list_todos(self) -> List[Dict[str, Any]]:
        return db.get_todos()

    def complete_todo(self, todo_id: str) -> bool:
        todos = db.get_todos()
        for t in todos:
            if t["id"] == todo_id:
                db.save_todo(todo_id, t["task"], completed=True)
                return True
        return False

    def get_all(self) -> Dict[str, Any]:
        return {
            "notes": self.list_notes(),
            "todos": self.list_todos()
        }
