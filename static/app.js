const state = {
  conversations: [],
  currentConvId: null,
  currentModel: 'minimax-m3:cloud',
  streaming: false,
  theme: 'dark',
  availableModels: [],
  modelPulling: false
};

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

function apiFetch(url, opts = {}) {
  const token = localStorage.getItem('ollama_token');
  const headers = opts.headers || {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetch(url, { ...opts, headers, credentials: 'same-origin' });
}

const el = {
  messages: $('#messages'),
  welcome: $('#welcome'),
  inputArea: $('#inputArea'),
  messageInput: $('#messageInput'),
  sendBtn: $('#sendBtn'),
  stopBtn: $('#stopBtn'),
  conversationList: $('#conversationList'),
  modelInput: $('#modelInput'),
  modelSuggest: $('#modelSuggest'),
  modelStatus: $('#modelStatus'),
  newChatBtn: $('#newChatBtn'),
  themeToggle: $('#themeToggle'),
  themeText: $('#themeText'),
  refreshModels: $('#refreshModels'),

  sidebarToggle: $('#sidebarToggle'),
  sidebar: $('#sidebar'),
  systemPrompt: $('#systemPrompt'),
  temperature: $('#temperature'),
  topP: $('#topP'),
  topK: $('#topK'),
  maxTokens: $('#maxTokens'),
  tempVal: $('#tempVal'),
  topPVal: $('#topPVal'),
  topKVal: $('#topKVal'),
  maxTokensVal: $('#maxTokensVal'),
  modelBadge: $('#modelBadge'),
  adminHeaderBtn: $('#adminHeaderBtn'),
  modal: $('#confirmModal'),
  modalMsg: $('#modalMsg'),
  modalConfirm: $('#modalConfirm'),
  modalCancel: $('#modalCancel'),
  statusText: $('#statusText'),
  logoutBtn: $('#logoutBtn'),
  userDisplayName: $('#userDisplayName'),
  userAvatar: $('#userAvatar'),
  userBadge: $('#userBadge'),
  navBackBtn: $('#navBackBtn'),
  navNextBtn: $('#navNextBtn'),
  settingsBtn: $('#settingsBtn'),
  settingsModal: $('#settingsModal'),
  settingsCloseBtn: $('#settingsCloseBtn'),
  ragToggleBtn: $('#ragToggleBtn'),
  ragPanel: $('#ragPanel'),
  ragPanelCloseBtn: $('#ragPanelCloseBtn'),
  ragDropZone: $('#ragDropZone'),
  ragFileInput: $('#ragFileInput'),
  ragUploadStatus: $('#ragUploadStatus'),
  ragList: $('#ragList')
};

// === THEME ===
function initTheme() {
  state.theme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', state.theme);
  el.themeText.textContent = state.theme === 'dark' ? 'Dark mode' : 'Light mode';
}

initTheme();

el.themeToggle.addEventListener('click', () => {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', state.theme);
  localStorage.setItem('theme', state.theme);
  el.themeText.textContent = state.theme === 'dark' ? 'Dark mode' : 'Light mode';
});

// === SIDEBAR TOGGLE (mobile) ===
el.sidebarToggle.addEventListener('click', () => {
  el.sidebar.classList.toggle('open');
});

// Close sidebar on conv click (mobile)
document.addEventListener('click', (e) => {
  if (window.innerWidth <= 768 && el.sidebar.classList.contains('open') && !el.sidebar.contains(e.target) && e.target !== el.sidebarToggle) {
    el.sidebar.classList.remove('open');
  }
});

// === AUTO RESIZE TEXTAREA ===
el.messageInput.addEventListener('input', () => {
  el.messageInput.style.height = 'auto';
  el.messageInput.style.height = Math.min(el.messageInput.scrollHeight, 200) + 'px';
});

// === MODELS ===
const modelState = {
  catalog: [],
  categories: [],
  installed: [],
  dropdownOpen: false,
  filterText: ''
};

async function loadModelCatalog() {
  try {
    const resp = await apiFetch('/api/models/catalog');
    const data = await resp.json();
    modelState.catalog = data.models || [];
    modelState.categories = data.categories || [];
    modelState.installed = modelState.catalog.filter(m => m.installed).map(m => m.name);
    state.availableModels = modelState.installed;
    if (!modelState.installed.includes(state.currentModel)) {
      el.modelInput.value = state.currentModel;
    } else {
      el.modelInput.value = state.currentModel;
    }
    updateModelBadge();
  } catch (e) {
    console.error('load catalog:', e);
  }
}

function renderModelDropdown(filter = '') {
  let items = modelState.catalog;
  if (filter) {
    const f = filter.toLowerCase();
    items = items.filter(m => m.name.toLowerCase().includes(f) || m.description.toLowerCase().includes(f));
  }
  if (!items.length) {
    el.modelDropdown.innerHTML = '<div class="model-dropdown-empty">No models found</div>';
    return;
  }
  // Group by category
  const grouped = {};
  for (const m of items) {
    (grouped[m.category] = grouped[m.category] || []).push(m);
  }
  let html = '';
  for (const cat of modelState.categories) {
    if (!grouped[cat]) continue;
    html += `<div class="model-dropdown-header">${cat}</div>`;
    for (const m of grouped[cat]) {
      const isInstalled = m.installed;
      const isSelected = m.name === state.currentModel;
      html += `
        <div class="model-dropdown-item ${isSelected ? 'selected' : ''}" data-name="${m.name}">
          <span class="mdl-dot ${isInstalled ? 'installed' : 'uninstalled'}"></span>
          <span class="mdl-name">${m.name}</span>
          <span class="mdl-desc">${m.description}</span>
          <span class="mdl-cat">${m.category}</span>
          ${isInstalled ? '' : '<span class="mdl-pull-badge">Pull</span>'}
        </div>
      `;
    }
  }
  el.modelDropdown.innerHTML = html;

  // Click handlers
  el.modelDropdown.querySelectorAll('.model-dropdown-item').forEach(item => {
    item.addEventListener('click', () => {
      const name = item.dataset.name;
      const entry = modelState.catalog.find(m => m.name === name);
      if (!entry) return;
      if (entry.installed) {
        selectModel(name);
        closeModelDropdown();
      } else {
        selectModel(name);
        closeModelDropdown();
        // focus input might re-open dropdown, so we let selectModel handle pull
      }
    });
  });
}

function openModelDropdown() {
  if (modelState.dropdownOpen) return;
  modelState.dropdownOpen = true;
  renderModelDropdown(modelState.filterText);
  el.modelDropdown.style.display = '';
}

function closeModelDropdown() {
  modelState.dropdownOpen = false;
  el.modelDropdown.style.display = 'none';
}

el.modelInput.addEventListener('focus', () => {
  openModelDropdown();
});

el.modelInput.addEventListener('input', () => {
  modelState.filterText = el.modelInput.value;
  if (modelState.dropdownOpen) {
    renderModelDropdown(modelState.filterText);
  }
});

el.modelInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    selectModel(el.modelInput.value.trim());
    closeModelDropdown();
  }
  if (e.key === 'Escape') {
    closeModelDropdown();
  }
});

// Close dropdown on click outside
document.addEventListener('click', (e) => {
  if (modelState.dropdownOpen && !e.target.closest('.model-combo-wrapper')) {
    closeModelDropdown();
  }
});

el.refreshModels.addEventListener('click', () => { loadModelCatalog(); });

async function selectModel(name) {
  if (!name || state.modelPulling) return;
  state.currentModel = name;
  el.modelInput.value = name;
  updateModelBadge();

  if (modelState.installed.includes(name)) return;

  state.modelPulling = true;
  el.modelStatus.textContent = `⏳ Pulling ${name}...`;
  el.modelStatus.className = 'pull-status pulling';

  try {
    const resp = await apiFetch('/api/models/pull', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (!resp.ok) {
      el.modelStatus.textContent = `❌ Pull failed: ${resp.statusText}`;
      el.modelStatus.className = 'pull-status error';
      state.modelPulling = false;
      return;
    }
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      for (const line of buffer.split('\n')) {
        const t = line.trim();
        if (!t.startsWith('data: ')) continue;
        const d = t.slice(6).trim();
        if (d === '[DONE]') continue;
        try {
          const p = JSON.parse(d);
          if (p.error) { el.modelStatus.textContent = `❌ ${p.error}`; el.modelStatus.className = 'pull-status error'; break; }
          el.modelStatus.textContent = p.status || '';
          if (p.done) {
            el.modelStatus.textContent = `✅ ${name} ready!`;
            el.modelStatus.className = 'pull-status success';
            loadModelCatalog();
          }
        } catch(e) {}
      }
      buffer = '';
    }
  } catch(e) {
    el.modelStatus.textContent = `❌ ${e.message}`;
    el.modelStatus.className = 'pull-status error';
  }
  state.modelPulling = false;
}

function updateModelBadge() {
  el.modelBadge.textContent = `Model: ${state.currentModel || 'none'}`;
}

// === CONVERSATIONS ===
async function loadConversations() {
  try {
    const resp = await apiFetch('/api/conversations');
    const data = await resp.json();
    state.conversations = data.conversations || [];
    renderConversationList();
    updateNavButtons();
  } catch (e) {
    console.error('load conversations:', e);
  }
}

function renderConversationList() {
  el.conversationList.innerHTML = '';
  if (state.conversations.length === 0) {
    el.conversationList.innerHTML = '<div style="padding:16px;text-align:center;color:var(--sidebar-text);font-size:12px;">No conversations yet</div>';
    return;
  }
  state.conversations.forEach(c => {
    const div = document.createElement('div');
    div.className = 'conv-item' + (c.id === state.currentConvId ? ' active' : '');
    div.innerHTML = `
      <span class="conv-title">${escapeHtml(c.title)}</span>
      <button class="conv-del" data-id="${c.id}" title="Delete">✕</button>
    `;
    div.addEventListener('click', (e) => {
      if (e.target.closest('.conv-del')) return;
      switchConversation(c.id);
    });
    div.querySelector('.conv-del').addEventListener('click', (e) => {
      e.stopPropagation();
      confirmDelete(c.id, c.title);
    });
    el.conversationList.appendChild(div);
  });
}

async function switchConversation(convId) {
  if (state.streaming) return;
  try {
    const resp = await apiFetch(`/api/conversations/${convId}`);
    if (!resp.ok) return;
    const conv = await resp.json();
    state.currentConvId = convId;
    renderConversationList();
    updateNavButtons();
    renderMessages(conv.messages || []);
    showChat();
    el.messageInput.focus();
    if (window.innerWidth <= 768) el.sidebar.classList.remove('open');
  } catch (e) {
    console.error('switch conv:', e);
  }
}

// === MESSAGES ===
function renderMessages(messages) {
  el.messages.innerHTML = '';
  messages.forEach(msg => appendMessage(msg.role, msg.content, false));
  el.messages.scrollTop = el.messages.scrollHeight;
}

function appendMessage(role, content, animated = true) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  const avatar = role === 'user' ? '🧑' : '🤖';
  const contentHtml = role === 'assistant' ? renderMarkdown(content) : escapeHtml(content);
  div.innerHTML = `
    <div class="avatar">${avatar}</div>
    <div class="msg-body">
      <div class="msg-content">${contentHtml}</div>
      <div class="msg-actions">
        ${role === 'assistant' ? '<button class="msg-action-btn copy-btn" title="Copy">📋 Copy</button>' : ''}
      </div>
    </div>
  `;

  if (role === 'assistant') {
    const copyBtn = div.querySelector('.copy-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        const text = getPlainText(content);
        navigator.clipboard.writeText(text).then(() => {
          copyBtn.textContent = '✅ Copied!';
          setTimeout(() => { copyBtn.textContent = '📋 Copy'; }, 2000);
        }).catch(() => {
          copyBtn.textContent = '❌ Failed';
        });
      });
    }
  }

  el.messages.appendChild(div);
  if (animated) el.messages.scrollTop = el.messages.scrollHeight;
  return div;
}

function updateLastMessage(content) {
  const last = el.messages.lastElementChild;
  if (last && last.classList.contains('assistant')) {
    const bubble = last.querySelector('.msg-content');
    if (bubble) {
      bubble.innerHTML = renderMarkdown(content);
      el.messages.scrollTop = el.messages.scrollHeight;
    }
  }
}

function showChat() {
  el.welcome.style.display = 'none';
  el.messages.style.display = 'flex';
}

function showWelcome() {
  el.welcome.style.display = 'flex';
  el.messages.style.display = 'none';
  el.messages.innerHTML = '';
  state.currentConvId = null;
  $$('.conv-item.active').forEach(e => e.classList.remove('active'));
}

// === NEW CHAT ===
el.newChatBtn.addEventListener('click', () => {
  if (state.streaming) return;
  showWelcome();
  el.messageInput.value = '';
  el.messageInput.style.height = 'auto';
  el.messageInput.focus();
});

// === SEND ===
el.sendBtn.addEventListener('click', sendMessage);
el.messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

async function sendMessage() {
  const text = el.messageInput.value.trim();
  if (!text || state.streaming) return;

  const convId = state.currentConvId || crypto.randomUUID();

  if (!state.currentConvId) {
    state.currentConvId = convId;
    showChat();
    el.messages.innerHTML = '';
  } else {
    showChat();
  }

  appendMessage('user', text);
  el.messageInput.value = '';
  el.messageInput.style.height = 'auto';

  const assistantDiv = appendMessage('assistant', '<div class="typing-indicator"><span></span><span></span><span></span>');

  setStreaming(true);

  try {
    const resp = await apiFetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        conversation_id: convId,
        model: state.currentModel,
        system_prompt: el.systemPrompt.value.trim(),
        temperature: parseFloat(el.temperature.value),
        top_p: parseFloat(el.topP.value),
        top_k: parseInt(el.topK.value),
        max_tokens: parseInt(el.maxTokens.value)
      })
    });

    if (!resp.ok) {
      const err = await resp.text();
      updateLastMessage(`Error: ${err}`);
      setStreaming(false);
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullContent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;
        const data = trimmed.slice(6).trim();
        if (data === '[DONE]') continue;

        try {
          const parsed = JSON.parse(data);
          if (parsed.error) {
            updateLastMessage(`Error: ${parsed.error}`);
            setStreaming(false);
            return;
          }
          if (parsed.queue) {
            updateLastMessage(`⏳ Đang chờ xử lý... Vị trí: #${parsed.queue}`);
            continue;
          }
          if (parsed.content) {
            fullContent += parsed.content;
            updateLastMessage(fullContent);
          }
          if (parsed.conversation_id) {
            state.currentConvId = parsed.conversation_id;
          }
        } catch (e) {}
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      updateLastMessage(`Error: ${e.message}`);
    }
  }

  setStreaming(false);
  await loadConversations();
  renderConversationList();
  el.messageInput.focus();
}

function setStreaming(val) {
  state.streaming = val;
  el.sendBtn.style.display = val ? 'none' : 'flex';
  el.stopBtn.style.display = val ? 'flex' : 'none';
  el.messageInput.disabled = val;
}

el.stopBtn.addEventListener('click', () => {
  setStreaming(false);
});

// === DELETE ===
let deleteTarget = null;

function confirmDelete(id, title) {
  deleteTarget = id;
  el.modalMsg.textContent = `Delete "${title}"?`;
  el.modal.style.display = 'flex';
}

el.modalConfirm.addEventListener('click', async () => {
  if (!deleteTarget) return;
  try {
    await apiFetch(`/api/conversations/${deleteTarget}`, { method: 'DELETE' });
    if (state.currentConvId === deleteTarget) showWelcome();
    deleteTarget = null;
    el.modal.style.display = 'none';
    await loadConversations();
    renderConversationList();
  } catch (e) {
    console.error('delete:', e);
  }
});

const closeModal = () => {
  deleteTarget = null;
  el.modal.style.display = 'none';
};
el.modalCancel.addEventListener('click', closeModal);
el.modal.addEventListener('click', (e) => {
  if (e.target === el.modal || e.target.classList.contains('modal-backdrop')) closeModal();
});

// === SETTINGS MODAL ===
function openSettings() {
  el.settingsModal.style.display = 'flex';
}

function closeSettings() {
  el.settingsModal.style.display = 'none';
}

el.settingsBtn.addEventListener('click', openSettings);
el.settingsCloseBtn.addEventListener('click', closeSettings);
el.settingsModal.addEventListener('click', (e) => {
  if (e.target === el.settingsModal || e.target.classList.contains('settings-backdrop')) closeSettings();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && el.settingsModal.style.display === 'flex') closeSettings();
});

// === RAG TOGGLE ===
let ragOpen = false;
el.ragToggleBtn.addEventListener('click', () => {
  ragOpen = !ragOpen;
  el.ragPanel.style.display = ragOpen ? '' : 'none';
  el.ragToggleBtn.classList.toggle('active', ragOpen);
});
el.ragPanelCloseBtn.addEventListener('click', () => {
  ragOpen = false;
  el.ragPanel.style.display = 'none';
  el.ragToggleBtn.classList.remove('active');
});

// === SLIDERS ===
['temperature', 'topP', 'topK', 'maxTokens'].forEach(id => {
  const slider = document.getElementById(id);
  const display = document.getElementById(id + 'Val');
  if (slider && display) {
    slider.addEventListener('input', () => { display.textContent = slider.value; });
  }
});

// === MARKDOWN RENDERER ===
function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

function getPlainText(md) {
  const cleaned = md.replace(/```[\s\S]*?```/g, match => {
    return match.replace(/```\w*\n?/, '').replace(/```$/, '');
  });
  return cleaned.replace(/[*_~`#\[\]()>|]/g, '').replace(/\n{3,}/g, '\n\n').trim();
}

function renderMarkdown(text) {
  if (!text) return '';
  let html = text;

  // Code blocks - must be first
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const langClass = lang ? ` class="language-${escapeHtml(lang)}"` : '';
    return `<pre><code${langClass}>${escapeHtml(code.trim())}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Headers
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Bold + italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Strikethrough
  html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');

  // Blockquotes
  html = html.replace(/^> (.+)$/gm, '<blockquote><p>$1</p></blockquote>');

  // Horizontal rules
  html = html.replace(/^---\s*$/gm, '<hr>');

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Unordered lists
  let inList = false;
  html = html.split('\n').map(line => {
    const ulMatch = line.match(/^[*\-] (.+)$/);
    const olMatch = line.match(/^\d+\. (.+)$/);
    if (ulMatch) {
      if (!inList) { inList = 'ul'; return '<ul>\n<li>' + ulMatch[1] + '</li>'; }
      return '<li>' + ulMatch[1] + '</li>';
    }
    if (olMatch) {
      if (!inList) { inList = 'ol'; return '<ol>\n<li>' + olMatch[1] + '</li>'; }
      return '<li>' + olMatch[1] + '</li>';
    }
    if (inList) {
      const close = inList === 'ul' ? '</ul>' : '</ol>';
      inList = false;
      return close + '\n' + line;
    }
    return line;
  }).join('\n');
  if (inList) {
    html += inList === 'ul' ? '</ul>' : '</ol>';
  }

  // Tables
  html = html.replace(/\n((\|[^\n]+\|)(?:\n\|[-\s:|]+\|)?(?:\n\|[^\n]+\|)*)/g, (match) => {
    const rows = match.trim().split('\n').filter(r => r.trim());
    let table = '<table>\n';
    let headerDone = false;
    rows.forEach((row, i) => {
      if (row.match(/^[\s|:,-]+$/)) { headerDone = true; return; }
      const cells = row.split('|').filter(c => c.trim());
      const tag = (i === 0 || headerDone) ? 'td' : 'th';
      if (i === 1 && !headerDone) return;
      table += '<tr>';
      cells.forEach(c => { table += `<${tag}>${c.trim()}</${tag}>`; });
      table += '</tr>\n';
    });
    table += '</table>';
    return '\n' + table;
  });

  // Paragraphs - wrap consecutive non-block lines
  const blockTags = 'h[1-4]|pre|blockquote|ul|ol|li|table|tr|td|th|hr|div';
  const blockRE = new RegExp(`^<(${blockTags})`);
  const parts = html.split('\n\n');
  html = parts.map(part => {
    const trimmed = part.trim();
    if (!trimmed) return '';
    if (blockRE.test(trimmed)) return trimmed;
    return '<p>' + trimmed.replace(/\n/g, '<br>') + '</p>';
  }).join('\n');

  return html;
}

// === NAVIGATION ===
function navConv(dir) {
  const idx = state.conversations.findIndex(c => c.id === state.currentConvId);
  if (idx === -1) return;
  const target = idx + dir;
  if (target < 0 || target >= state.conversations.length) return;
  switchConversation(state.conversations[target].id);
}

function updateNavButtons() {
  const idx = state.conversations.findIndex(c => c.id === state.currentConvId);
  el.navBackBtn.disabled = idx <= 0;
  el.navNextBtn.disabled = idx === -1 || idx >= state.conversations.length - 1;
}

// === AUTH / USER ===
async function checkAuth() {
  try {
    const resp = await apiFetch('/api/auth/me');
    if (!resp.ok) {
      window.location.href = '/';
      return null;
    }
    const user = await resp.json();
    el.userDisplayName.textContent = user.username;
    if (user.role === 'admin') {
      el.userBadge.textContent = 'Admin';
      el.adminHeaderBtn.style.display = '';
    }
    state.user = user;
    return user;
  } catch (e) {
    window.location.href = '/';
    return null;
  }
}

el.logoutBtn?.addEventListener('click', async () => {
  await apiFetch('/api/auth/logout', { method: 'POST' });
  window.location.href = '/';
});

// === RAG (file upload, session-only, cyber security) ===
async function loadRagDocs() {
  try {
    const resp = await apiFetch('/api/rag/documents');
    if (!resp.ok) return;
    const data = await resp.json();
    if (!data.documents || data.documents.length === 0) {
      el.ragList.innerHTML = '<div class="rag-file-list-empty">No documents</div>';
      return;
    }
    el.ragList.innerHTML = data.documents.map(d => `
      <div class="rag-file-item">
        <span class="file-icon">📄</span>
        <span class="file-name">${d.filename}</span>
        <span class="file-chunks">${d.chunks} chunks</span>
        <button class="file-del" onclick="deleteRagDoc('${d.id}')">✕</button>
      </div>
    `).join('');
  } catch(e) {}
}

async function deleteRagDoc(id) {
  await apiFetch(`/api/rag/documents/${id}`, {method:'DELETE'});
  loadRagDocs();
}

async function uploadRagFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  el.ragUploadStatus.textContent = `⏳ Processing ${file.name}...`;
  el.ragUploadStatus.className = 'rag-upload-status pulling';
  try {
    const resp = await apiFetch('/api/rag/upload-file', {
      method: 'POST',
      body: formData
    });
    if (resp.ok) {
      const data = await resp.json();
      el.ragUploadStatus.textContent = `✅ ${data.filename} added (${data.chunks} chunks)`;
      el.ragUploadStatus.className = 'rag-upload-status success';
      loadRagDocs();
    } else {
      const err = await resp.text();
      try {
        const j = JSON.parse(err);
        el.ragUploadStatus.textContent = `❌ ${j.detail || 'Upload failed'}`;
      } catch {
        el.ragUploadStatus.textContent = `❌ Upload failed`;
      }
      el.ragUploadStatus.className = 'rag-upload-status error';
    }
  } catch(e) {
    el.ragUploadStatus.textContent = `❌ ${e.message}`;
    el.ragUploadStatus.className = 'rag-upload-status error';
  }
}

// File input click via drop zone
el.ragDropZone.addEventListener('click', () => el.ragFileInput.click());

el.ragFileInput.addEventListener('change', () => {
  for (const file of el.ragFileInput.files) {
    uploadRagFile(file);
  }
  el.ragFileInput.value = '';
});

// Drag & drop
el.ragDropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  el.ragDropZone.classList.add('dragover');
});
el.ragDropZone.addEventListener('dragleave', () => {
  el.ragDropZone.classList.remove('dragover');
});
el.ragDropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  el.ragDropZone.classList.remove('dragover');
  for (const file of e.dataTransfer.files) {
    uploadRagFile(file);
  }
});

// === INIT ===
async function init() {
  const user = await checkAuth();
  if (!user) return;
  await loadModelCatalog();
  await loadConversations();
  await loadRagDocs();
  renderConversationList();
  showWelcome();
}

init();
