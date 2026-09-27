"""
Calendar & Task Scheduling Tool
Supports managing local events, upcoming agenda, and ICS file export (importable to Google/Apple/Outlook Calendar).
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dateutil import parser
from icalendar import Calendar, Event

CALENDAR_FILE = os.path.expanduser("/Users/pl/projects/personal-agent/data/calendar.json")
ICS_FILE = os.path.expanduser("/Users/pl/projects/personal-agent/data/agent_calendar.ics")


class CalendarManager:
    def __init__(self, file_path: str = CALENDAR_FILE):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.events = self._load_events()

    def _load_events(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_events(self):
        with open(self.file_path, "w") as f:
            json.dump(self.events, f, indent=2)
        self.export_ics()

    def add_event(
        self,
        title: str,
        start_time_str: str,
        end_time_str: Optional[str] = None,
        description: str = "",
        location: str = ""
    ) -> Dict[str, Any]:
        """
        Schedules a new calendar event.
        Time strings can be natural like '2026-09-28 15:00', 'tomorrow 3pm', etc.
        """
        try:
            start_dt = parser.parse(start_time_str, fuzzy=True)
        except Exception:
            start_dt = datetime.now() + timedelta(hours=1)

        if end_time_str:
            try:
                end_dt = parser.parse(end_time_str, fuzzy=True)
            except Exception:
                end_dt = start_dt + timedelta(hours=1)
        else:
            end_dt = start_dt + timedelta(hours=1)

        event_id = str(uuid.uuid4())[:8]
        new_event = {
            "id": event_id,
            "title": title,
            "start": start_dt.strftime("%Y-%m-%d %H:%M"),
            "end": end_dt.strftime("%Y-%m-%d %H:%M"),
            "description": description,
            "location": location,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.events.append(new_event)
        self._save_events()
        return new_event

    def list_events(self, upcoming_days: int = 30) -> List[Dict[str, Any]]:
        """Lists events sorted by date."""
        def parse_date(e):
            try:
                return parser.parse(e.get("start", ""))
            except Exception:
                return datetime.max
        return sorted(self.events, key=parse_date)

    def delete_event(self, event_id: str) -> bool:
        """Deletes an event by ID."""
        initial_len = len(self.events)
        self.events = [e for e in self.events if e.get("id") != event_id]
        if len(self.events) < initial_len:
            self._save_events()
            return True
        return False

    def export_ics(self) -> str:
        """Generates standard .ics file for Google Calendar / Apple Calendar."""
        cal = Calendar()
        cal.add("prodid", "-//AetherMind Personal AI Agent//EN")
        cal.add("version", "2.0")

        for item in self.events:
            event = Event()
            event.add("summary", item.get("title", "Event"))
            event.add("uid", item.get("id", str(uuid.uuid4())))
            try:
                dt_start = parser.parse(item.get("start"))
                dt_end = parser.parse(item.get("end"))
                event.add("dtstart", dt_start)
                event.add("dtend", dt_end)
            except Exception:
                continue
            if item.get("description"):
                event.add("description", item.get("description"))
            if item.get("location"):
                event.add("location", item.get("location"))
            cal.add_component(event)

        with open(ICS_FILE, "wb") as f:
            f.write(cal.to_ical())
        return ICS_FILE
