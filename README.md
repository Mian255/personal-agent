<div align="center">

# ⚡ Bob — All-Purpose Personal AI Agent

**An autonomous, multi-tool personal AI agent & web dashboard.**  
*Compatible with ANY LLM provider (OpenAI, DeepSeek, Groq, OpenRouter, Gemini, Ollama, or custom OpenAI-compatible endpoints).*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LLM Compatible](https://img.shields.io/badge/LLM-Any%20Provider-purple.svg)](#-universal-llm-configuration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-key-features) • [Quick Start](#-quick-start) • [Model Setup](#-universal-llm-configuration) • [Free 24/7 Hosting](#-free-247-cloud-hosting) • [Docker](#-docker-deployment)

</div>

---

## 🌟 Key Features

- 🧠 **Universal Model Support**: Plug in **ANY** API key or model (Groq, OpenRouter, DeepSeek, OpenAI, Google Gemini, Ollama, or any custom endpoint).
- 📅 **Calendar & Task Scheduling**: Add events via natural chat (*"Bob, schedule design review tomorrow at 3pm"*), view upcoming agendas, and export standard `.ics` calendar files for Google Calendar, Apple Calendar, and Outlook.
- 📱 **WhatsApp Hub**: Send WhatsApp alerts, dispatch scheduled notifications, and receive inbound messages via webhooks.
- 🔍 **Real-Time Web Search**: Free DuckDuckGo search integration to fetch breaking news, documentation, and live data.
- 🌐 **Moltbook AI Social Network**: Native integration with [Moltbook](https://www.moltbook.com) — register your agent identity, browse global discussions, publish posts, and run autonomous engagement cycles.
- 📝 **Notes & Todo Manager**: Maintain memos, research notes, and persistent task checklists.
- ⏰ **24/7 Background Scheduler**: Configurable background heartbeat to monitor calendar deadlines and social activity.
- 💻 **Modern Web Dashboard & CLI**: Clean dark-mode glassmorphic dashboard + terminal CLI.

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/Mian255/personal-agent.git
cd personal-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your chosen API key (see [Model Configuration](#-universal-llm-configuration) below).

### 3. Launch Bob
```bash
# Launch the Web Dashboard
python server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

*(Alternatively, run `python main.py` for the interactive Terminal CLI).*

---

## 🔌 Universal LLM Configuration

Bob is provider-agnostic. Configure your preferred model in `.env`:

### Option 1: Universal / Custom OpenAI-Compatible Endpoint
Works with **Together AI, Mistral, Fireworks, LocalAI, vLLM, LM Studio**:
```env
LLM_PROVIDER=custom
LLM_BASE_URL=https://api.yourprovider.com/v1
LLM_API_KEY=your_api_key_here
LLM_MODEL=your_model_name
```

### Option 2: Groq (Ultra-Fast Free Tier)
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_key
GROQ_MODEL=openai/gpt-oss-120b
```

### Option 3: OpenRouter (100+ Free & Paid Models)
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

### Option 4: Official OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your_openai_key
OPENAI_MODEL=gpt-4o-mini
```

### Option 5: DeepSeek API
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your_deepseek_key
DEEPSEEK_MODEL=deepseek-chat
```

### Option 6: Google Gemini Free API
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
```

### Option 7: 100% Offline Local Ollama
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
```

---

## 📁 Project Architecture

```
personal-agent/
├── server.py              # FastAPI Web Dashboard & API backend
├── main.py                # Terminal CLI Hub
├── agent.py               # Core autonomous agent & tool orchestrator
├── llm.py                 # Universal LLM client wrapper
├── requirements.txt       # Python dependencies
├── render.yaml            # 1-Click Render.com deployment config
├── Dockerfile             # Docker container definition
├── static/                # Modern Glassmorphic Web UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/                  # Local persistent data (Calendar, Notes, History)
│   ├── calendar.json
│   └── notes.json
└── tools/                 # Modular pluggable capabilities
    ├── calendar_tool.py   # Event management & .ICS export
    ├── whatsapp_tool.py   # Twilio / Webhook WhatsApp messaging
    ├── web_search_tool.py # DuckDuckGo live web search
    ├── notes_tool.py      # Notes & todo checklist manager
    └── moltbook.py        # Moltbook AI social network API client
```

---

## ☁️ Free 24/7 Cloud Hosting

### Deploying to Render.com (100% Free):
1. Push this repository to your GitHub account (`Mian255/personal-agent`).
2. Go to [render.com](https://render.com) and select **New + Web Service**.
3. Select your repository `personal-agent`.
4. Render will automatically detect `render.yaml` (Python 3, build command: `pip install -r requirements.txt`, start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`).
5. Add your `GROQ_API_KEY` (or other chosen provider keys) under Environment Variables.
6. Click **Deploy**. Your agent is live on a free public HTTPS URL 24/7!

---

## 🐳 Docker Deployment

```bash
# Build Docker image
docker build -t bob-agent .

# Run container
docker run -d -p 8000:8000 --env-file .env --name bob-agent bob-agent
```

---

## 🤝 Contributing

Contributions, feature requests, and new tools are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
