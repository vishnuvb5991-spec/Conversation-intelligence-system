import './style.css';

const app = document.querySelector('#app');
let meetings = [];
let selected = null;
let busy = false;
let errorMessage = '';

const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
const timestamp = seconds => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
const duration = seconds => `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;

function render() {
  app.innerHTML = `
    <aside class="sidebar">
      <a class="brand" href="#" aria-label="Converse home"><span class="brand-mark">C</span><span>converse</span></a>
      <div class="workspace-label">WORKSPACE</div>
      <button class="side-link active" id="new-meeting"><span class="nav-icon">＋</span> New meeting</button>
      <div class="workspace-label recent-label">RECENT MEETINGS <span>${meetings.length}</span></div>
      <div class="meeting-list">${meetings.length ? meetings.map(item => `<button class="meeting-link ${selected?.id === item.id ? 'current' : ''}" data-meeting="${escapeHtml(item.id)}"><span class="meeting-dot"></span><span><b>${escapeHtml(item.title)}</b><small>${new Date(item.created_at).toLocaleDateString()} · ${duration(item.duration_seconds)}</small></span></button>`).join('') : '<p class="empty-sidebar">Your processed meetings will appear here.</p>'}</div>
      <div class="sidebar-bottom"><div class="plan-label"><span class="live-dot"></span> Batch workspace</div><small>Audio is processed in memory. Source files are not retained.</small></div>
    </aside>
    <main>
      <header><div><div class="eyebrow">CONVERSATION INTELLIGENCE</div><h1>${selected ? escapeHtml(selected.title) : 'Meeting workspace'}</h1></div><div class="header-badge"><span class="live-dot"></span> SOURCE AUDIO NOT STORED</div></header>
      ${selected ? meetingView(selected) : uploadView()}
    </main>`;
  bind();
}

function uploadView() {
  return `<section class="welcome"><div class="intro"><div class="eyebrow">FROM AUDIO TO ACTION</div><h2>Make every conversation<br><em>easy to act on.</em></h2><p>Upload a meeting recording to get a speaker-labeled transcript, concise summary, decisions, and clear next steps.</p></div>
    <form id="upload-form" class="upload-card">
      <div class="upload-top"><span class="upload-icon">↥</span><div><h3>Process a meeting</h3><p>WAV, MP3, M4A, MP4, WebM, FLAC or OGG · up to 50 MB</p></div></div>
      <label class="drop-zone" for="audio-file"><span class="wave-icon">◖))</span><strong>Choose an audio file</strong><span>or drop it here</span><input id="audio-file" name="audio" type="file" accept="audio/*,video/mp4,video/webm" required></label>
      <div class="pipeline-steps"><span><i>01</i> Transcribe</span><span><i>02</i> Identify speakers</span><span><i>03</i> Extract outcomes</span></div>
      <button class="primary" type="submit" ${busy ? 'disabled' : ''}>${busy ? '<span class="spinner"></span> Processing recording…' : 'Generate meeting record <span>→</span>'}</button>
      <div class="form-message ${errorMessage ? 'error' : ''}" role="status">${escapeHtml(errorMessage || 'Recordings are sent to configured providers for processing and are not stored.')}</div>
    </form>
    <div class="capability-row"><div><span class="cap-icon">◷</span><div><b>Word-level timing</b><small>Aligned transcript segments</small></div></div><div><span class="cap-icon">◉</span><div><b>Speaker turns</b><small>pyannote Community-1</small></div></div><div><span class="cap-icon">↗</span><div><b>Structured outcomes</b><small>Decisions and action items</small></div></div></div>
    <div class="privacy-note"><span>⌑</span><div><b>Audio is temporary; provider processing is explicit</b><p>Audio is sent to Deepgram; transcripts go to OpenAI only when configured. Source audio is deleted after processing. Meeting records stay in app memory until the service restarts.</p></div></div>
  </section>`;
}

function meetingView(meeting) {
  const speakers = [...new Set(meeting.turns.map(turn => turn.speaker).filter(Boolean))];
  return `<section class="meeting-page">
    ${meeting.warnings?.length ? `<div class="notice">${meeting.warnings.map(warning => `<p>${escapeHtml(warning)}</p>`).join('')}</div>` : ''}
    <div class="meeting-meta"><span class="meta-chip">${duration(meeting.duration_seconds)} recording</span><span class="meta-chip">${escapeHtml(meeting.language || 'Language detected')}</span>${speakers.length ? `<span class="meta-chip">${speakers.length} speakers</span>` : ''}<button id="export-record" class="export-button">Export JSON ↓</button></div>
    <div class="record-grid">
      <div class="left-column">
        <article class="panel summary-panel"><div class="panel-heading"><div><span class="panel-kicker">THE MEETING, AT A GLANCE</span><h2>Summary</h2></div><span class="panel-symbol">✳</span></div><ul class="summary-list">${meeting.summary.length ? meeting.summary.map(line => `<li>${escapeHtml(line)}</li>`).join('') : '<li>No summary was returned. Add OPENAI_API_KEY to extract a structured meeting record.</li>'}</ul>
          ${meeting.decisions.length ? `<div class="subsection"><div class="section-title"><span>✓</span> Decisions</div>${meeting.decisions.map(item => `<div class="decision"><b>${escapeHtml(item.decision)}</b>${item.evidence ? `<small>“${escapeHtml(item.evidence)}”</small>` : ''}</div>`).join('')}</div>` : ''}
          ${meeting.open_questions.length ? `<div class="subsection"><div class="section-title"><span>?</span> Open questions</div>${meeting.open_questions.map(item => `<div class="question">${escapeHtml(item)}</div>`).join('')}</div>` : ''}
        </article>
        <article class="panel actions-panel"><div class="panel-heading"><div><span class="panel-kicker">OWNERS AND NEXT STEPS</span><h2>Action items <span class="count">${meeting.action_items.length}</span></h2></div><span class="panel-symbol">↗</span></div>${meeting.action_items.length ? `<div class="action-list">${meeting.action_items.map(item => `<div class="action-item"><span class="checkbox"></span><div><b>${escapeHtml(item.task)}</b><small>${escapeHtml(item.owner || 'Owner not specified')}${item.due_date ? ` · Due ${escapeHtml(item.due_date)}` : ''}</small>${item.evidence ? `<small class="evidence">“${escapeHtml(item.evidence)}”</small>` : ''}</div></div>`).join('')}</div>` : '<p class="quiet-empty">No explicit action items found in this recording.</p>'}</article>
      </div>
      <article class="panel transcript-panel"><div class="panel-heading"><div><span class="panel-kicker">WORD-ALIGNED WITH SPEAKER LABELS</span><h2>Transcript</h2></div><span class="transcript-count">${meeting.turns.length} turns</span></div><div class="transcript-scroll">${meeting.turns.length ? meeting.turns.map(turn => `<div class="turn"><time>${timestamp(turn.start)}</time><div class="turn-body"><span class="speaker ${turn.speaker ? '' : 'unknown'}">${escapeHtml(turn.speaker || 'Speaker unknown')}</span><p>${escapeHtml(turn.text)}</p></div></div>`).join('') : `<p class="full-transcript">${escapeHtml(meeting.transcript)}</p>`}</div></article>
    </div><div class="provider-line">Processing: ${Object.entries(meeting.providers).map(([key, value]) => `<span>${escapeHtml(key)} · ${escapeHtml(value)}</span>`).join('')}</div>
  </section>`;
}

function bind() {
  document.querySelector('#new-meeting')?.addEventListener('click', () => { selected = null; errorMessage = ''; render(); });
  document.querySelectorAll('[data-meeting]').forEach(button => button.addEventListener('click', () => { selected = meetings.find(item => item.id === button.dataset.meeting) || null; render(); }));
  const input = document.querySelector('#audio-file');
  input?.addEventListener('change', () => {
    const file = input.files?.[0];
    const label = document.querySelector('.drop-zone strong');
    if (file && label) label.textContent = file.name;
  });
  const drop = document.querySelector('.drop-zone');
  drop?.addEventListener('dragover', event => { event.preventDefault(); drop.classList.add('dragging'); });
  drop?.addEventListener('dragleave', () => drop.classList.remove('dragging'));
  drop?.addEventListener('drop', event => {
    event.preventDefault(); drop.classList.remove('dragging');
    const file = event.dataTransfer.files[0];
    if (file && input) { const transfer = new DataTransfer(); transfer.items.add(file); input.files = transfer.files; input.dispatchEvent(new Event('change')); }
  });
  document.querySelector('#upload-form')?.addEventListener('submit', uploadMeeting);
  document.querySelector('#export-record')?.addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(selected, null, 2)], { type: 'application/json' });
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${selected.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.json`; link.click(); URL.revokeObjectURL(link.href);
  });
}

async function uploadMeeting(event) {
  event.preventDefault();
  const file = document.querySelector('#audio-file').files[0];
  if (!file) return;
  busy = true; errorMessage = ''; render();
  const body = new FormData(); body.append('audio', file);
  try {
    const response = await fetch('/api/meetings', { method: 'POST', body });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Could not process this recording.');
    meetings = [payload, ...meetings.filter(item => item.id !== payload.id)]; selected = payload;
  } catch (error) {
    selected = null; errorMessage = error.message || 'Meeting processing failed.';
  } finally { busy = false; render(); }
}

async function loadMeetings() {
  try {
    const response = await fetch('/api/meetings');
    if (response.ok) meetings = await response.json();
  } catch { /* The upload panel remains usable when the API is waking up. */ }
  render();
}

loadMeetings();
