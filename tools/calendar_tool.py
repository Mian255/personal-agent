"""
Google Calendar & Local Calendar Integration Tool
Production-ready secure integration with in-memory PKCE state & live 2-way sync
"""

import json
import os
import time
import uuid
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import urllib.parse
from dateutil import parser
from icalendar import Calendar, Event
import requests
from database import db

# Allow HTTP callbacks during local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

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
        # Transient in-memory OAuth PKCE handshake storage (never written to disk)
        self._oauth_states: Dict[str, Dict[str, Any]] = {}

    def _cleanup_expired_oauth_states(self):
        """Purge temporary PKCE states older than 10 minutes."""
        now = time.time()
        expired_keys = [k for k, v in self._oauth_states.items() if now - v.get("created_at", 0) > 600]
        for k in expired_keys:
            self._oauth_states.pop(k, None)

    def _load_local_events(self) -> List[Dict[str, Any]]:
        try:
            return db.get_calendar_events()
        except Exception:
            return []

    def _save_local_events(self):
        pass

    def _get_client_config(self, redirect_uri: str) -> Optional[Dict[str, Any]]:
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
                    "redirect_uris": [
                        redirect_uri,
                        "http://localhost:8000/api/calendar/google/callback",
                        "http://127.0.0.1:8000/api/calendar/google/callback"
                    ]
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

    def disconnect_google(self) -> bool:
        """Safely revoke / delete tokens from database and disconnect service."""
        try:
            db.delete_setting("google_token_json")
            if os.path.exists(GOOGLE_TOKEN_FILE):
                os.remove(GOOGLE_TOKEN_FILE)
            self._google_service = None
            return True
        except Exception as e:
            print("Error disconnecting Google account:", e)
            return False

    def is_google_connected(self) -> bool:
        return self._get_google_service() is not None

    def _get_google_service(self):
        if self._google_service:
            return self._google_service

        creds = None
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

        # Check database settings store
        if not creds:
            try:
                db_token_str = db.get_setting("google_token_json")
                if db_token_str:
                    from google.oauth2.credentials import Credentials
                    from google.auth.transport.requests import Request
                    token_info = json.loads(db_token_str)
                    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        db.set_setting("google_token_json", creds.to_json())
            except Exception as e:
                print("DB token load error:", e)
                creds = None

        # Fallback to local token file if exists (and migrate to DB)
        if not creds and os.path.exists(GOOGLE_TOKEN_FILE):
            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
                if creds:
                    db.set_setting("google_token_json", creds.to_json())
                    os.remove(GOOGLE_TOKEN_FILE)
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
            auth_url, state = flow.authorization_url(
                prompt='consent',
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store transient PKCE state in memory
            self._cleanup_expired_oauth_states()
            code_verifier = getattr(flow, 'code_verifier', None)
            state_payload = {
                "code_verifier": code_verifier,
                "redirect_uri": redirect_uri,
                "created_at": time.time()
            }
            if state:
                self._oauth_states[state] = state_payload
            self._oauth_states["_latest"] = state_payload

            return auth_url
        except Exception as e:
            print("get_google_auth_url error:", e)
            traceback.print_exc()
            return None

    def exchange_google_code(self, code: str, redirect_uri: str, state: Optional[str] = None) -> bool:
        self._cleanup_expired_oauth_states()
        state_data = self._oauth_states.pop(state, None) if state else None
        if not state_data:
            state_data = self._oauth_states.pop("_latest", {})
        code_verifier = state_data.get("code_verifier") if state_data else None

        possible_uris = [
            redirect_uri,
            redirect_uri.replace("127.0.0.1", "localhost") if "127.0.0.1" in redirect_uri else redirect_uri.replace("localhost", "127.0.0.1"),
            "http://localhost:8000/api/calendar/google/callback",
            "http://127.0.0.1:8000/api/calendar/google/callback"
        ]

        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        for uri in possible_uris:
            config = self._get_client_config(uri)
            if not config:
                continue

            # Method 1: Google Flow with in-memory code_verifier
            try:
                from google_auth_oauthlib.flow import Flow
                flow = Flow.from_client_config(
                    config,
                    scopes=SCOPES,
                    redirect_uri=uri
                )
                if code_verifier:
                    flow.code_verifier = code_verifier

                flow.fetch_token(code=code)
                creds = flow.credentials
                
                db.set_setting("google_token_json", creds.to_json())
                if os.path.exists(GOOGLE_TOKEN_FILE):
                    os.remove(GOOGLE_TOKEN_FILE)
                self._google_service = None
                print(f"Successfully exchanged Google OAuth token using Flow with URI: {uri}")
                return True
            except Exception as e:
                print(f"Flow exchange attempt failed with URI {uri}: {e}")

            # Method 2: Direct HTTP Token Endpoint fallback
            if client_id and client_secret:
                try:
                    payload = {
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": uri,
                        "grant_type": "authorization_code"
                    }
                    if code_verifier:
                        payload["code_verifier"] = code_verifier
                    
                    resp = requests.post("https://oauth2.googleapis.com/token", data=payload, timeout=10)
                    if resp.status_code == 200:
                        token_data = resp.json()
                        token_json = {
                            "token": token_data.get("access_token"),
                            "refresh_token": token_data.get("refresh_token"),
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "scopes": SCOPES
                        }
                        db.set_setting("google_token_json", json.dumps(token_json))
                        if os.path.exists(GOOGLE_TOKEN_FILE):
                            os.remove(GOOGLE_TOKEN_FILE)
                        self._google_service = None
                        print(f"Successfully exchanged Google OAuth token via direct POST with URI: {uri}")
                        return True
                except Exception as e2:
                    print(f"Direct exchange failed: {e2}")

        return False

    def generate_google_web_link(self, title: str, start_dt: datetime, end_dt: datetime, description: str = "", location: str = "") -> str:
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
                cal_info = service.calendars().get(calendarId='primary').execute()
                cal_tz = cal_info.get('timeZone', 'UTC')
                body = {
                    'summary': title,
                    'description': description,
                    'location': location,
                    'start': {'dateTime': start_dt.isoformat(), 'timeZone': cal_tz},
                    'end': {'dateTime': end_dt.isoformat(), 'timeZone': cal_tz}
                }
                g_event = service.events().insert(calendarId='primary', body=body).execute()
                event_data["id"] = g_event.get('id', event_id)
                event_data["google_calendar_link"] = g_event.get('htmlLink', g_link)
                event_data["source"] = "google_calendar_live"
            except Exception as e:
                print("Google Calendar insert error:", e)
                event_data["google_error"] = str(e)

        db.save_calendar_event(event_data)
        return event_data

    def list_events(self, upcoming_days: int = 30) -> List[Dict[str, Any]]:
        service = self._get_google_service()
        if service:
            try:
                now_min = (datetime.utcnow() - timedelta(hours=24)).isoformat() + 'Z'
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=now_min,
                    maxResults=100,
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

        local_evs = db.get_calendar_events()
        def parse_date(e):
            try:
                return parser.parse(e.get("start", ""))
            except Exception:
                return datetime.max
        return sorted(local_evs, key=parse_date)

    def delete_event(self, event_id: str) -> bool:
        service = self._get_google_service()
        if service:
            try:
                service.events().delete(calendarId='primary', eventId=event_id).execute()
            except Exception:
                pass

        db.delete_calendar_event(event_id)
        return True

    def export_ics_bytes(self) -> bytes:
        cal = Calendar()
        cal.add("prodid", "-//Personal AI Agent//EN")
        cal.add("version", "2.0")

        events_to_export = self.list_events()
        for item in events_to_export:
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

        return cal.to_ical()
