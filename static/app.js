// Configure Marked for Rich Typography & Markdown Formatting
if (window.marked) {
  marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: false,
    mangle: false
  });
}

/**
 * Personal AI Agent Web Dashboard
 * Glassmorphic UI Controller with Custom Modals, Toast Alerts & Calendar Filters
 */

let currentTab = 'chat';
let currentAgentName = '';
let currentCalendarFilter = 7;
let cachedCalendarEvents = [];

function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

  const pane = document.getElementById(`pane-${tabId}`);
  const nav = document.getElementById(`nav-${tabId}`);
  if (pane) pane.classList.add('active');
  if (nav) nav.classList.add('active');

  if (tabId === 'calendar') { loadCalendar(); setDefaultEventStartTime(); }
  
  if (tabId === 'moltbook') loadMoltbookFeed();
  
  
  refreshIcons();
}

function refreshIcons() {
  if (window.lucide) {
    lucide.createIcons();
  }
}

// ----------------------------------------------------
// Custom Toast & Modal System
// ----------------------------------------------------
function showToast(message, type = 'info', title = '') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast-card toast-${type}`;

  let iconName = 'info';
  let defaultTitle = 'Notification';
  if (type === 'success') { iconName = 'check-circle'; defaultTitle = 'Success'; }
  else if (type === 'error') { iconName = 'alert-circle'; defaultTitle = 'Error'; }
  else if (type === 'warning') { iconName = 'alert-triangle'; defaultTitle = 'Notice'; }

  toast.innerHTML = `
    <div class="toast-icon"><i data-lucide="${iconName}"></i></div>
    <div class="toast-content">
      <div class="toast-title">${title || defaultTitle}</div>
      <div class="toast-msg">${message}</div>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()"><i data-lucide="x" style="width:14px;height:14px;"></i></button>
  `;
  container.appendChild(toast);
  refreshIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

function showModal({
  title = 'Confirmation',
  message = '',
  icon = 'info',
  iconType = 'primary',
  confirmText = 'Confirm',
  confirmClass = 'btn-primary',
  cancelText = 'Cancel',
  onConfirm = null,
  showCancel = true
}) {
  const backdrop = document.getElementById('custom-modal-backdrop');
  const titleEl = document.getElementById('modal-title');
  const msgEl = document.getElementById('modal-message');
  const iconWrapEl = document.getElementById('modal-icon-wrapper');
  const iconEl = document.getElementById('modal-icon');
  const confirmBtn = document.getElementById('modal-confirm-btn');
  const cancelBtn = document.getElementById('modal-cancel-btn');

  if (!backdrop) return;

  titleEl.innerText = title;
  msgEl.innerText = message;
  iconWrapEl.className = `modal-icon-wrapper ${iconType}`;
  iconEl.setAttribute('data-lucide', icon);

  confirmBtn.innerText = confirmText;
  confirmBtn.className = `btn ${confirmClass}`;

  cancelBtn.style.display = showCancel ? 'inline-flex' : 'none';
  if (cancelText) cancelBtn.innerText = cancelText;

  confirmBtn.onclick = () => {
    closeModal();
    if (onConfirm) onConfirm();
  };

  backdrop.style.display = 'flex';
  refreshIcons();
}

function closeModal() {
  const backdrop = document.getElementById('custom-modal-backdrop');
  if (backdrop) backdrop.style.display = 'none';
}

// ----------------------------------------------------
// Status Poller & Init
// ----------------------------------------------------
async function loadStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();

    currentAgentName = data.agent_name || 'AI Assistant';
    document.title = currentAgentName + " - Personal AI Assistant";

    // Update Brand & Display Names dynamically
    const nameEl = document.getElementById('agent-display-name');
    if (nameEl) nameEl.innerText = `${currentAgentName} Agent`;

    const welcomeEl = document.getElementById('welcome-msg-text');
    if (welcomeEl && welcomeEl.dataset.initialized !== 'true') {
      welcomeEl.innerText = `Hello! I'm ${currentAgentName}, your personal autonomous AI assistant. How can I help you today?`;
      welcomeEl.dataset.initialized = 'true';
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
    const disconnectBtn = document.getElementById('btn-disconnect-gcal');

    if (data.google_calendar_connected) {
      if (gcalStatus) { gcalStatus.innerText = 'Connected'; gcalStatus.className = 'stat-value text-success'; }
      if (gcalTitle) gcalTitle.innerText = 'Google Calendar (Live Sync Active)';
      if (gcalDesc) gcalDesc.innerText = 'Connected to your primary Google Calendar. All agenda changes sync in real time.';
      if (gcalBtn) {
        gcalBtn.innerHTML = '<i data-lucide="check-circle"></i> Synced';
        gcalBtn.className = 'btn btn-secondary';
        gcalBtn.onclick = () => showToast("Google Calendar is connected and synchronizing live.", "info", "Calendar Active");
      }
      if (disconnectBtn) disconnectBtn.style.display = 'inline-flex';
    } else {
      if (gcalStatus) { gcalStatus.innerText = 'Ready to Connect'; gcalStatus.className = 'stat-value'; }
      if (gcalTitle) gcalTitle.innerText = 'Google Calendar Sync';
      if (gcalDesc) gcalDesc.innerText = 'Connect your Google account for live two-way synchronization.';
      if (gcalBtn) {
        gcalBtn.innerHTML = '<i data-lucide="link"></i> Connect Google Account';
        gcalBtn.className = 'btn btn-primary';
        gcalBtn.onclick = connectGoogleCalendar;
      }
      if (disconnectBtn) disconnectBtn.style.display = 'none';
    }

    // Model Stat
    const modelStat = document.getElementById('quick-model-name');
    if (modelStat) modelStat.innerText = data.model || data.provider;

    // Scheduler
    const schedStatus = document.getElementById('quick-scheduler-status');
    const schedSwitch = document.getElementById('scheduler-switch');
    const lastRun = document.getElementById('scheduler-last-run');

    if (data.scheduler) {
      const isRunning = data.scheduler.status === 'Running';
      if (schedStatus) {
        schedStatus.innerText = isRunning ? 'Active' : 'Stopped';
        schedStatus.className = isRunning ? 'stat-value text-success' : 'stat-value';
      }
      if (schedSwitch) schedSwitch.checked = data.scheduler.enabled;
      if (lastRun) lastRun.innerText = data.scheduler.last_run || 'Never';
    }
  } catch (err) {
    console.error("Status load failed:", err);
  }
  refreshIcons();
}

// Check OAuth callback parameters from URL
function checkAuthUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const authState = params.get('google_auth');
  if (authState === 'success') {
    showToast("🎉 Google Calendar connected successfully! Your events will now sync live.", "success", "Google Calendar");
    window.history.replaceState({}, document.title, window.location.pathname);
    switchTab('calendar');
  } else if (authState === 'failed' || authState === 'error') {
    const reason = params.get('reason') || 'Authorization was cancelled or failed';
    showToast(`Could not connect Google Calendar: ${reason}`, "error", "OAuth Error");
    window.history.replaceState({}, document.title, window.location.pathname);
  } else if (authState === 'missing_credentials') {
    showToast("Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env first.", "warning", "Credentials Required");
    window.history.replaceState({}, document.title, window.location.pathname);
  }
}

// ----------------------------------------------------
// Chat & Messaging
// ----------------------------------------------------
async function loadChatHistory() {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  try {
    const res = await fetch('/api/chat/history');
    const data = await res.json();
    const messages = data.messages || [];

    if (messages.length > 0) {
      container.innerHTML = '';
      messages.forEach(m => {
        appendMessage(m.role, m.content, m.tool_calls || []);
      });
    }
  } catch (err) {
    console.error("Failed to load chat history:", err);
  }
}

// ----------------------------------------------------
// WhatsApp-Style Hold-to-Speak & Live Audio Visualizer
// ----------------------------------------------------
let speechRecognition = null;
let isRecordingVoice = false;
let voiceStartTime = 0;
let voiceTimerInterval = null;
let audioContext = null;
let analyserNode = null;
let micMediaStream = null;
let animFrameId = null;
let capturedVoiceTranscript = '';

function setupVoiceEvents() {
  const micBtn = document.getElementById('btn-voice-input');
  if (!micBtn || micBtn.dataset.bound === 'true') return;

  micBtn.dataset.bound = 'true';

  // Desktop Mouse Events
  micBtn.addEventListener('mousedown', (e) => {
    e.preventDefault();
    startHoldToSpeak();
  });

  window.addEventListener('mouseup', (e) => {
    if (isRecordingVoice) {
      stopAndSendVoice();
    }
  });

  // Mobile Touch Events
  micBtn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    startHoldToSpeak();
  }, { passive: false });

  micBtn.addEventListener('touchend', (e) => {
    e.preventDefault();
    if (isRecordingVoice) {
      stopAndSendVoice();
    }
  });
}

function initSpeechEngine() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    let text = '';
    for (let i = 0; i < event.results.length; ++i) {
      text += event.results[i][0].transcript;
    }
    capturedVoiceTranscript = text.trim();
  };

  recognition.onerror = (event) => {
    console.warn("Speech recognition error:", event.error);
  };

  return recognition;
}

async function startHoldToSpeak() {
  if (isRecordingVoice) return;

  if (!speechRecognition) {
    speechRecognition = initSpeechEngine();
  }

  if (!speechRecognition && !navigator.mediaDevices?.getUserMedia) {
    showModal({
      title: "Voice Recognition Not Supported",
      message: "Your browser does not support live speech recognition. Please use Google Chrome, Safari, or Edge.",
      icon: "mic-off",
      iconType: "danger",
      confirmText: "Understood",
      showCancel: false
    });
    return;
  }

  isRecordingVoice = true;
  voiceStartTime = Date.now();
  capturedVoiceTranscript = '';

  // UI Updates: Activate Mic Button & Show Wave Overlay
  const micBtn = document.getElementById('btn-voice-input');
  const overlay = document.getElementById('voice-recording-overlay');
  const timerEl = document.getElementById('voice-recording-timer');

  if (micBtn) micBtn.classList.add('recording');
  if (overlay) overlay.style.display = 'flex';
  if (timerEl) timerEl.innerText = '0:00';

  // Start Timer
  clearInterval(voiceTimerInterval);
  voiceTimerInterval = setInterval(() => {
    const elapsedSec = Math.floor((Date.now() - voiceStartTime) / 1000);
    const mins = Math.floor(elapsedSec / 60);
    const secs = elapsedSec % 60;
    if (timerEl) timerEl.innerText = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  }, 500);

  // Start Audio Visualizer (Live Wave Animation Moving With Voice)
  startAudioVisualizer();

  // Start Speech Recognition
  if (speechRecognition) {
    try {
      speechRecognition.start();
    } catch (e) {
      console.warn("Speech start:", e);
    }
  }

  refreshIcons();
}

async function startAudioVisualizer() {
  try {
    micMediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    audioContext = new AudioContextClass();
    analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = 64;

    const source = audioContext.createMediaStreamSource(micMediaStream);
    source.connect(analyserNode);

    const bars = document.querySelectorAll('#audio-wave-bars .wave-bar');
    const dataArray = new Uint8Array(analyserNode.frequencyBinCount);

    function renderWaves() {
      if (!isRecordingVoice) return;
      analyserNode.getByteFrequencyData(dataArray);

      bars.forEach((bar, i) => {
        const val = dataArray[i % dataArray.length] || 0;
        // Calculate dynamic height between 4px and 26px based on real volume
        const height = Math.max(4, Math.min(26, (val / 255) * 32));
        bar.style.height = `${height}px`;
      });

      animFrameId = requestAnimationFrame(renderWaves);
    }

    renderWaves();
  } catch (err) {
    // Fallback CSS Wave Simulation if mic stream unavailable
    simulateWaveAnimation();
  }
}

function simulateWaveAnimation() {
  const bars = document.querySelectorAll('#audio-wave-bars .wave-bar');
  let step = 0;
  function sim() {
    if (!isRecordingVoice) return;
    step += 0.2;
    bars.forEach((bar, i) => {
      const h = 5 + Math.abs(Math.sin(step + i * 0.4)) * 18;
      bar.style.height = `${h}px`;
    });
    animFrameId = requestAnimationFrame(sim);
  }
  sim();
}

function stopAndSendVoice() {
  if (!isRecordingVoice) return;
  const duration = Date.now() - voiceStartTime;
  isRecordingVoice = false;

  // Cleanup Visualizer & Streams
  if (animFrameId) cancelAnimationFrame(animFrameId);
  if (voiceTimerInterval) clearInterval(voiceTimerInterval);
  if (micMediaStream) {
    micMediaStream.getTracks().forEach(t => t.stop());
    micMediaStream = null;
  }
  if (audioContext && audioContext.state !== 'closed') {
    audioContext.close();
    audioContext = null;
  }

  // Reset UI
  const micBtn = document.getElementById('btn-voice-input');
  const overlay = document.getElementById('voice-recording-overlay');
  const bars = document.querySelectorAll('#audio-wave-bars .wave-bar');

  if (micBtn) micBtn.classList.remove('recording');
  if (overlay) overlay.style.display = 'none';
  bars.forEach(b => b.style.height = '6px');

  // Stop Speech Engine
  if (speechRecognition) {
    try {
      speechRecognition.stop();
    } catch (e) {}
  }

  // If held for less than 400ms, ignore (accidental tap)
  if (duration < 400) {
    showToast("Hold to speak, release to send.", "info", "Hold to Talk");
    return;
  }

  // Wait a brief tick to capture final transcript and dispatch
  setTimeout(() => {
    const input = document.getElementById('chat-input');
    const textToSend = capturedVoiceTranscript || (input ? input.value.trim() : '');

    if (textToSend) {
      if (input) input.value = textToSend;
      sendMessage();
    } else {
      showToast("No speech detected. Please hold and speak clearly.", "warning", "Voice Message");
    }
  }, 250);

  refreshIcons();
}

function handleChatKey(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message) return;

  appendMessage('user', message);
  input.value = '';

  const typingId = appendTypingIndicator();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const data = await res.json();
    removeMessage(typingId);

    if (res.ok) {
      appendMessage('assistant', data.reply, data.tool_calls);
      if (data.tool_calls && data.tool_calls.some(t => t.includes('calendar') || t.includes('event'))) {
        loadCalendar();
      }
    } else {
      appendMessage('assistant', `⚠️ Error: ${data.detail || 'Failed to get response'}`);
    }
  } catch (err) {
    removeMessage(typingId);
    appendMessage('assistant', `⚠️ Network Error: ${err.message}`);
  }
}

function appendMessage(role, text, toolCalls = []) {
  const container = document.getElementById('chat-messages');
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}`;

  const avatar = role === 'user'
    ? '<div class="avatar user"><i data-lucide="user"></i></div>'
    : '<div class="avatar"><i data-lucide="bot"></i></div>';

  let toolChipsHtml = '';
  if (toolCalls && toolCalls.length > 0) {
    toolChipsHtml = `
      <div class="tool-chips">
        ${toolCalls.map(t => `<span class="tool-chip"><i data-lucide="wrench"></i> ${escapeHtml(t)}</span>`).join('')}
      </div>
    `;
  }

  const parsedText = window.marked ? marked.parse(text) : `<p>${escapeHtml(text)}</p>`;

  msgDiv.innerHTML = `
    ${avatar}
    <div class="bubble">
      ${parsedText}
      ${toolChipsHtml}
    </div>
  `;
  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
  refreshIcons();
}

function appendTypingIndicator() {
  const container = document.getElementById('chat-messages');
  const id = `typing-${Date.now()}`;
  const msgDiv = document.createElement('div');
  msgDiv.id = id;
  msgDiv.className = 'message assistant';
  msgDiv.innerHTML = `
    <div class="avatar"><i data-lucide="bot"></i></div>
    <div class="bubble">
      <div class="typing-indicator"><span></span><span></span><span></span></div>
    </div>
  `;
  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
  refreshIcons();
  return id;
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function clearChat() {
  showModal({
    title: 'Clear Conversation',
    message: `Are you sure you want to clear the conversation history with ${currentAgentName}?`,
    icon: 'trash-2',
    iconType: 'danger',
    confirmText: 'Clear Chat',
    confirmClass: 'btn-danger',
    onConfirm: async () => {
      try {
        await fetch('/api/chat/clear', { method: 'POST' });
        const container = document.getElementById('chat-messages');
        container.innerHTML = `
          <div class="message assistant">
            <div class="avatar"><i data-lucide="bot"></i></div>
            <div class="bubble">
              <p>Chat cleared. What would you like to do next?</p>
            </div>
          </div>
        `;
        refreshIcons();
        showToast("Chat history cleared from database.", "info");
      } catch (err) {
        showToast(`Failed to clear chat: ${err.message}`, 'error');
      }
    }
  });
}

// ----------------------------------------------------
// Google Calendar & Agenda
// ----------------------------------------------------
function setDefaultEventStartTime() {
  const startInput = document.getElementById('event-start');
  if (startInput) {
    const now = new Date();
    now.setHours(now.getHours() + 1);
    now.setMinutes(0);
    now.setSeconds(0);
    const tzOffset = now.getTimezoneOffset() * 60000;
    const localISOTime = (new Date(now.getTime() - tzOffset)).toISOString().slice(0, 16);
    startInput.value = localISOTime;
    const minTime = (new Date(Date.now() - tzOffset)).toISOString().slice(0, 16);
    startInput.min = minTime;
  }
}

function connectGoogleCalendar() {
  window.location.href = '/api/calendar/google/login';
}

function confirmDisconnectGoogleCalendar() {
  showModal({
    title: 'Sign Out of Google Calendar',
    message: 'Are you sure you want to disconnect your Google Calendar? Live automatic event syncing will be paused until you sign back in.',
    icon: 'log-out',
    iconType: 'danger',
    confirmText: 'Sign Out',
    confirmClass: 'btn-danger',
    onConfirm: async () => {
      try {
        const res = await fetch('/api/calendar/google/disconnect', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'disconnected') {
          showToast('Signed out of Google Calendar successfully.', 'success', 'Disconnected');
          loadStatus();
  setupVoiceEvents();
  loadChatHistory();
          loadCalendar();
  setDefaultEventStartTime();
        } else {
          showToast('Failed to disconnect Google Calendar.', 'error');
        }
      } catch (err) {
        showToast(`Network error: ${err.message}`, 'error');
      }
    }
  });
}

function setCalendarFilter(filterVal, buttonEl) {
  currentCalendarFilter = filterVal;
  document.querySelectorAll('#calendar-filters .filter-pill').forEach(btn => btn.classList.remove('active'));
  if (buttonEl) buttonEl.classList.add('active');
  renderCalendarList();
}

async function loadCalendar() {
  const list = document.getElementById('agenda-list');
  try {
    const res = await fetch('/api/calendar');
    const data = await res.json();
    cachedCalendarEvents = data.events || [];
    renderCalendarList();
  } catch (err) {
    list.innerHTML = `<div class="p-3 text-danger">Failed to load calendar events: ${err}</div>`;
  }
}

function renderCalendarList() {
  const list = document.getElementById('agenda-list');
  const countBadge = document.getElementById('agenda-count');
  

  let filtered = cachedCalendarEvents;

  if (currentCalendarFilter !== 'all') {
    const maxDays = parseInt(currentCalendarFilter, 10);
    const now = new Date();
    // Start from beginning of today
    now.setHours(0, 0, 0, 0);

    const maxDate = new Date(now);
    maxDate.setDate(maxDate.getDate() + maxDays);
    maxDate.setHours(23, 59, 59, 999);

    filtered = cachedCalendarEvents.filter(e => {
      if (!e.start) return true;
      const eventDate = new Date(e.start.replace(' ', 'T'));
      if (isNaN(eventDate.getTime())) return true;
      return eventDate >= now && eventDate <= maxDate;
    });
  }

  if (countBadge) countBadge.innerText = `${filtered.length} Events`;
  

  if (filtered.length > 0) {
    list.innerHTML = filtered.map(e => {
      const isLiveGoogle = e.source === "google_calendar_live";
      const gcalBtn = e.google_calendar_link ? `
        <a href="${e.google_calendar_link}" target="_blank" rel="noopener" class="btn btn-secondary" style="padding:4px 9px;font-size:0.75rem;margin-left:auto;text-decoration:none;" title="Open in Google Calendar">
          <i data-lucide="external-link" style="width:13px;height:13px;"></i> Google Calendar
        </a>
      ` : '';

      const sourceBadge = isLiveGoogle ? `
        <span style="font-size:0.7rem;padding:2px 7px;border-radius:4px;background:rgba(66,133,244,0.2);color:#60a5fa;margin-left:0.35rem;font-weight:600;">Google Synced</span>
      ` : '';

      return `
        <div class="feed-item">
          <div class="feed-header" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.25rem;">
            <div style="display:flex;align-items:center;gap:0.35rem;">
              <strong>${escapeHtml(e.title || 'Untitled Event')}</strong>
              ${sourceBadge}
            </div>
            <span class="feed-time" style="font-size:0.75rem;color:var(--text-muted);">${e.start || 'Time TBD'}</span>
          </div>
          ${e.description ? `<p style="font-size:0.82rem;color:var(--text-secondary);margin:0.35rem 0;">${escapeHtml(e.description)}</p>` : ''}
          <div style="display:flex;align-items:center;gap:0.5rem;margin-top:0.5rem;">
            ${gcalBtn}
            <button class="btn btn-danger-outline" style="padding:4px 8px;font-size:0.75rem;" onclick="confirmDeleteEvent('${e.id}')" title="Delete event">
              <i data-lucide="trash-2" style="width:13px;height:13px;"></i>
            </button>
          </div>
        </div>
      `;
    }).join('');
  } else {
    const filterLabel = currentCalendarFilter === 'all' ? 'scheduled yet' : `found within the next ${currentCalendarFilter} days`;
    list.innerHTML = `
      <div style="padding: 2.5rem 1rem; text-align: center; color: var(--text-muted);">
        <i data-lucide="calendar-x" style="width:38px;height:38px;opacity:0.4;margin:0 auto 0.75rem auto;display:block;"></i>
        <p style="font-size:0.88rem;">No events ${filterLabel}.</p>
      </div>
    `;
  }
  refreshIcons();
}

async function createCalendarEvent() {
  const title = document.getElementById('event-title').value.trim();
  const start_time = document.getElementById('event-start').value.trim();
  const description = document.getElementById('event-desc').value.trim();

  if (!title || !start_time) {
    showToast("Please provide both an event title and start time.", "warning", "Missing Fields");
    return;
  }

  try {
    const res = await fetch('/api/calendar/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, start_time, description })
    });
    const data = await res.json();

    document.getElementById('event-title').value = '';
    setDefaultEventStartTime();
    document.getElementById('event-desc').value = '';
    
    showToast(`Event "${title}" added to your calendar!`, 'success', 'Event Created');
    loadCalendar();
  setDefaultEventStartTime();

    if (data.google_calendar_link && data.source !== "google_calendar_live") {
      showModal({
        title: 'Open in Google Calendar',
        message: `Would you like to open "${title}" directly in your Google Calendar web app?`,
        icon: 'external-link',
        iconType: 'primary',
        confirmText: 'Open Google Calendar',
        cancelText: 'Done',
        onConfirm: () => {
          window.open(data.google_calendar_link, '_blank');
        }
      });
    }
  } catch (err) {
    showToast(`Failed to create event: ${err.message}`, 'error');
  }
}

function confirmDeleteEvent(id) {
  showModal({
    title: 'Delete Calendar Event',
    message: 'Are you sure you want to delete this event from your calendar?',
    icon: 'trash-2',
    iconType: 'danger',
    confirmText: 'Delete Event',
    confirmClass: 'btn-danger',
    onConfirm: async () => {
      try {
        await fetch(`/api/calendar/${id}`, { method: 'DELETE' });
        showToast('Event deleted successfully.', 'info');
        loadCalendar();
  setDefaultEventStartTime();
      } catch (err) {
        showToast(`Failed to delete event: ${err.message}`, 'error');
      }
    }
  });
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
          <div class="feed-item-header" style="display:flex;justify-content:space-between;margin-bottom:0.25rem;">
            <span class="feed-author"><i data-lucide="phone" style="width:12px;height:12px;display:inline;"></i> To: ${escapeHtml(m.to)}</span>
            <span class="feed-time" style="font-size:0.75rem;color:var(--text-muted);">${escapeHtml(m.timestamp)}</span>
          </div>
          <div class="feed-content" style="font-size:0.85rem;color:var(--text-primary);">${escapeHtml(m.message)}</div>
          <div style="font-size:0.7rem;color:var(--accent-emerald);margin-top:0.35rem;font-weight:600;">Status: ${escapeHtml(m.status)}</div>
        </div>
      `).join('');
    } else {
      list.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-muted);">No dispatched WhatsApp messages yet.</div>';
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
    showToast("Please enter a message body.", "warning", "Empty Message");
    return;
  }

  try {
    const res = await fetch('/api/whatsapp/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to_number, message })
    });
    const data = await res.json();
    showToast(`WhatsApp message dispatched! Status: ${data.status}`, 'success', 'WhatsApp Dispatched');
    document.getElementById('wa-message').value = '';
    loadWhatsAppMessages();
  } catch (err) {
    showToast(`Failed to send WhatsApp message: ${err.message}`, 'error');
  }
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
        <div class="feed-title ${t.completed ? 'text-muted' : ''}" style="font-weight:500;">${escapeHtml(t.task)}</div>
        <div class="feed-time" style="font-size:0.75rem;color:var(--text-muted);margin-top:0.2rem;">Added: ${t.created_at}</div>
      </div>
    `).join('') : '<div style="padding:1.5rem;text-align:center;color:var(--text-muted);">No todos yet. Ask in chat to "add to my todo list"!</div>';

    noteContainer.innerHTML = notes.length > 0 ? notes.map(n => `
      <div class="feed-item">
        <div class="feed-title" style="font-weight:600;margin-bottom:0.25rem;">${escapeHtml(n.title)}</div>
        <div class="feed-content" style="font-size:0.83rem;color:var(--text-secondary);">${escapeHtml(n.content)}</div>
      </div>
    `).join('') : '<div style="padding:1.5rem;text-align:center;color:var(--text-muted);">No notes yet. Ask in chat to "save note"!</div>';

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
      showToast("Registration initiated! Claim your agent link above.", "success");
    }
  } catch (err) {
    resBox.classList.remove('hidden');
    resBox.innerText = `Error: ${err}`;
    showToast(`Registration failed: ${err}`, 'error');
  }
  refreshIcons();
}

async function generatePostDraft() {
  const topic = document.getElementById('post-topic').value.trim();
  showToast("Drafting creative post with AI...", "info");
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: `Draft a creative Moltbook post title and content about: ${topic || 'autonomous AI agents'}` })
  });
  const data = await res.json();
  document.getElementById('post-content').value = data.reply;
  showToast("Post draft ready for review!", "success");
}

async function publishPost() {
  const title = document.getElementById('post-title').value.trim();
  const content = document.getElementById('post-content').value.trim();
  if (!title || !content) {
    showToast("Title and content are required.", "warning");
    return;
  }
  await fetch('/api/moltbook/post/publish', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content })
  });
  showToast("Post published live to Moltbook network!", "success");
  loadMoltbookFeed();
}

async function triggerEngagement() {
  showToast("Running Moltbook AI engagement cycle...", "info");
  await fetch('/api/moltbook/engage', { method: 'POST' });
  showToast("Engagement cycle completed successfully!", "success");
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
          <div class="feed-title" style="font-weight:600;">${escapeHtml(p.title || 'Untitled')}</div>
          <div class="feed-content" style="font-size:0.84rem;color:var(--text-secondary);margin-top:0.25rem;">${escapeHtml(p.content || '')}</div>
        </div>
      `).join('');
    } else {
      feedContainer.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-muted);">No posts available or not registered.</div>';
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
  showToast(`Scheduler ${toggle.checked ? 'activated' : 'paused'}.`, toggle.checked ? 'success' : 'info');
  loadStatus();
  setupVoiceEvents();
  loadChatHistory();
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
  setupVoiceEvents();
  loadChatHistory();
  checkAuthUrlParams();
  loadCalendar();
  setDefaultEventStartTime();
  setInterval(loadStatus, 15000);
});
