"""
Personal AI Agent - Multi-Tool Web Dashboard & API Server
"""

import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, Response
from pydantic import BaseModel

from llm import LLMClient
from agent import PersonalAgent
from database import db

load_dotenv()

app = FastAPI(title="Personal AI Agent Hub")

agent_name = os.getenv("AGENT_NAME", "AI Assistant")
user_name = os.getenv("USER_NAME", "User")
agent = PersonalAgent(name=agent_name, user_name=user_name)

activity_logs: List[Dict[str, Any]] = [
    {
        "id": 1,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "type": "system",
        "message": f"Personal Agent '{agent.name}' online with multi-tool capabilities."
    }
]

stats = {
    "chats_count": 0,
    "events_scheduled": 0,
    "whatsapp_sent": 0,
    "moltbook_posts": 0,
    "moltbook_comments": 0,
    "scheduler_runs": 0,
}

scheduler_state = {
    "enabled": False,
    "interval_minutes": 60,
    "last_run": None,
    "status": "Stopped"
}

def log_activity(activity_type: str, message: str, meta: Optional[Dict[str, Any]] = None):
    activity_logs.insert(0, {
        "id": len(activity_logs) + 1,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "type": activity_type,
        "message": message,
        "meta": meta or {}
    })
    if len(activity_logs) > 100:
        activity_logs.pop()
    try:
        db.add_activity_log(activity_type, message)
    except Exception:
        pass

def scheduler_worker():
    while True:
        if scheduler_state["enabled"]:
            now = datetime.now()
            log_activity("scheduler", "⏰ Scheduler triggered autonomous heartbeat.")
            try:
                # 1. Moltbook social check
                logs = agent.moltbook_auto_engage(max_comments=1, auto_upvote=True)
                for l in logs:
                    log_activity("moltbook", l)
                
                # 2. Check calendar reminders
                events = agent.calendar.list_events()
                log_activity("calendar", f"Heartbeat: Synced {len(events)} calendar events.")
                
                stats["scheduler_runs"] += 1
                scheduler_state["last_run"] = now.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                log_activity("error", f"Scheduler execution error: {e}")
            
            interval_sec = scheduler_state["interval_minutes"] * 60
            time.sleep(interval_sec)
        else:
            time.sleep(2)

scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
scheduler_thread.start()

# Request Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class CalendarEventRequest(BaseModel):
    title: str
    start_time: str
    end_time: Optional[str] = None
    description: Optional[str] = ""
    location: Optional[str] = ""

class WhatsAppSendRequest(BaseModel):
    message: str
    to_number: Optional[str] = None

class MoltbookRegisterRequest(BaseModel):
    name: str
    description: str

class MoltbookPublishRequest(BaseModel):
    title: str
    content: str
    submolt: Optional[str] = None

class SchedulerConfigRequest(BaseModel):
    enabled: bool
    interval_minutes: int

def get_oauth_redirect_uri(request: Request) -> str:
    host = request.headers.get("host", "localhost:8000")
    if "0.0.0.0" in host:
        host = host.replace("0.0.0.0", "localhost")
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    return f"{proto}://{host}/api/calendar/google/callback"

# --- API Endpoints ---
@app.get("/api/status")
def get_status():
    return {
        "agent_name": agent.name,
        "user_name": agent.user_name,
        "provider": agent.llm.provider,
        "model": agent.llm.model,
        "moltbook_key_set": bool(agent.moltbook.api_key),
        "google_calendar_configured": bool(os.getenv("GOOGLE_CLIENT_ID") or os.path.exists(os.path.join(os.path.dirname(__file__), "data/google_credentials.json"))),
        "google_calendar_connected": agent.calendar.is_google_connected(),
        "whatsapp_configured": bool(agent.whatsapp.account_sid and not agent.whatsapp.account_sid.startswith("your_")),
        "stats": stats,
        "scheduler": scheduler_state
    }

@app.get("/api/chat/history")
def get_chat_history(session_id: str = "default"):
    return {"messages": db.get_chat_history(session_id=session_id)}

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    try:
        session_id = req.session_id or "default"
        # Save user message to DB
        db.save_chat_message("user", req.message, session_id=session_id)

        result = agent.chat(req.message)
        stats["chats_count"] += 1
        
        tool_names = []
        if result.get("tool_executed"):
            tool_name = result["tool_executed"]["tool"]
            tool_names.append(tool_name)
            log_activity(tool_name, f"Tool executed: {tool_name}")
            if "calendar" in tool_name:
                stats["events_scheduled"] += 1
            elif "whatsapp" in tool_name:
                stats["whatsapp_sent"] += 1
            elif "moltbook" in tool_name:
                stats["moltbook_posts"] += 1
        elif result.get("all_tools_executed"):
            for t in result["all_tools_executed"]:
                tool_names.append(t.get("tool", "tool"))
        else:
            log_activity("chat", f"User: {req.message[:50]}...")

        # Save assistant message to DB
        db.save_chat_message("assistant", result["reply"], tool_calls=tool_names, session_id=session_id)

        return result
    except Exception as e:
        log_activity("error", f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/clear")
def clear_chat(session_id: str = "default"):
    agent.clear_history()
    db.clear_chat_history(session_id=session_id)
    log_activity("system", "Conversation cleared.")
    return {"status": "cleared"}

# Calendar Endpoints
@app.get("/api/calendar")
def list_calendar():
    return {
        "events": agent.calendar.list_events(),
        "google_connected": agent.calendar.is_google_connected()
    }

@app.post("/api/calendar")
@app.post("/api/calendar/event")
def add_calendar_event(req: CalendarEventRequest):
    event = agent.calendar.add_event(
        title=req.title,
        start_time_str=req.start_time,
        end_time_str=req.end_time,
        description=req.description or "",
        location=req.location or ""
    )
    stats["events_scheduled"] += 1
    log_activity("calendar", f"Scheduled event: '{event['title']}' ({event.get('source', 'local')})")
    return event

@app.delete("/api/calendar/{event_id}")
def delete_calendar_event(event_id: str):
    success = agent.calendar.delete_event(event_id)
    if success:
        log_activity("calendar", f"Deleted calendar event ID {event_id}")
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Event not found")

@app.post("/api/calendar/google/disconnect")
def google_calendar_disconnect():
    success = agent.calendar.disconnect_google()
    log_activity("calendar", "🔴 Google Calendar disconnected / signed out")
    return {"status": "disconnected", "success": success}

@app.get("/api/calendar/google/login")
def google_calendar_login(request: Request):
    """Direct redirect to Google OAuth authorization."""
    redirect_uri = get_oauth_redirect_uri(request)
    auth_url = agent.calendar.get_google_auth_url(redirect_uri)
    if not auth_url:
        return RedirectResponse(url="/?google_auth=missing_credentials")
    return RedirectResponse(url=auth_url)

@app.get("/api/calendar/google/callback")
def google_calendar_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    if error:
        return RedirectResponse(url=f"/?google_auth=error&reason={error}")
    if not code:
        return RedirectResponse(url="/?google_auth=failed&reason=Missing+authorization+code")
    redirect_uri = get_oauth_redirect_uri(request)
    success = agent.calendar.exchange_google_code(code, redirect_uri, state=state)
    if success:
        log_activity("calendar", "🟢 Google Calendar connected successfully via OAuth2!")
        return RedirectResponse(url="/?google_auth=success")
    return RedirectResponse(url="/?google_auth=failed&reason=Token+exchange+failed")

@app.get("/api/calendar/export.ics")
def export_calendar_ics():
    ics_bytes = agent.calendar.export_ics_bytes()
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=agent_calendar.ics"}
    )

# WhatsApp Endpoints
@app.get("/api/whatsapp/messages")
def get_whatsapp_messages():
    return {"messages": agent.whatsapp.get_messages()}

@app.post("/api/whatsapp/send")
def send_whatsapp(req: WhatsAppSendRequest):
    res = agent.whatsapp.send_message(req.message, req.to_number)
    stats["whatsapp_sent"] += 1
    log_activity("whatsapp", f"Dispatched WhatsApp to {res['to']}: {req.message[:40]}...")
    return res

@app.get("/api/whatsapp/webhook")
def whatsapp_meta_verify(request: Request):
    """
    Meta Webhook Verification Handshake
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    verify_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "bob_whatsapp_verify_token_2026")
    if mode == "subscribe" and token == verify_token:
        print("Meta WhatsApp Webhook verified successfully!")
        return Response(content=str(challenge), media_type="text/plain")
    return Response(content="Verification failed", status_code=403)

@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Inbound WhatsApp Assistant Handler (Meta Cloud API & Twilio Supported)
    Direct control of the AI agent from your WhatsApp phone.
    """
    content_type = request.headers.get("content-type", "")

    # 1. Meta WhatsApp Cloud API (JSON Payload)
    if "application/json" in content_type:
        try:
            data = await request.json()
            entry = data.get("entry", [])
            if entry:
                changes = entry[0].get("changes", [])
                if changes:
                    val = changes[0].get("value", {})
                    messages = val.get("messages", [])
                    if messages:
                        msg = messages[0]
                        from_number = msg.get("from", "")
                        body = msg.get("text", {}).get("body", "").strip()

                        if body and from_number:
                            log_activity("whatsapp", f"📱 Inbound Meta WhatsApp from {from_number}: '{body}'")
                            db.save_chat_message("user", body, session_id=f"whatsapp_{from_number}")

                            ai_reply = agent.chat(body)
                            reply_text = ai_reply.get("reply", "I've processed your request.")
                            tool_names = [t.get("tool", "tool") for t in ai_reply.get("all_tools_executed", [])]
                            db.save_chat_message("assistant", reply_text, tool_calls=tool_names, session_id=f"whatsapp_{from_number}")

                            # Reply back via Meta Graph API
                            agent.whatsapp.send_message(reply_text, to_number=from_number)

            return {"status": "EVENT_RECEIVED"}
        except Exception as e:
            print("Meta WhatsApp Webhook error:", e)
            return {"status": "error", "detail": str(e)}

    # 2. Twilio WhatsApp Sandbox (Form Data Payload)
    try:
        form_data = await request.form()
        from_number = form_data.get("From", "User")
        body = form_data.get("Body", "").strip()

        if body:
            log_activity("whatsapp", f"📱 Inbound Twilio WhatsApp from {from_number}: '{body}'")
            db.save_chat_message("user", body, session_id=f"whatsapp_{from_number}")

            ai_reply = agent.chat(body)
            reply_text = ai_reply.get("reply", "I've processed your request.")
            tool_names = [t.get("tool", "tool") for t in ai_reply.get("all_tools_executed", [])]
            db.save_chat_message("assistant", reply_text, tool_calls=tool_names, session_id=f"whatsapp_{from_number}")

            twiml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""
            return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        print("Twilio WhatsApp Webhook error:", e)

    return Response(content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>", media_type="application/xml")

@app.get("/api/notes")
def get_notes():
    return {"notes": agent.notes.list_notes(), "todos": agent.notes.list_todos()}

# Moltbook Endpoints
@app.get("/api/moltbook/feed")
def get_moltbook_feed(sort: str = "hot", limit: int = 10):
    try:
        posts = agent.moltbook.get_feed(sort=sort, limit=limit)
        return {"posts": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/moltbook/register")
def register_moltbook(req: MoltbookRegisterRequest):
    try:
        data = agent.moltbook.register_agent(req.name, req.description)
        log_activity("moltbook", f"Registered agent '{req.name}' on Moltbook!")
        return data
    except Exception as e:
        log_activity("error", f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/moltbook/post/publish")
def publish_moltbook(req: MoltbookPublishRequest):
    try:
        res = agent.moltbook.create_post(req.title, req.content, req.submolt)
        stats["moltbook_posts"] += 1
        log_activity("moltbook", f"Published post: '{req.title}'")
        return res
    except Exception as e:
        log_activity("error", f"Publish error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/moltbook/engage")
def engage_moltbook():
    try:
        logs = agent.moltbook_auto_engage(max_comments=2, auto_upvote=True)
        for l in logs:
            log_activity("moltbook", l)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activity")
def get_activity():
    return {"logs": activity_logs, "stats": stats}

@app.post("/api/scheduler/config")
def update_scheduler(req: SchedulerConfigRequest):
    scheduler_state["enabled"] = req.enabled
    scheduler_state["interval_minutes"] = max(5, req.interval_minutes)
    scheduler_state["status"] = "Running" if req.enabled else "Stopped"
    log_activity("scheduler", f"Scheduler {'Enabled' if req.enabled else 'Disabled'} ({scheduler_state['interval_minutes']}m interval)")
    return {"scheduler": scheduler_state}

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static/index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
