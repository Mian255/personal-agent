"""
Personal AI Agent Core Engine with Native Tool Execution
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from llm import LLMClient
from tools.moltbook import MoltbookClient
from tools.calendar_tool import CalendarManager
from tools.whatsapp_tool import WhatsAppClient
from tools.web_search_tool import WebSearchTool
from tools.notes_tool import NotesManager

AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "schedule_calendar_event",
            "description": "Schedule a new meeting, event, or task on the user's calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title or subject of the event."},
                    "start_time": {"type": "string", "description": "Start date and time (e.g., '2026-09-28 15:00', 'tomorrow 3pm')."},
                    "end_time": {"type": "string", "description": "Optional end time (defaults to 1 hour after start)."},
                    "description": {"type": "string", "description": "Optional description or meeting notes."}
                },
                "required": ["title", "start_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_calendar_events",
            "description": "View scheduled calendar events and upcoming agenda.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {"type": "integer", "description": "Number of days ahead to look (default 30)."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp_message",
            "description": "Send a WhatsApp message or alert to a phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The message body to send via WhatsApp."},
                    "to_number": {"type": "string", "description": "Recipient phone number with country code (e.g., '+1234567890')."}
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the live internet for up-to-date information, news, or technical documentation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query terms."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_note",
            "description": "Save a note or memo for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the note."},
                    "content": {"type": "string", "description": "Full content of the note."}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_todos",
            "description": "Add a new todo task or list current todos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add", "list"], "description": "Action to perform."},
                    "task": {"type": "string", "description": "Task description when adding."},
                    "due_date": {"type": "string", "description": "Optional deadline."}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "publish_moltbook_post",
            "description": "Publish a post to the Moltbook AI social network.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Post title."},
                    "content": {"type": "string", "description": "Post content."}
                },
                "required": ["title", "content"]
            }
        }
    }
]


class PersonalAgent:
    def __init__(
        self,
        name: Optional[str] = None,
        user_name: Optional[str] = None,
        system_persona: Optional[str] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.name = name or os.getenv("AGENT_NAME", "AI Assistant")
        self.user_name = user_name or os.getenv("USER_NAME", "User")
        self.llm = llm_client or LLMClient()
        
        # Tools
        self.moltbook = MoltbookClient()
        self.calendar = CalendarManager()
        self.whatsapp = WhatsAppClient()
        self.web_search = WebSearchTool()
        self.notes = NotesManager()
        
        self.history: List[Dict[str, Any]] = []
        
        self.system_prompt = system_persona or (
            f"You are {self.name}, an intelligent, proactive, all-purpose personal AI agent for {self.user_name}.\n"
            f"Current local time: {datetime.now().strftime('%A, %Y-%m-%d %H:%M')}.\n"
            f"You can execute tasks like scheduling calendar events, dispatching WhatsApp messages, searching the web, saving notes/todos, and interacting on Moltbook."
        )

    def _execute_single_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name == "schedule_calendar_event":
            return self.calendar.add_event(
                title=args.get("title", "Event"),
                start_time_str=args.get("start_time", "tomorrow 10am"),
                end_time_str=args.get("end_time"),
                description=args.get("description", "")
            )
        elif tool_name == "list_calendar_events":
            return self.calendar.list_events(upcoming_days=args.get("days_ahead", 30))
        elif tool_name == "send_whatsapp_message":
            return self.whatsapp.send_message(
                message=args.get("message", ""),
                to_number=args.get("to_number")
            )
        elif tool_name == "search_web":
            return self.web_search.search(query=args.get("query", ""))
        elif tool_name == "add_note":
            return self.notes.add_note(title=args.get("title", "Note"), content=args.get("content", ""))
        elif tool_name == "manage_todos":
            if args.get("action") == "add":
                return self.notes.add_todo(task=args.get("task", ""), due_date=args.get("due_date", ""))
            return self.notes.list_todos()
        elif tool_name == "publish_moltbook_post":
            return self.moltbook.create_post(title=args.get("title", ""), content=args.get("content", ""))
        return {"error": f"Unknown tool {tool_name}"}

    def chat(self, user_message: str) -> Dict[str, Any]:
        """
        Processes message with LLM function calling loop.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-10:],
            {"role": "user", "content": user_message}
        ]

        executed_tools = []
        
        try:
            # 1. First model call with tools available
            msg = self.llm.chat_completion(messages, tools=AGENT_TOOLS_SCHEMA)
            
            # Check if model invoked tool calls
            if msg.tool_calls:
                # Add assistant's tool-call intent to conversation
                messages.append(msg)
                
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except Exception:
                        fn_args = {}
                    
                    tool_output = self._execute_single_tool(fn_name, fn_args)
                    executed_tools.append({
                        "tool": fn_name,
                        "args": fn_args,
                        "result": tool_output
                    })
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": json.dumps(tool_output)
                    })

                # 2. Second model call to summarize and reply to user
                final_msg = self.llm.chat_completion(messages, tools=None)
                final_reply = final_msg.content or "Task completed."
            else:
                final_reply = msg.content or "Understood."

        except Exception as e:
            # Fallback direct completion
            fallback_msg = self.llm.chat_completion(
                [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_message}],
                tools=None
            )
            final_reply = fallback_msg.content or str(e)

        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": final_reply})

        return {
            "reply": final_reply,
            "tool_executed": executed_tools[0] if executed_tools else None,
            "all_tools_executed": executed_tools
        }

    def clear_history(self):
        self.history = []

    # Moltbook helpers
    def moltbook_generate_post(self, topic: Optional[str] = None) -> Dict[str, str]:
        prompt = f"Draft a creative Moltbook post for AI agents. Topic: {topic or 'general AI frontiers'}.\nFormat as:\nTITLE: <title>\nCONTENT: <content>"
        msg = self.llm.chat_completion([{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}], tools=None, temperature=0.8)
        raw = msg.content or ""
        title = "Agent Thought Stream"
        content = raw
        if "TITLE:" in raw and "CONTENT:" in raw:
            parts = raw.split("CONTENT:", 1)
            title = parts[0].replace("TITLE:", "").strip()
            content = parts[1].strip()
        return {"title": title, "content": content}

    def moltbook_generate_comment(self, post_title: str, post_content: str) -> str:
        prompt = f"Post: {post_title}\nContent: {post_content}\nWrite a thoughtful 1-paragraph reply."
        msg = self.llm.chat_completion([{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}], tools=None, temperature=0.7)
        return msg.content or ""

    def moltbook_auto_engage(self, max_comments: int = 2, auto_upvote: bool = True) -> List[str]:
        logs = []
        try:
            feed = self.moltbook.get_feed(sort="hot", limit=10)
            logs.append(f"Fetched {len(feed)} posts from Moltbook.")
        except Exception as e:
            return [f"Could not reach Moltbook API: {e}"]

        comments_posted = 0
        for post in feed:
            post_id = post.get("id") or post.get("_id")
            title = post.get("title", "Untitled")
            content = post.get("content", "")
            if not post_id:
                continue

            if auto_upvote:
                try:
                    self.moltbook.upvote_post(post_id)
                    logs.append(f"👍 Upvoted: '{title[:35]}...'")
                except Exception as e:
                    logs.append(f"Upvote skipped ({post_id}): {e}")

            if comments_posted < max_comments:
                try:
                    comment = self.moltbook_generate_comment(title, content)
                    self.moltbook.comment_on_post(post_id, comment)
                    logs.append(f"💬 Commented on '{title[:35]}...': {comment[:50]}...")
                    comments_posted += 1
                except Exception as e:
                    logs.append(f"Comment skipped ({post_id}): {e}")

        return logs
