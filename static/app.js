// Init States
const WS_URL = `ws://${location.host}/ws/logs`;
const LEVELS = {
  DEBUG: { badge: 'badge-debug', msg: 'text-zinc-400',  row: '' },
  INFO:  { badge: 'badge-info',  msg: 'text-sky-300',   row: '' },
  WARN:  { badge: 'badge-warn',  msg: 'text-amber-300', row: 'row-warn' },
  ERROR: { badge: 'badge-error', msg: 'text-red-300',   row: 'row-error' },
};

let ws = null;
let paused = false;
let buffer = [];
let levelFilter = 'ALL';

// DOM
const $entries    = document.getElementById('log-entries');
const $container  = document.getElementById('log-container');
const $emptyState = document.getElementById('empty-state');
const $pauseBtn   = document.getElementById('pause-btn');
const $pauseLabel = document.getElementById('pause-label');
const $pauseIcon  = document.getElementById('pause-icon');
const $resumeIcon = document.getElementById('resume-icon');
const $wsDot      = document.getElementById('ws-dot');
const $wsStatus   = document.getElementById('ws-status');
const $wsBtn      = document.getElementById('ws-toggle-btn');
const $autoscroll = document.getElementById('autoscroll');
const $count      = document.getElementById('total-count');

// Websocket
function connect() {
  setStatus('connecting');
  ws = new WebSocket(WS_URL);
  ws.onopen    = () => setStatus('connected');
  ws.onclose   = () => { ws = null; setStatus('disconnected'); };
  ws.onerror   = () => { ws = null; setStatus('disconnected'); };
  ws.onmessage = (e) => {
    let raw;
    try { raw = JSON.parse(e.data); }
    catch { raw = { level: 'INFO', message: e.data }; }
    addLog({ ...raw, level: raw.level });
  };
}

function disconnect() {
  if (ws) { ws.close(); ws = null; }
  setStatus('disconnected');
}

function toggleConnection() {
  ws ? disconnect() : connect();
}

// Controls
function togglePause() {
  paused = !paused;
  $pauseLabel.textContent = paused ? 'Resume' : 'Pause';
  $pauseIcon.classList.toggle('hidden', paused);
  $resumeIcon.classList.toggle('hidden', !paused);
  $pauseBtn.classList.toggle('bg-zinc-800', !paused);
  $pauseBtn.classList.toggle('text-zinc-300', !paused);
  $pauseBtn.classList.toggle('bg-amber-900/40', paused);
  $pauseBtn.classList.toggle('text-amber-300', paused);
  $pauseBtn.classList.toggle('border-amber-800/60', paused);

  if (!paused) {
    buffer.splice(0).forEach(appendEntry);
    scrollToBottom();
  }
}

function clearLogs() {
  buffer = [];
  $entries.innerHTML = '';
  $count.textContent = '0';
  $emptyState.style.display = '';
}

function setFilter(level) {
  levelFilter = level;
  document.querySelectorAll('.level-filter').forEach(btn =>
    btn.classList.toggle('active', btn.dataset.level === level)
  );
  $entries.querySelectorAll('.log-entry').forEach(row =>
    row.classList.toggle('hidden', level !== 'ALL' && row.dataset.level !== level)
  );
}

// Logging
function addLog(raw) {
  const level = raw.level;
  const entry = {
    level,
    message: String(raw.message ?? ''),
    source:  raw.source || '',
    ts:      raw.timestamp ? new Date(raw.timestamp) : new Date(),
  };

  $emptyState.style.display = 'none';

  if (paused) {
    buffer.push(entry);
    $count.textContent = $entries.childElementCount + buffer.length;
    return;
  }
  appendEntry(entry);
}

function appendEntry(entry) {
  const cfg = LEVELS[entry.level];
  const ts  = entry.ts.toLocaleTimeString('en-US', { hour12: false })
              + '.' + String(entry.ts.getMilliseconds()).padStart(3, '0');

  const row = document.createElement('div');
  row.className = `log-entry ${cfg.row}`;
  row.dataset.level = entry.level;
  if (levelFilter !== 'ALL' && entry.level !== levelFilter) row.classList.add('hidden');
  row.innerHTML = `
    <span class="log-ts">${ts}</span>
    <span class="log-badge ${cfg.badge}">${entry.level.slice(0, 5)}</span>
    ${entry.source ? `<span class="log-source">${escHtml(entry.source)}</span>` : ''}
    <span class="log-msg ${cfg.msg}">${escHtml(entry.message)}</span>
  `;
  $entries.appendChild(row);
  $count.textContent = $entries.childElementCount;
  if ($autoscroll.checked) scrollToBottom();
}

function escHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// UI 
function setStatus(state) {
  const states = {
    connecting:   ['bg-yellow-400 animate-pulse', 'Connecting…',  'text-yellow-400',  'Disconnect'],
    connected:    ['bg-emerald-400 animate-pulse', 'Connected',    'text-emerald-400', 'Disconnect'],
    disconnected: ['bg-zinc-600',                  'Disconnected', 'text-zinc-500',    'Connect'],
  };
  const [dot, label, color, btn] = states[state];
  $wsDot.className      = `w-2 h-2 rounded-full flex-shrink-0 ${dot}`;
  $wsStatus.textContent = label;
  $wsStatus.className   = `text-xs font-medium tabular-nums hidden sm:block ${color}`;
  $wsBtn.textContent    = btn;
}

function scrollToBottom() {
  requestAnimationFrame(() => { $container.scrollTop = $container.scrollHeight; });
}

$container.addEventListener('scroll', () => {
  const nearBottom = $container.scrollHeight - $container.scrollTop - $container.clientHeight < 80;
  if (!nearBottom) $autoscroll.checked = false;
});
