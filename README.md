# ⚡ Bob — All-Purpose Personal AI Agent

An autonomous, multi-tool Personal AI Agent engine and Web Dashboard designed to handle your daily personal, scheduling, messaging, and online agent tasks.

---

## 🌟 Core Capabilities

| Capability | What Bob Does |
| :--- | :--- |
| **🧠 Groq 120B Reasoning Engine** | Ultra-fast multi-turn intelligence, coding assistance, research, and planning. |
| **📅 Google / Apple Calendar** | Schedule meetings via natural chat ("*Bob, schedule sync tomorrow at 3pm*"), view agenda, and export standard `.ics` calendar files. |
| **📱 WhatsApp Hub** | Dispatch WhatsApp notifications and handle incoming webhook messages (Twilio Sandbox / WhatsApp Cloud API). |
| **🔍 Live Web Search** | Real-time DuckDuckGo web search & webpage scraping without paid API keys. |
| **🌐 Moltbook AI Social Net** | Automated presence, post generation, feed reading, upvoting, and commenting on [moltbook.com](https://www.moltbook.com). |
| **📝 Notes & Todos** | Maintain personal memos, research notes, and interactive task checklists. |
| **⏰ Background Scheduler** | Configurable background heartbeats (15m, 30m, 1h, 2h) for proactive alerts. |

---

## 🚀 Local Quick Start

```bash
cd /Users/pl/projects/personal-agent
source .venv/bin/activate
python server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## ☁️ 100% Free 24/7 Cloud Hosting

### Option 1: Render.com (Recommended)
1. Push this repo to your GitHub (`Mian255/personal-agent`).
2. Go to [render.com](https://render.com) and click **New + Web Service**.
3. Connect your repository `Mian255/personal-agent`.
4. Render will automatically detect `render.yaml` or you can select:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variable:
   - `GROQ_API_KEY`: `your_groq_api_key`
6. Click **Deploy**. Bob will run 24/7 on the cloud with a public HTTPS URL!

---

## 🐙 Push to GitHub (`Mian255`)

```bash
cd /Users/pl/projects/personal-agent
git push -u origin main
```
