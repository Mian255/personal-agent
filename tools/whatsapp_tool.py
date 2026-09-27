"""
WhatsApp Messaging Tool (Meta Cloud API & Twilio Supported)
Powered by Universal DatabaseManager
"""

import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from database import db


class WhatsAppClient:
    def __init__(self):
        self.provider = os.getenv("WHATSAPP_PROVIDER", "meta").lower()
        # Meta Official Cloud API Credentials
        self.meta_token = os.getenv("META_WHATSAPP_TOKEN", "")
        self.meta_phone_id = os.getenv("META_PHONE_NUMBER_ID", "")
        self.meta_business_id = os.getenv("META_WHATSAPP_BUSINESS_ACCOUNT_ID", "")

        # Twilio API Credentials
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

        self.default_user_phone = os.getenv("USER_WHATSAPP_PHONE", "")

    def send_message(self, message: str, to_number: Optional[str] = None) -> Dict[str, Any]:
        target = to_number or self.default_user_phone

        if not target:
            return {"status": "failed", "error": "No recipient phone number provided or set in USER_WHATSAPP_PHONE."}

        clean_target = target.replace("whatsapp:", "").replace("+", "").replace(" ", "").replace("-", "")

        # 1. Meta Official WhatsApp Cloud API Dispatch
        if self.meta_token and self.meta_phone_id and not self.meta_token.startswith("your_"):
            try:
                url = f"https://graph.facebook.com/v19.0/{self.meta_phone_id}/messages"
                headers = {
                    "Authorization": f"Bearer {self.meta_token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": clean_target,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": message
                    }
                }
                resp = requests.post(url, json=payload, headers=headers, timeout=10)
                if resp.status_code in [200, 201]:
                    db.save_whatsapp_message(target, self.meta_phone_id, message, "sent_via_meta")
                    return {
                        "status": "sent",
                        "provider": "meta",
                        "to": target,
                        "response": resp.json(),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                else:
                    print("Meta WhatsApp send error:", resp.status_code, resp.text)
                    db.save_whatsapp_message(target, self.meta_phone_id, message, f"meta_error_{resp.status_code}")
                    return {"status": "failed", "error": resp.text}
            except Exception as e:
                db.save_whatsapp_message(target, self.meta_phone_id, message, f"failed: {e}")
                return {"status": "failed", "error": str(e)}

        # 2. Twilio API Dispatch Fallback
        if self.account_sid and self.auth_token and not self.account_sid.startswith("your_"):
            try:
                from twilio.rest import Client
                twilio_target = target if target.startswith("whatsapp:") else f"whatsapp:{target}"
                client = Client(self.account_sid, self.auth_token)
                msg = client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=twilio_target
                )
                status = "sent" if msg.sid else "queued"
                db.save_whatsapp_message(twilio_target, self.from_number, message, status)
                return {
                    "status": status,
                    "provider": "twilio",
                    "sid": msg.sid,
                    "to": twilio_target,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            except Exception as e:
                db.save_whatsapp_message(target, self.from_number, message, f"failed: {e}")
                return {"status": "failed", "error": str(e)}

        # 3. Simulated Sandbox Dispatch
        status = "simulated_sent (Configure META_WHATSAPP_TOKEN or TWILIO_ACCOUNT_SID in .env)"
        db.save_whatsapp_message(target, "simulator", message, status)
        return {
            "status": status,
            "to": target,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_messages(self) -> List[Dict[str, Any]]:
        return db.get_whatsapp_messages()
