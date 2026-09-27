"""
Google Calendar & Local Calendar Integration Tool
"""

import json
import os
import uuid
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import urllib.parse
from dateutil import parser
from icalendar import Calendar, Event
import requests

# Allow HTTP callbacks during local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

BASE_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
CALENDAR_FILE = os.path.join(BASE_DATA_DIR, "calendar.json")
ICS_FILE = os.path.join(BASE_DATA_DIR, "agent_calendar.ics")
GOOGLE_CREDS_FILE = os.path.join(BASE_DATA_DIR, "google_credentials.json")
GOOGLE_TOKEN_FILE = os.path.join(BASE_DATA_DIR, "google_token.json")
OAUTH_STATE_FILE = os.path.join(BASE_DATA_DIR, "oauth_state.json")

SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarManager:
    def __init__(self, file_path: str = CALENDAR_FILE):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.events = self._load_local_events()
        self._google_service = None
        self._oauth_states = self._load_oauth_states()

    def _load_oauth_states(self) -> Dict[str, Any]:
        if os.path.exists(OAUTH_STATE_FILE):
            try:
                with open(OAUTH_STATE_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_oauth_states(self):
        try:
            with open(OAUTH_STATE_FILE, "w") as f:
                json.dump(self._oauth_states, f)
        except Exception:
            pass

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
            
            # Store PKCE code_verifier for exchange
            code_verifier = getattr(flow, 'code_verifier', None)
            if state and code_verifier:
                self._oauth_states[state] = {
                    "code_verifier": code_verifier,
                    "redirect_uri": redirect_uri
                }
            self._oauth_states["_latest"] = {
                "code_verifier": code_verifier,
                "redirect_uri": redirect_uri
            }
            self._save_oauth_states()
            return auth_url
        except Exception as e:
            print("get_google_auth_url error:", e)
            traceback.print_exc()
            return None

    def exchange_google_code(self, code: str, redirect_uri: str, state: Optional[str] = None) -> bool:
        # Load stored code_verifier
        self._oauth_states = self._load_oauth_states()
        state_data = self._oauth_states.get(state) if state else None
        if not state_data:
            state_data = self._oauth_states.get("_latest", {})
        code_verifier = state_data.get("code_verifier") if state_data else None

        # Candidate redirect URIs
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

            # Method 1: Google Flow with restored code_verifier
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
                
                with open(GOOGLE_TOKEN_FILE, "w") as token_f:
                    token_f.write(creds.to_json())
                self._google_service = None
                print(f"Successfully exchanged Google OAuth token using Flow with URI: {uri}")
                return True
            except Exception as e:
                print(f"Flow exchange attempt failed with URI {uri}: {e}")

            # Method 2: Direct token endpoint request fallback
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
                            "token": token_data.get("access_type", token_data.get("access_token")),
                            "refresh_token": token_data.get("refresh_token"),
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "scopes": SCOPES
                        }
                        with open(GOOGLE_TOKEN_FILE, "w") as token_f:
                            json.dump(token_json, token_f, indent=2)
                        self._google_service = None
                        print(f"Successfully exchanged Google OAuth token via direct POST with URI: {uri}")
                        return True
                    else:
                        print(f"Direct token POST failed for URI {uri}: {resp.status_code} {resp.text}")
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
