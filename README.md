# Bob — Autonomous Personal AI Agent

Bob is an all-purpose personal AI assistant equipped with a web dashboard, calendar scheduling, WhatsApp integration, live web search, and social agent capabilities on Moltbook.

Bob works with any AI provider: Groq, DeepSeek, OpenAI, OpenRouter, Google Gemini, Ollama (local offline), or any custom OpenAI-compatible API endpoint.

---

## What Bob Can Do

- **Personal Assistant & Chat**: Answers questions, writes and debugs code, drafts emails, and summarizes articles.
- **Calendar & Agenda Management**: Schedule meetings using natural language (for example, *"Bob, schedule a team sync tomorrow at 3 PM"*), view your upcoming schedule, and export to Google Calendar or Apple Calendar (`.ics` format).
- **WhatsApp Integration**: Dispatch WhatsApp notifications and automatically reply to incoming messages via webhooks.
- **Real-Time Web Search**: Search the web and retrieve live news and articles without requiring paid search API keys.
- **Moltbook Social Network**: Participate on the Moltbook platform (post updates, comment on discussions, and browse feeds).
- **Notes and Task Checklists**: Keep personal notes, track to-dos, and mark completed items.
- **Background Scheduler**: Run automated background checks for calendar events and social updates at set intervals (15 minutes, 30 minutes, 1 hour, or 2 hours).

---

## Quick Start Guide

### Step 1: Clone the Repository and Install Dependencies

```bash
git clone https://github.com/Mian255/personal-agent.git
cd personal-agent

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Step 2: Set Up Your Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and add your API key (for example, a free key from Groq, OpenRouter, or Google AI Studio).

### Step 3: Start the Web Dashboard

```bash
python server.py
```

Open your browser and navigate to:
**http://localhost:8000**

*(If you prefer working inside the terminal, you can also run `python main.py`).*

---

## Supported AI Providers & Models

You can use any model by editing your `.env` file:

### 1. Groq (Fastest & Free Tier Available)
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

### 2. Universal / Custom API Endpoint (Together AI, Mistral, LocalAI, vLLM)
```env
LLM_PROVIDER=custom
LLM_BASE_URL=https://api.yourprovider.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=your_model_name
```

### 3. OpenRouter (Access to 100+ Models)
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

### 4. Official OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
```

### 5. DeepSeek
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_MODEL=deepseek-chat
```

### 6. Google Gemini Free Tier
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash
```

### 7. Local Offline Ollama
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
```

---

## Free 24/7 Cloud Hosting on Render

You can host Bob online for free so it stays active even when your computer is off:

1. Push this project to your GitHub repository:
   ```bash
   git push -u origin main
   ```
2. Log in to [Render.com](https://render.com) and click **New + Web Service**.
3. Select your repository (`personal-agent`).
4. In the settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. In the **Environment Variables** section, add your `GROQ_API_KEY` (or other provider key).
6. Click **Deploy Web Service**. Render will assign a free public web address where Bob runs around the clock.

---

## Running with Docker

If you prefer containerized deployment:

```bash
# Build the Docker image
docker build -t bob-agent .

# Run the container
docker run -d -p 8000:8000 --env-file .env --name bob-agent bob-agent
```

---

## Project Structure

- `server.py` — Web dashboard server and API endpoints (FastAPI).
- `main.py` — Terminal interactive interface.
- `agent.py` — Core autonomous tool-calling AI agent.
- `llm.py` — Universal adapter supporting any model provider.
- `tools/` — Modular tools (Calendar, WhatsApp, Web Search, Notes, Moltbook).
- `static/` — Web dashboard interface files (HTML, CSS, JavaScript).
- `data/` — Local storage for calendar events, notes, and logs.

---

## License

This project is licensed under the MIT License. Created by [Mian255](https://github.com/Mian255).
