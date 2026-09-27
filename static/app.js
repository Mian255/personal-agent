function refreshIcons() {
  if (window.lucide) window.lucide.createIcons();
}

let currentAgentName = "AI Assistant";

function switchTab(tabId) {
  document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
  
  const targetPane = document.getElementById(`pane-${tabId}`);
  const targetNav = document.getElementById(`nav-${tabId}`);
  if (targetPane) targetPane.classList.add('active');
  if (targetNav) targetNav.classList.add('active');

  if (tabId === 'calendar') loadCalendar();
  else if (tabId === 'whatsapp') loadWhatsAppMessages();
  else if (tabId === 'moltbook') loadMoltbookFeed();
  else if (tabId === 'notes') loadNotes();
  else if (tabId === 'activity') loadActivityLogs();
  
  refreshIcons();
}

// Status Poller & Dynamic Loader
async function loadStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    
    currentAgentName = data.agent_name || 'AI Assistant';
    
    const displayNameElem = document.getElementById('agent-display-name');
    if (displayNameElem) displayNameElem.innerText = currentAgentName;
    
    document.title = `${currentAgentName} — Personal AI Agent`;
    
    const welcomeBubble = document.getElementById('welcome-msg-text');
    if (welcomeBubble) {
      welcomeBubble.innerHTML = `Hello! I am <strong>${escapeHtml(currentAgentName)}</strong>, your personal AI assistant. How can I help you today?`;
    }

    const regNameInput = document.getElementById('reg-agent-name');
    if (regNameInput && !regNameInput.dataset.touched) {
      regNameInput.value = currentAgentName;
    }

    // Google Calendar Status
    const gcalStatus = document.getElementById('quick-gcal-status');
    const gcalTitle = document.getElementById('gcal-banner-title');
    const gcalDesc = document.getElementById('gcal-banner-desc');
    const gcalBtn = document.getElementById('btn-connect-gcal');

    if (data.google_calendar_connected) {
      if (gcalStatus) { gcalStatus.innerText = 'Connected'; gcalStatus.className = 'stat-value text-success'; }
      if (gcalTitle) gcalTitle.innerText = 'Google Calendar (Live Sync Active)';
      if (gcalDesc) gcalDesc.innerText = 'Connected to your primary Google Calendar. Events created sync directly.';
      if (gcalBtn) { gcalBtn.innerHTML = '<i data-lucide="check-circle"></i> Connected'; gcalBtn.className = 'btn btn-secondary'; }
    } else {
      if (gcalStatus) { gcalStatus.innerText = '1-Click / OAuth'; gcalStatus.className = 'stat-value'; }
      if (gcalTitle) gcalTitle.innerText = 'Google Calendar Integration';
      if (gcalDesc) gcalDesc.innerText = 'Events sync to your calendar with 1-click links or direct Google OAuth.';
    }

    const modelBadge = document.getElementById('quick-model-name');
    if (modelBadge) modelBadge.innerText = (data.model || '').split('/').pop() || 'LLM';

    const schedStat = document.getElementById('quick-scheduler-status');
    const schedToggle = document.getElementById('scheduler-switch');
    const schedStatusText = document.getElementById('scheduler-toggle-status');
    const schedInterval = document.getElementById('scheduler-interval-display');
    const lastRun = document.getElementById('scheduler-last-run');

    if (data.scheduler) {
      if (schedStat) schedStat.innerText = data.scheduler.enabled ? 'Running' : 'Stopped';
      if (schedToggle) schedToggle.checked = data.scheduler.enabled;
      if (schedStatusText) schedStatusText.innerText = `Status: ${data.scheduler.status}`;
      if (schedInterval) schedInterval.innerText = `Interval: ${data.scheduler.interval_minutes}m`;
      if (lastRun) lastRun.innerText = data.scheduler.last_run || 'Never';
    }
  } catch (err) {
    console.error("Status load failed:", err);
  }
}

// ----------------------------------------------------
// Chat & Tool Calling UI
// ----------------------------------------------------
function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;

  const msgContainer = document.getElementById('chat-messages');

  const userDiv = document.createElement('div');
  userDiv.className = 'message user';
  userDiv.innerHTML = `
    <div class="avatar"><i data-lucide="user"></i></div>
    <div class="bubble"><p>${escapeHtml(text)}</p></div>
  `;
  msgContainer.appendChild(userDiv);
  input.value = '';
  msgContainer.scrollTop = msgContainer.scrollHeight;
  refreshIcons();

  const typingDiv = document.createElement('div');
  typingDiv.className = 'message assistant';
  typingDiv.id = 'typing-indicator';
  typingDiv.innerHTML = `
    <div class="avatar"><i data-lucide="bot"></i></div>
    <div class="bubble"><p><i data-lucide="loader-2" class="spin"></i> Thinking...</p></div>
  `;
  msgContainer.appendChild(typingDiv);
  msgContainer.scrollTop = msgContainer.scrollHeight;
  refreshIcons();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    typingDiv.remove();

    if (res.ok) {
      const botDiv = document.createElement('div');
      botDiv.className = 'message assistant';
      
      let toolChip = '';
      if (data.tool_executed) {
        toolChip = `
          <div style="margin-bottom: 0.5rem; display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.72rem; padding: 2px 8px; border-radius: 9999px; background: rgba(99, 102, 241, 0.2); color: #818cf8; font-weight: 600;">
            <i data-lucide="cpu" style="width:12px;height:12px;"></i> Action: ${data.tool_executed.tool}
          </div>
        `;
      }

      const rendered = window.marked ? window.marked.parse(data.reply) : data.reply;
      botDiv.innerHTML = `
        <div class="avatar"><i data-lucide="bot"></i></div>
        <div class="bubble">
          ${toolChip}
          <div>${rendered}</div>
        </div>
      `;
      msgContainer.appendChild(botDiv);
    } else {
      const errDiv = document.createElement('div');
      errDiv.className = 'message assistant';
      errDiv.innerHTML = `
        <div class="avatar"><i data-lucide="alert-triangle"></i></div>
        <div class="bubble"><p style="color:#ef4444;">Error: ${data.detail || 'Could not process request'}</p></div>
      `;
      msgContainer.appendChild(errDiv);
    }
  } catch (err) {
    typingDiv.remove();
    console.error(err);
  }
  msgContainer.scrollTop = msgContainer.scrollHeight;
  refreshIcons();
  loadCalendar();
}

async function clearChat() {
  await fetch('/api/chat/clear', { method: 'POST' });
  const msgContainer = document.getElementById('chat-messages');
  msgContainer.innerHTML = `
    <div class="message assistant">
      <div class="avatar"><i data-lucide="bot"></i></div>
      <div class="bubble"><p id="welcome-msg-text">Hello! I am <strong>${escapeHtml(currentAgentName)}</strong>, your personal AI assistant. How can I help you today?</p></div>
    </div>
  `;
  refreshIcons();
}

// ----------------------------------------------------
// Google Calendar
// ----------------------------------------------------
async function connectGoogleCalendar() {
  try {
    const res = await fetch('/api/calendar/google/auth');
    const data = await res.json();
    if (data.auth_url) {
      window.open(data.auth_url, '_blank');
    } else {
      alert("To enable direct OAuth Google Calendar API:\n\n1. Go to Google Cloud Console (console.cloud.google.com)\n2. Create an OAuth Client ID\n3. Download credentials JSON and place in 'data/google_credentials.json'\n\n(Note: 1-click Google Calendar creation links work right now without any setup!)");
    }
  } catch (err) {
    alert(`Could not initiate Google Auth: ${err}`);
  }
}

async function loadCalendar() {
  const list = document.getElementById('agenda-list');
  const countBadge = document.getElementById('agenda-count');
  const sidebarBadge = document.getElementById('badge-calendar-count');

  try {
    const res = await fetch('/api/calendar');
    const data = await res.json();
    const events = data.events || [];

    if (countBadge) countBadge.innerText = `${events.length} Events`;
    if (sidebarBadge) sidebarBadge.innerText = events.length;

    if (events.length > 0) {
      list.innerHTML = events.map(e => {
        const gcalBtn = e.google_calendar_link ? `
          <a href="${e.google_calendar_link}" target="_blank" rel="noopener" class="btn btn-secondary" style="padding:3px 8px;font-size:0.72rem;margin-left:auto;text-decoration:none;" title="Open in Google Calendar">
            <i data-lucide="external-link" style="width:12px;height:12px;"></i> Google Calendar
          </a>
        ` : '';

        return `
          <div class="feed-item">
            <div class="feed-item-header">
              <span class="feed-author" style="color:#10b981;"><i data-lucide="clock" style="width:12px;height:12px;display:inline;"></i> ${e.start}</span>
              ${gcalBtn}
              <button onclick="deleteEvent('${e.id}')" style="background:none;border:none;color:#ef4444;cursor:pointer;margin-left:0.5rem;" title="Delete">
                <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
              </button>
            </div>
            <div class="feed-title">${escapeHtml(e.title)}</div>
            <div class="feed-content">${escapeHtml(e.description || 'No description.')}</div>
          </div>
        `;
      }).join('');
    } else {
      list.innerHTML = '<div class="p-3 text-muted">No scheduled events. Say "Schedule meeting tomorrow at 3pm" in chat!</div>';
    }
  } catch (err) {
    list.innerHTML = `<div class="p-3 text-danger">Error loading calendar: ${err}</div>`;
  }
  refreshIcons();
}

async function createCalendarEvent() {
  const title = document.getElementById('event-title').value.trim();
  const start_time = document.getElementById('event-start').value.trim();
  const description = document.getElementById('event-desc').value.trim();

  if (!title || !start_time) {
    alert("Please enter title and start time.");
    return;
  }

  const res = await fetch('/api/calendar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, start_time, description })
  });
  const data = await res.json();

  document.getElementById('event-title').value = '';
  document.getElementById('event-start').value = '';
  document.getElementById('event-desc').value = '';
  loadCalendar();

  if (data.google_calendar_link && data.source !== "google_calendar_live") {
    if (confirm("Event added! Would you like to open it in your Google Calendar right now?")) {
      window.open(data.google_calendar_link, '_blank');
    }
  }
}

async function deleteEvent(id) {
  if (confirm("Delete this calendar event?")) {
    await fetch(`/api/calendar/${id}`, { method: 'DELETE' });
    loadCalendar();
  }
}

// ----------------------------------------------------
// WhatsApp
// ----------------------------------------------------
async function loadWhatsAppMessages() {
  const list = document.getElementById('wa-history-list');
  try {
    const res = await fetch('/api/whatsapp/messages');
    const data = await res.json();
    const msgs = data.messages || [];

    if (msgs.length > 0) {
      list.innerHTML = msgs.slice().reverse().map(m => `
        <div class="feed-item">
          <div class="feed-item-header">
            <span class="feed-author"><i data-lucide="phone" style="width:12px;height:12px;display:inline;"></i> To: ${escapeHtml(m.to)}</span>
            <span class="feed-time">${escapeHtml(m.timestamp)}</span>
          </div>
          <div class="feed-content">${escapeHtml(m.message)}</div>
          <div style="font-size:0.7rem;color:#94a3b8;margin-top:0.25rem;">Status: ${escapeHtml(m.status)}</div>
        </div>
      `).join('');
    } else {
      list.innerHTML = '<div class="p-3 text-muted">No dispatched WhatsApp messages yet.</div>';
    }
  } catch (err) {
    list.innerHTML = `<div class="p-3 text-danger">Error: ${err}</div>`;
  }
  refreshIcons();
}

async function sendWhatsAppDirect() {
  const to_number = document.getElementById('wa-recipient').value.trim();
  const message = document.getElementById('wa-message').value.trim();

  if (!message) {
    alert("Please enter a message body.");
    return;
  }

  const res = await fetch('/api/whatsapp/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ to_number, message })
  });
  const data = await res.json();
  alert(`Message dispatched! Status: ${data.status}`);
  document.getElementById('wa-message').value = '';
  loadWhatsAppMessages();
}

// ----------------------------------------------------
// Notes & Todos
// ----------------------------------------------------
async function loadNotes() {
  const todoContainer = document.getElementById('todos-list');
  const noteContainer = document.getElementById('notes-list');

  try {
    const res = await fetch('/api/notes');
    const data = await res.json();
    
    const todos = data.todos || [];
    const notes = data.notes || [];

    todoContainer.innerHTML = todos.length > 0 ? todos.map(t => `
      <div class="feed-item">
        <div class="feed-title ${t.completed ? 'text-muted' : ''}">${escapeHtml(t.task)}</div>
        <div class="feed-time">Added: ${t.created_at}</div>
      </div>
    `).join('') : '<div class="p-3 text-muted">No todos yet. Ask in chat to "add to my todo list"!</div>';

    noteContainer.innerHTML = notes.length > 0 ? notes.map(n => `
      <div class="feed-item">
        <div class="feed-title">${escapeHtml(n.title)}</div>
        <div class="feed-content">${escapeHtml(n.content)}</div>
      </div>
    `).join('') : '<div class="p-3 text-muted">No notes yet. Ask in chat to "save note"!</div>';

  } catch (err) {
    console.error(err);
  }
  refreshIcons();
}

// ----------------------------------------------------
// Moltbook & Scheduler & Logs
// ----------------------------------------------------
async function registerAgent() {
  const name = document.getElementById('reg-agent-name').value.trim();
  const desc = document.getElementById('reg-agent-desc').value.trim();
  const resBox = document.getElementById('reg-result');

  try {
    const res = await fetch('/api/moltbook/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description: desc })
    });
    const data = await res.json();
    resBox.classList.remove('hidden');

    if (res.ok) {
      resBox.className = 'alert-box success';
      resBox.innerHTML = `
        <div>
          <strong>Registration Successful!</strong><br>
          <a href="${data.claim_url}" target="_blank" style="color: #10b981; font-weight: bold; text-decoration: underline;">
            👉 Click here to verify on X/Twitter & Claim Agent
          </a>
        </div>
      `;
    }
  } catch (err) {
    resBox.classList.remove('hidden');
    resBox.innerText = `Error: ${err}`;
  }
  refreshIcons();
}

async function generatePostDraft() {
  const topic = document.getElementById('post-topic').value.trim();
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: `Draft a creative Moltbook post title and content about: ${topic || 'autonomous AI agents'}` })
  });
  const data = await res.json();
  document.getElementById('post-content').value = data.reply;
}

async function publishPost() {
  const title = document.getElementById('post-title').value.trim();
  const content = document.getElementById('post-content').value.trim();
  if (!title || !content) {
    alert("Title and content are required.");
    return;
  }
  await fetch('/api/moltbook/post/publish', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content })
  });
  alert("Post published live!");
  loadMoltbookFeed();
}

async function triggerEngagement() {
  await fetch('/api/moltbook/engage', { method: 'POST' });
  alert("Engagement cycle completed!");
  loadMoltbookFeed();
}

async function loadMoltbookFeed() {
  const feedContainer = document.getElementById('feed-list');
  try {
    const res = await fetch('/api/moltbook/feed?sort=hot&limit=8');
    const data = await res.json();
    const posts = data.posts || [];
    if (posts.length > 0) {
      feedContainer.innerHTML = posts.map(p => `
        <div class="feed-item">
          <div class="feed-title">${escapeHtml(p.title || 'Untitled')}</div>
          <div class="feed-content">${escapeHtml(p.content || '')}</div>
        </div>
      `).join('');
    } else {
      feedContainer.innerHTML = '<div class="p-3 text-muted">No posts available or not registered.</div>';
    }
  } catch (err) {
    feedContainer.innerHTML = `<div class="p-3 text-muted">Could not fetch Moltbook feed: ${err}</div>`;
  }
  refreshIcons();
}

async function toggleScheduler() {
  const toggle = document.getElementById('scheduler-switch');
  const intervalSelect = document.getElementById('scheduler-interval');
  await fetch('/api/scheduler/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      enabled: toggle.checked,
      interval_minutes: parseInt(intervalSelect.value, 10)
    })
  });
  loadStatus();
}

async function updateSchedulerInterval() {
  toggleScheduler();
}

async function loadActivityLogs() {
  const timeline = document.getElementById('activity-timeline');
  try {
    const res = await fetch('/api/activity');
    const data = await res.json();
    if (data.logs) {
      timeline.innerHTML = data.logs.map(log => `
        <div class="activity-item">
          <span class="activity-time">${log.timestamp}</span>
          <span class="activity-badge badge-${log.type}">${log.type}</span>
          <span>${escapeHtml(log.message)}</span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error(err);
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
  refreshIcons();
  loadStatus();
  loadCalendar();
  setInterval(loadStatus, 15000);
});
