import './style.css';

let documents = [
  { id: 1, source: 'Slack', icon: '#4A154B', title: '#launch-room · Go-to-market check-in', author: 'Maya Chen', date: 'Today, 10:42 AM', body: 'The Enterprise plan is approved for a phased launch. Sales enablement needs the final competitive positioning and the updated security one-pager before the November 4 announcement.', score: 94, tags: ['Launch', 'Enterprise'] },
  { id: 2, source: 'Confluence', icon: '#1868DB', title: 'Enterprise launch plan', author: 'Growth team', date: 'Updated yesterday', body: 'Phase one starts with existing design partners. The public release is targeted for November 4, contingent on legal approval of the updated terms and security review.', score: 91, tags: ['Launch', 'Strategy'] },
  { id: 3, source: 'Jira', icon: '#0052CC', title: 'GTM-184 · Finalize launch enablement', author: 'Alex Morgan', date: 'Due Oct 30', body: 'Complete the battlecard, announcement brief, and account list. Dependencies: LEGAL-72 and SEC-91 must be resolved before external communications are scheduled.', score: 87, tags: ['Launch', 'Blocked'] },
  { id: 4, source: 'Email', icon: '#EA4335', title: 'Re: Enterprise announcement timing', author: 'Priya Shah', date: 'Oct 21', body: 'We can support a November 4 launch provided the customer-facing docs use the approved claims. I will share the final language by Friday.', score: 82, tags: ['Launch', 'Legal'] },
  { id: 5, source: 'Drive', icon: '#0F9D58', title: 'Enterprise launch narrative v3', author: 'Marketing', date: 'Oct 19', body: 'The core story centers on trusted knowledge access with source-grounded answers, permission-aware retrieval, and measurable time to insight.', score: 76, tags: ['Messaging'] }
];

const app = document.querySelector('#app');
let selected = documents[0];
let activeSource = 'All sources';
let searchTerm = 'What is the plan for the enterprise launch?';
let answerData = null;
let searchNotice = 'Sample company data · citations are linked to retrieved passages';

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  })[character]);
}

function sourceMark(doc) {
  const colors = { Slack: '#4A154B', Confluence: '#1868DB', Jira: '#0052CC', Email: '#EA4335', Drive: '#0F9D58' };
  return `<span class="source-mark" style="--mark:${doc.icon || colors[doc.source] || '#54736a'}">${doc.source.slice(0, 1)}</span>`;
}

function filteredDocs() {
  const query = searchTerm.toLowerCase().trim();
  return documents.filter(doc =>
    (activeSource === 'All sources' || doc.source === activeSource) &&
    (!query || `${doc.title} ${doc.body} ${doc.tags.join(' ')}`.toLowerCase().includes(query) || query.includes('enterprise') && doc.tags.includes('Launch'))
  );
}

function render() {
  const docs = answerData ? documents : filteredDocs();
  app.innerHTML = `
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">R</span><span>relay</span></div>
      <nav>
        <a class="nav-item active" href="#search"><span>⌕</span> Search <kbd>⌘ K</kbd></a>
        <a class="nav-item" href="#collections"><span>▣</span> Collections</a>
        <a class="nav-item" href="#alerts"><span>◌</span> Alerts <b>3</b></a>
      </nav>
      <div class="nav-label">WORKSPACES</div>
      <nav>
        <a class="nav-item" href="#all">All company</a>
        <a class="nav-item" href="#product"><span class="dot cyan"></span> Product</a>
        <a class="nav-item" href="#revenue"><span class="dot gold"></span> Revenue</a>
        <a class="nav-item" href="#ops"><span class="dot purple"></span> Operations</a>
      </nav>
      <div class="sidebar-bottom">
        <button class="new-search" id="new-search">＋ New search</button>
        <div class="user"><div class="avatar">VC</div><div><strong>Vishnu</strong><span>Acme, Inc.</span></div><button aria-label="Settings">⚙</button></div>
      </div>
    </aside>
    <main>
      <header><div class="crumb">SEARCH <span>/</span> SAMPLE COMPANY</div><div class="header-actions"><button class="about-trigger" id="about-button">About this demo</button><button class="avatar small">VC</button></div></header>
      <section class="search-area">
        <h1>Find answers across your company</h1>
        <div class="search-box"><span>⌕</span><input id="search-input" value="${escapeHtml(searchTerm)}" aria-label="Search company knowledge"/><button id="clear-search" aria-label="Clear search">×</button><button class="ask" id="ask-button">Ask</button></div>
        <p class="demo-note" role="status">${escapeHtml(searchNotice)}</p>
        <div class="suggestions"><span>Try asking</span><button>What did we decide about pricing?</button><button>Summarize customer feedback</button><button>Who owns the Q4 plan?</button></div>
      </section>
      <section class="content ${docs.length ? '' : 'empty'}">
        <div class="results-column">
          <div class="result-toolbar"><strong>${docs.length} results</strong><span>Sorted by relevance <button>⌄</button></span></div>
          <div class="source-filters">${['All sources','Slack','Confluence','Jira','Email','Drive'].map(source => `<button class="${activeSource === source ? 'selected' : ''}" data-source="${source}">${source}</button>`).join('')}</div>
          <div class="results-list">${docs.length ? docs.map(doc => `
            <article class="result ${selected.id === doc.id ? 'selected' : ''}" data-id="${doc.id}">
              <div class="result-top">${sourceMark(doc)}<span>${escapeHtml(doc.source)}</span><time>${escapeHtml(doc.date)}</time><span class="score">${escapeHtml(doc.score)}% match</span></div>
              <h2>${escapeHtml(doc.title)}</h2><p>${escapeHtml(doc.body)}</p>
              <footer><span>${escapeHtml(doc.author)}</span>${doc.tags.map(tag => `<em>${escapeHtml(tag)}</em>`).join('')}</footer>
            </article>`).join('') : `<div class="empty-state"><div>⌕</div><h2>No matching knowledge found</h2><p>Try a broader question or remove a source filter.</p></div>`}</div>
        </div>
        <aside class="answer-panel">
          <div class="answer-head"><span class="spark">✦</span><span>ANSWER</span><button aria-label="More options">•••</button></div>
          <h2>${escapeHtml(answerData ? answerData.answer : 'Enterprise launch is planned for November 4')}</h2>
          <p>${answerData ? (answerData.grounded ? 'This answer was generated only from the retrieved source passages below.' : 'The available evidence was insufficient for a grounded answer.') : 'The team is preparing a phased Enterprise launch, starting with existing design partners. The date depends on legal approval of customer-facing terms and the security review.'}</p>
          <div class="answer-list"><div><b>What needs to happen next</b><span>Sales enablement, competitive positioning, and the security one-pager need to be finalized.</span></div><div><b>Who is involved</b><span>Growth, Legal, Security, Marketing, and the Revenue team.</span></div></div>
          <div class="citations"><span>Sources</span>${(answerData ? answerData.citations : [{source:'Slack',title:'#launch-room'},{source:'Confluence',title:'Launch plan'},{source:'Jira',title:'GTM-184'}]).map((citation,index) => `<button class="citation" data-id="${escapeHtml(citation.id || documents[index]?.id || 1)}"><i>${index + 1}</i> ${escapeHtml(citation.source)} · ${escapeHtml(citation.title)}</button>`).join('')}</div>
          <div class="answer-feedback"><span>Was this helpful?</span><button>↑</button><button>↓</button><button>Share</button></div>
        </aside>
      </section>
      <dialog id="about-dialog"><div class="dialog-head"><span>HOW RELAY WORKS</span><button id="close-about" aria-label="Close">×</button></div><h2>Enterprise search with evidence, not guesswork.</h2><ol><li><b>Ingest</b> — safe sample Slack, email, Jira, Confluence, and Drive records are chunked.</li><li><b>Retrieve</b> — dense + sparse Qdrant search finds relevant passages.</li><li><b>Rerank</b> — an optional reranker prioritizes the strongest evidence.</li><li><b>Answer with citations</b> — every response is grounded in the retrieved passages.</li></ol><p><strong>Evaluation:</strong> tracks context recall@10 and MRR on representative questions. This public demo contains synthetic data only.</p></dialog>
    </main>`;
  bindEvents();
}

function bindEvents() {
  document.querySelectorAll('[data-source]').forEach(button => button.addEventListener('click', () => {
    activeSource = button.dataset.source;
    if (answerData) search(searchTerm); else render();
  }));
  document.querySelectorAll('.result, .citation').forEach(item => item.addEventListener('click', () => { selected = documents.find(doc => String(doc.id) === item.dataset.id) || selected; render(); }));
  document.querySelector('#search-input').addEventListener('keydown', event => { if (event.key === 'Enter') search(event.target.value); });
  document.querySelector('#ask-button').addEventListener('click', () => search(document.querySelector('#search-input').value));
  document.querySelector('#clear-search').addEventListener('click', () => { searchTerm = ''; render(); document.querySelector('#search-input').focus(); });
  document.querySelector('#new-search').addEventListener('click', () => { searchTerm = ''; activeSource = 'All sources'; selected = documents[0]; render(); document.querySelector('#search-input').focus(); });
  document.querySelectorAll('.suggestions button').forEach(button => button.addEventListener('click', () => search(button.textContent)));
  const dialog = document.querySelector('#about-dialog');
  document.querySelector('#about-button').addEventListener('click', () => dialog.showModal());
  document.querySelector('#close-about').addEventListener('click', () => dialog.close());
}

async function search(query) {
  searchTerm = query;
  searchNotice = 'Searching the sample company knowledge base…';
  render();
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    const response = await fetch('/api/search', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, sources: activeSource === 'All sources' ? [] : [activeSource], limit: 8 }), signal: controller.signal
    });
    clearTimeout(timer);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Search API is unavailable');
    answerData = payload;
    documents = answerData.results.map(result => ({ id: result.id, source: result.source, title: result.title, author: result.author || 'Unknown', date: 'Retrieved now', body: result.excerpt, score: Math.round(result.score * 100), tags: ['Cited'] }));
    selected = documents[0] || selected;
    searchNotice = answerData.notice || 'Sample company data · every answer includes its retrieved evidence';
  } catch (error) {
    answerData = null;
    searchNotice = `${error.message || 'The demo service is waking up.'} Showing the sample preview instead.`;
  }
  render();
}

render();
