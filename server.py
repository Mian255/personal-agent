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
from fastapi.responses import FileResponse
from pydantic import BaseModel

from llm import LLMClient
from agent import PersonalAgent

load_dotenv()

app = FastAPI(title="Personal AI Agent Hub")

agent_name = os.getenv("AGENT_NAME", "Bob")
user_name = os.getenv("USER_NAME", "Creator")
agent = PersonalAgent(name=agent_name, user_name=user_name)

activity_logs: List[Dict[str, Any]] = [
    {
        "id": 1,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "type": "system",
        "message": f"Personal Agent '{agent.name}' online with Groq 120B & Tool Suite (Calendar, WhatsApp, Moltbook, Web Search)."
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

# --- API Endpoints ---
@app.get("/api/status")
def get_status():
    return {
        "agent_name": agent.name,
        "user_name": agent.user_name,
        "provider": agent.llm.provider,
        "model": agent.llm.model,
        "moltbook_key_set": bool(agent.moltbook.api_key),
        "whatsapp_configured": bool(agent.whatsapp.account_sid and not agent.whatsapp.account_sid.startswith("your_")),
        "stats": stats,
        "scheduler": scheduler_state
    }

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    try:
        result = agent.chat(req.message)
        stats["chats_count"] += 1
        
        if result.get("tool_executed"):
            tool_name = result["tool_executed"]["tool"]
            log_activity(tool_name, f"Tool executed: {tool_name} -> {result['tool_executed'].get('action')}")
            if "calendar" in tool_name:
                stats["events_scheduled"] += 1
            elif "whatsapp" in tool_name:
                stats["whatsapp_sent"] += 1
            elif "moltbook" in tool_name:
                stats["moltbook_posts"] += 1
        else:
            log_activity("chat", f"User: {req.message[:50]}...")
            
        return result
    except Exception as e:
        log_activity("error", f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/clear")
def clear_chat():
    agent.clear_history()
    log_activity("system", "Conversation cleared.")
    return {"status": "cleared"}

# Calendar Endpoints
@app.get("/api/calendar")
def list_calendar():
    return {"events": agent.calendar.list_events()}

@app.post("/api/calendar")
def add_calendar_event(req: CalendarEventRequest):
    event = agent.calendar.add_event(
        title=req.title,
        start_time_str=req.start_time,
        end_time_str=req.end_time,
        description=req.description or "",
        location=req.location or ""
    )
    stats["events_scheduled"] += 1
    log_activity("calendar", f"Scheduled event: '{event['title']}' for {event['start']}")
    return event

@app.delete("/api/calendar/{event_id}")
def delete_calendar_event(event_id: str):
    success = agent.calendar.delete_event(event_id)
    if success:
        log_activity("calendar", f"Deleted calendar event ID {event_id}")
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Event not found")

@app.get("/api/calendar/export.ics")
def export_calendar_ics():
    ics_path = agent.calendar.export_ics()
    return FileResponse(ics_path, media_type="text/calendar", filename="agent_calendar.ics")

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

@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """Handles incoming WhatsApp messages from Twilio or webhook."""
    form_data = await request.form()
    from_number = form_data.get("From", "User")
    body = form_data.get("Body", "")
    
    if body:
        log_activity("whatsapp", f"Incoming WhatsApp from {from_number}: {body}")
        ai_reply = agent.chat(body)
        agent.whatsapp.send_message(ai_reply["reply"], to_number=from_number)
        return {"status": "replied", "reply": ai_reply["reply"]}
    return {"status": "ignored"}

# Notes & Todos Endpoints
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

app.mount("/static", StaticFiles(directory="/Users/pl/projects/personal-agent/static"), name="static")

@app.get("/")
def index():
    return FileResponse("/Users/pl/projects/personal-agent/static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
