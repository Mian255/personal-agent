<div align="center">

# ⚡ Bob — Autonomous Personal AI Agent

**An all-purpose, multi-tool AI assistant with Web Dashboard & WhatsApp integration.**  
*Plug in ANY model: Groq, DeepSeek, OpenAI, OpenRouter, Google Gemini, Ollama, or custom endpoints.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/Groq-Ultra--Fast-F55036?style=for-the-badge)](https://console.groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

[✨ Features](#-features) • [⚡ Quickstart](#-quickstart) • [🔌 Any Model Setup](#-connect-any-llm-model) • [☁️ 24/7 Free Hosting](#-free-247-cloud-hosting) • [🐳 Docker](#-docker)

</div>

---

## 🏗️ Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │             User Interfaces            │
                      │   Web Dashboard  •  WhatsApp  •  CLI   │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │          🤖 Bob Core Agent Engine      │
                      │     Autonomous Function Calling Loop   │
                      └───────────────────┬────────────────────┘
                                          │
         ┌─────────────────┬──────────────┴───────────────┬─────────────────┐
         ▼                 ▼                              ▼                 ▼
   📅 Calendar       📱 WhatsApp                    🔍 Web Search     🌐 Moltbook
 (Google/Apple)    (Twilio/Webhooks)                 (DuckDuckGo)    (AI Social Net)
         │                 │                              │                 │
         └─────────────────┴──────────────┬───────────────┴─────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │       Universal LLM Provider Layer     │
                      │ Groq • DeepSeek • OpenAI • Ollama • Any │
                      └────────────────────────────────────────┘
```

---

## ✨ Features

| Category | Capability | How to Use |
| :--- | :--- | :--- |
| **🧠 Intelligence** | Multi-turn reasoning, problem-solving, coding & writing | *"Help me write a Python automation script"* |
| **📅 Scheduling** | Calendar scheduling with **Google / Apple Calendar (.ICS)** export | *"Bob, schedule sync with Alex tomorrow at 3pm"* |
| **📱 WhatsApp** | Send outbound notifications & auto-reply to inbound messages | *"Send a WhatsApp to +123456 saying I'm running late"* |
| **🔍 Search** | Real-time web search without paid API keys | *"Search the web for latest breakthroughs in robotics"* |
| **🌐 Moltbook** | Autonomous presence on the **[Moltbook](https://www.moltbook.com)** AI social network | *"Publish a post about AI agent societies to Moltbook"* |
| **📝 Notes** | Persistent memos, research notes, and todo task checklists | *"Save a note about project roadmap"* |
| **⏰ Background** | Heartbeat scheduler for automated calendar reminders & social checks | Toggle 15m / 30m / 1h / 2h intervals in UI |

---

## ⚡ Quickstart

### 1. Clone & Set Up
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
```bash
cp .env.example .env
```
Add your free API key (e.g. from [Groq](https://console.groq.com) or [OpenRouter](https://openrouter.ai)).

### 3. Start Bob
```bash
# Launch the Web Dashboard
python server.py
```
👉 Open **[http://localhost:8000](http://localhost:8000)** in your browser!

*(Prefer terminal? Run `python main.py` for the interactive CLI).*

---

## 🔌 Connect Any LLM Model

Bob supports **any** provider via standard OpenAI-compatible endpoints or built-in presets:

<details open>
<summary><b>⚡ Option A: Groq (Recommended for Speed & Free Tier)</b></summary>

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_key
GROQ_MODEL=openai/gpt-oss-120b
```
</details>

<details>
<summary><b>🌐 Option B: Any Custom / Self-Hosted Endpoint (vLLM, Ollama, Together, Mistral)</b></summary>

```env
LLM_PROVIDER=custom
LLM_BASE_URL=https://api.yourprovider.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=your_model_name
```
</details>

<details>
<summary><b>🔀 Option C: OpenRouter (100+ Free & Paid Models)</b></summary>

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your_key
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```
</details>

<details>
<summary><b>🟢 Option D: DeepSeek Official API</b></summary>

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your_deepseek_key
DEEPSEEK_MODEL=deepseek-chat
```
</details>

<details>
<summary><b>💎 Option E: Google Gemini API</b></summary>

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy_your_gemini_key
GEMINI_MODEL=gemini-2.0-flash
```
</details>

<details>
<summary><b>🔒 Option F: 100% Offline Local Ollama</b></summary>

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
```
</details>

---

## ☁️ Free 24/7 Cloud Hosting

Deploy Bob to **[Render.com](https://render.com)** in 3 minutes:

1. Push this repository to your GitHub: `git push -u origin main`
2. In **Render.com**, click **New + Web Service** and select `personal-agent`.
3. Render automatically loads [`render.yaml`](render.yaml).
4. Add your `GROQ_API_KEY` under **Environment Variables**.
5. Click **Deploy**. Your agent is live on a free HTTPS URL 24/7!

---

## 🐳 Docker

```bash
# Build image
docker build -t bob-agent .

# Run container
docker run -d -p 8000:8000 --env-file .env --name bob-agent bob-agent
```

---

## 📂 Project Structure

```
personal-agent/
├── server.py              # FastAPI server & Web Dashboard API
├── main.py                # Terminal CLI Hub
├── agent.py               # Autonomous tool-calling agent engine
├── llm.py                 # Universal LLM provider adapter
├── static/                # Modern Glassmorphic Dark-Mode UI
├── data/                  # Persistent storage (Calendar, Notes, History)
└── tools/                 # Pluggable modular capabilities
    ├── calendar_tool.py   # Calendar manager & .ICS generator
    ├── whatsapp_tool.py   # WhatsApp dispatch & webhook receiver
    ├── web_search_tool.py # Real-time DuckDuckGo web search
    ├── notes_tool.py      # Notes & todo checklist manager
    └── moltbook.py        # Moltbook AI social network API client
```

---

## 📄 License

Distributed under the **MIT License**. Created by [Mian255](https://github.com/Mian255).
