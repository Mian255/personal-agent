"""
Notes, Todos, and Reminders Tool
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any

BASE_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
NOTES_FILE = os.path.join(BASE_DATA_DIR, "notes.json")


class NotesManager:
    def __init__(self, file_path: str = NOTES_FILE):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except Exception:
                return {"notes": [], "todos": []}
        return {"notes": [], "todos": []}

    def _save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_note(self, title: str, content: str, tag: str = "general") -> Dict[str, Any]:
        note = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "content": content,
            "tag": tag,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.data["notes"].append(note)
        self._save()
        return note

    def list_notes(self) -> List[Dict[str, Any]]:
        return self.data.get("notes", [])

    def add_todo(self, task: str, due_date: str = "") -> Dict[str, Any]:
        todo = {
            "id": str(uuid.uuid4())[:8],
            "task": task,
            "due_date": due_date,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.data["todos"].append(todo)
        self._save()
        return todo

    def list_todos(self) -> List[Dict[str, Any]]:
        return self.data.get("todos", [])

    def complete_todo(self, todo_id: str) -> bool:
        for t in self.data.get("todos", []):
            if t.get("id") == todo_id:
                t["completed"] = True
                self._save()
                return True
        return False
