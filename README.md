# Bob — Personal AI Agent

Bob is a simple, all-purpose personal AI assistant with a local web dashboard and WhatsApp support. It helps you manage your schedule, search the web, take notes, and interact with other AI agents on Moltbook.

Bob works with any model or API key: Groq, DeepSeek, OpenAI, OpenRouter, Google Gemini, or local Ollama.

---

## What It Can Do

- **Chat & Assistant**: Answer questions, write and review code, draft emails, and brainstorm ideas.
- **Calendar & Reminders**: Schedule meetings in plain English (e.g., *"Schedule team sync tomorrow at 3 PM"*), view your agenda, and export standard `.ics` files for Google Calendar and Apple Calendar.
- **WhatsApp Messaging**: Send notifications and auto-reply to incoming WhatsApp messages using webhooks.
- **Web Search**: Search the live web for news, documentation, and research articles without needing paid search keys.
- **Moltbook Social Network**: Connect with other AI agents on Moltbook to read posts, publish updates, and comment.
- **Notes & To-Do Lists**: Save quick notes, create task checklists, and track deadlines.
- **Background Scheduler**: Run automated background checks for calendar events and social updates at set intervals.

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/Mian255/personal-agent.git
cd personal-agent

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Add Your API Key

Copy the example settings file:

```bash
cp .env.example .env
```

Open `.env` and paste your API key (for example, a free key from [Groq](https://console.groq.com) or [OpenRouter](https://openrouter.ai)).

### 3. Start the Web Dashboard

```bash
python server.py
```

Then open **http://localhost:8000** in your browser.

*(If you prefer the command line, you can also run `python main.py`).*

---

## Setting Up Your Model

You can use any provider by editing your `.env` file:

### Groq
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

### Any Custom or Self-Hosted API
```env
LLM_PROVIDER=custom
LLM_BASE_URL=https://api.yourprovider.com/v1
LLM_API_KEY=your_key_here
LLM_MODEL=your_model_name
```

### OpenRouter
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
```

### DeepSeek
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_MODEL=deepseek-chat
```

### Google Gemini
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.0-flash
```

### Local Ollama (Offline)
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
```

---

## Free 24/7 Cloud Hosting (Render.com)

To keep Bob running continuously online for free:

1. Push your code to GitHub:
   ```bash
   git push -u origin main
   ```
2. Go to [Render.com](https://render.com) and click **New + Web Service**.
3. Select your repository (`personal-agent`).
4. Set the build command to `pip install -r requirements.txt` and start command to `uvicorn server:app --host 0.0.0.0 --port $PORT`.
5. Add your `GROQ_API_KEY` under Environment Variables.
6. Click **Deploy**. Render will give you a free live URL.

---

## Project Structure

- `server.py` — Web dashboard server (FastAPI).
- `main.py` — Terminal interactive interface.
- `agent.py` — Core AI agent and tool runner.
- `llm.py` — Multi-provider model client.
- `tools/` — Modular tools (Calendar, WhatsApp, Search, Notes, Moltbook).
- `static/` — Web dashboard files (HTML, CSS, JavaScript).
- `data/` — Storage for calendar events, notes, and history.

---

## License

MIT License — Created by [Mian255](https://github.com/Mian255).
