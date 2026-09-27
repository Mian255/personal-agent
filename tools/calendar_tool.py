"""
Google Calendar & Local Calendar Integration Tool
Supports:
1. Direct .env Configuration (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
2. Live Google Calendar API (OAuth2 Bidirectional Sync)
3. 1-Click Direct Google Calendar Web Links
4. Standard .ICS Export for Apple/Outlook/Google Calendar
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import urllib.parse
from dateutil import parser
from icalendar import Calendar, Event

BASE_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
CALENDAR_FILE = os.path.join(BASE_DATA_DIR, "calendar.json")
ICS_FILE = os.path.join(BASE_DATA_DIR, "agent_calendar.ics")
GOOGLE_CREDS_FILE = os.path.join(BASE_DATA_DIR, "google_credentials.json")
GOOGLE_TOKEN_FILE = os.path.join(BASE_DATA_DIR, "google_token.json")

SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarManager:
    def __init__(self, file_path: str = CALENDAR_FILE):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.events = self._load_local_events()
        self._google_service = None

    def _load_local_events(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_local_events(self):
        with open(self.file_path, "w") as f:
            json.dump(self.events, f, indent=2)
        self.export_ics()

    def _get_client_config(self, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """
        Loads Google OAuth client configuration from .env variables first,
        or falls back to google_credentials.json file.
        """
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        raw_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

        if client_id and client_secret:
            return {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            }
        
        if raw_json:
            try:
                return json.loads(raw_json)
            except Exception:
                pass

        creds_path = GOOGLE_CREDS_FILE if os.path.exists(GOOGLE_CREDS_FILE) else os.path.join(os.path.dirname(__file__), "../credentials.json")
        if os.path.exists(creds_path):
            try:
                with open(creds_path, "r") as f:
                    return json.load(f)
            except Exception:
                return None

        return None

    def is_google_connected(self) -> bool:
        """Checks if Google Calendar OAuth token is valid and connected."""
        return self._get_google_service() is not None

    def _get_google_service(self):
        if self._google_service:
            return self._google_service

        creds = None
        # 1. Check refresh token in .env or token file
        env_refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        if env_refresh_token and client_id and client_secret:
            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                creds = Credentials(
                    None,
                    refresh_token=env_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=SCOPES
                )
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds and os.path.exists(GOOGLE_TOKEN_FILE):
            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open(GOOGLE_TOKEN_FILE, "w") as token_f:
                        token_f.write(creds.to_json())
            except Exception:
                creds = None

        if creds and creds.valid:
            try:
                from googleapiclient.discovery import build
                self._google_service = build('calendar', 'v3', credentials=creds)
                return self._google_service
            except Exception:
                return None
        return None

    def get_google_auth_url(self, redirect_uri: str) -> Optional[str]:
        """Generates Google OAuth consent URL from .env or JSON credentials."""
        config = self._get_client_config(redirect_uri)
        if not config:
            return None

        try:
            from google_auth_oauthlib.flow import Flow
            flow = Flow.from_client_config(
                config,
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
            return auth_url
        except Exception:
            return None

    def exchange_google_code(self, code: str, redirect_uri: str) -> bool:
        """Exchanges OAuth authorization code for credentials token."""
        config = self._get_client_config(redirect_uri)
        if not config:
            return False

        try:
            from google_auth_oauthlib.flow import Flow
            flow = Flow.from_client_config(
                config,
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            flow.fetch_token(code=code)
            creds = flow.credentials
            
            # Save token to file and print refresh token for .env
            with open(GOOGLE_TOKEN_FILE, "w") as token_f:
                token_f.write(creds.to_json())
            self._google_service = None
            return True
        except Exception:
            return False

    def generate_google_web_link(self, title: str, start_dt: datetime, end_dt: datetime, description: str = "", location: str = "") -> str:
        """Generates 1-click Google Calendar instant creation web URL."""
        fmt = "%Y%m%dT%H%M%SZ"
        dates = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": dates,
            "details": description,
            "location": location
        }
        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

    def add_event(
        self,
        title: str,
        start_time_str: str,
        end_time_str: Optional[str] = None,
        description: str = "",
        location: str = ""
    ) -> Dict[str, Any]:
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

        g_link = self.generate_google_web_link(title, start_dt, end_dt, description, location)
        event_id = str(uuid.uuid4())[:8]

        event_data = {
            "id": event_id,
            "title": title,
            "start": start_dt.strftime("%Y-%m-%d %H:%M"),
            "end": end_dt.strftime("%Y-%m-%d %H:%M"),
            "description": description,
            "location": location,
            "google_calendar_link": g_link,
            "source": "local",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        service = self._get_google_service()
        if service:
            try:
                body = {
                    'summary': title,
                    'description': description,
                    'location': location,
                    'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'UTC'},
                    'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'UTC'}
                }
                g_event = service.events().insert(calendarId='primary', body=body).execute()
                event_data["id"] = g_event.get('id', event_id)
                event_data["google_calendar_link"] = g_event.get('htmlLink', g_link)
                event_data["source"] = "google_calendar_live"
            except Exception as e:
                event_data["google_error"] = str(e)

        self.events.append(event_data)
        self._save_local_events()
        return event_data

    def list_events(self, upcoming_days: int = 30) -> List[Dict[str, Any]]:
        service = self._get_google_service()
        if service:
            try:
                now = datetime.utcnow().isoformat() + 'Z'
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=now,
                    maxResults=50,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                items = events_result.get('items', [])
                
                g_events = []
                for item in items:
                    start = item.get('start', {}).get('dateTime', item.get('start', {}).get('date', ''))
                    end = item.get('end', {}).get('dateTime', item.get('end', {}).get('date', ''))
                    g_events.append({
                        "id": item.get('id'),
                        "title": item.get('summary', 'Untitled Event'),
                        "start": start.replace('T', ' ')[:16],
                        "end": end.replace('T', ' ')[:16],
                        "description": item.get('description', ''),
                        "location": item.get('location', ''),
                        "google_calendar_link": item.get('htmlLink', ''),
                        "source": "google_calendar_live"
                    })
                return g_events
            except Exception:
                pass

        def parse_date(e):
            try:
                return parser.parse(e.get("start", ""))
            except Exception:
                return datetime.max
        return sorted(self.events, key=parse_date)

    def delete_event(self, event_id: str) -> bool:
        service = self._get_google_service()
        if service:
            try:
                service.events().delete(calendarId='primary', eventId=event_id).execute()
            except Exception:
                pass

        initial_len = len(self.events)
        self.events = [e for e in self.events if e.get("id") != event_id]
        if len(self.events) < initial_len:
            self._save_local_events()
            return True
        return True

    def export_ics(self) -> str:
        cal = Calendar()
        cal.add("prodid", "-//Personal AI Agent//EN")
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
