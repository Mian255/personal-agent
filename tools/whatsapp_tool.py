"""
WhatsApp Messaging Tool
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

BASE_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
HISTORY_FILE = os.path.join(BASE_DATA_DIR, "whatsapp_history.json")


class WhatsAppClient:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.default_user_phone = os.getenv("USER_WHATSAPP_PHONE", "")
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.history[-100:], f, indent=2)

    def send_message(self, message: str, to_number: Optional[str] = None) -> Dict[str, Any]:
        target = to_number or self.default_user_phone
        if not target:
            target = "Default Contact"

        formatted_to = target if target.startswith("whatsapp:") else f"whatsapp:{target}"

        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "to": target,
            "message": message,
            "status": "sent"
        }

        if self.account_sid and self.auth_token and not self.account_sid.startswith("your_"):
            try:
                from twilio.rest import Client
                client = Client(self.account_sid, self.auth_token)
                msg = client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=formatted_to
                )
                result["sid"] = msg.sid
                result["status"] = "delivered_via_twilio"
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
        else:
            result["status"] = "simulated_logged (Twilio credentials not set)"

        self.history.append(result)
        self._save_history()
        return result

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.history
