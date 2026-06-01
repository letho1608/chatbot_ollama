const $ = s => document.querySelector(s), $$ = s => document.querySelectorAll(s);
const api = (u,o={}) => { const t=localStorage.getItem('ollama_token'), h=o.headers||{}; if(t)h['Authorization']=`Bearer ${t}`; return fetch(u,{...o,headers:h,credentials:'same-origin'}); };

const S = { section:'dashboard', stats:null, catalogModels:[], installedModels:[], modelDetails:[], umUserId:null };

const el = {
  sectionTitle: $('#adminSectionTitle'),
  sidebarName: $('#adminSidebarName'),
  topbarName: $('#adminTopbarName'),
  navUsersCount: $('#navUsersCount'),
  navModelsCount: $('#navModelsCount'),
  navConvsCount: $('#navConvsCount'),
  usersCountBadge: $('#usersCountBadge'),
  modelsCountBadge: $('#modelsCountBadge'),
  convsCountBadge: $('#convsCountBadge'),
  quickStats: $('#adminQuickStats'),
  userList: $('#adminUserList'),
  modelInput: $('#adminModelInput'),
  modelSuggest: $('#adminModelSuggest'),
  modelPullBtn: $('#adminModelPullBtn'),
  modelStatus: $('#adminModelStatus'),
  modelList: $('#adminModelList'),
  modelFilter: $('#adminModelFilter'),
  pullProgressBar: $('#pullProgressBar'),
  pullProgressFill: $('#pullProgressFill'),
  convList: $('#adminConvList'),
  convSearch: $('#adminConvSearch'),
  convRefreshBtn: $('#adminConvRefreshBtn'),
  auditList: $('#adminAuditList'),
  auditEventFilter: $('#auditEventFilter'),
  auditUserSearch: $('#auditUserSearch'),
  auditCountBadge: $('#auditCountBadge'),
  sysInfo: $('#adminSysInfo'),
  activityTotalLabel: $('#activityTotalLabel'),
  dashActivityFeed: $('#dashActivityFeed'),
  dashTopUsers: $('#dashTopUsers'),
  dashMsgChart: $('#dashMsgChart'),
  dashActivityCount: $('#dashActivityCount'),
  dashTopUsersCount: $('#dashTopUsersCount'),
  adminActivityList: $('#adminActivityList'),
  umAvatar: $('#umAvatar'),
  umName: $('#umName'),
  umMeta: $('#umMeta'),
  umActivityTab: $('#umActivityTab'),
  umConversationsTab: $('#umConversationsTab'),
  userModal: $('#userModal'),
};
el.dashActivityFeed = $('#dashActivityFeed');
el.dashTopUsers = $('#dashTopUsers');
el.dashMsgChart = $('#dashMsgChart');
el.dashActivityCount = $('#dashActivityCount');
el.dashTopUsersCount = $('#dashTopUsersCount');
el.adminActivityList = $('#adminActivityList');
el.umAvatar = $('#umAvatar');
el.umName = $('#umName');
el.umMeta = $('#umMeta');
el.umActivityTab = $('#umActivityTab');
el.umConversationsTab = $('#umConversationsTab');

const ST = { dashboard:'Dashboard', activity:'Activity', users:'Users', models:'Models', conversations:'Conversations', audit:'Audit Logs', system:'System' };
const SL = { dashboard:[loadQuickStats, loadDashActivity, loadTopUsers, loadMsgChart], activity:[loadFullActivity], users:[loadUsers], models:[loadModels], conversations:[loadConvs], audit:[loadAudit], system:[loadSystem] };

function nav(s) {
  $$('.admin-nav-item').forEach(i=>i.classList.remove('active'));
  const b = document.querySelector(`.admin-nav-item[data-section="${s}"]`);
  if(b)b.classList.add('active');
  $$('.admin-section-content').forEach(c=>c.style.display='none');
  const t = document.getElementById('section-'+s);
  if(t)t.style.display='';
  el.sectionTitle.textContent = ST[s]||s; S.section=s;
  (SL[s]||[]).forEach(f=>f());
}
window.nav = nav;
document.querySelectorAll('.admin-nav-item').forEach(i=>i.addEventListener('click',()=>nav(i.dataset.section)));
document.getElementById('adminLogoutBtn').addEventListener('click',async()=>{await api('/api/auth/logout',{method:'POST'});window.location.href='/';});

const esc = s => {const d=document.createElement('div');d.textContent=s;return d.innerHTML;};
const ago = iso => {if(!iso)return'—';const d=Date.now()-new Date(iso).getTime(),m=Math.floor(d/60000),h=Math.floor(d/3600000),dd=Math.floor(d/86400000);return m<1?'now':m<60?`${m}m`:h<24?`${h}h`:dd<7?`${dd}d`:new Date(iso).toLocaleDateString()};
const fmtSize = b => {if(!b)return'—';const u=['B','KB','MB','GB'];let i=0,s=b;while(s>=1024&&i<3){s/=1024;i++}return`${s.toFixed(i>0?1:0)} ${u[i]}`};
const fmtCost = v => `$${Number(v||0).toFixed(Number(v||0) < 0.01 ? 4 : 2)}`;
const evBadge = e => `<span class="event-badge ${e.replace(/_/g,'_')}">${e.replace(/_/g,' ')}</span>`;
const catBg = c => ({General:'rgba(59,130,246,0.1)',Code:'rgba(168,85,247,0.1)',Vision:'rgba(6,182,212,0.1)',Embedding:'rgba(34,197,94,0.1)',Math:'rgba(245,158,11,0.1)',Creative:'rgba(236,72,153,0.1)',Lightweight:'rgba(148,163,184,0.1)'}[c]||'var(--sidebar-hover)');
const catFg = c => ({General:'#3b82f6',Code:'#a855f7',Vision:'#06b6d4',Embedding:'#22c55e',Math:'#f59e0b',Creative:'#ec4899',Lightweight:'#94a3b8'}[c]||'var(--text-secondary)');

// ── DASHBOARD ──
async function loadQuickStats() {
  try {
    const r = await api('/api/admin/stats');
    if(!r.ok)return; const s=await r.json(); S.stats=s;
    const u=s.usage||{};
    el.quickStats.innerHTML = `
      <div class="admin-stat-card"><div class="stat-row"><div><div class="stat-val">${s.users}</div><div class="stat-lbl">Users</div></div><div class="stat-icon c1">👥</div></div><div class="stat-sub" style="background:rgba(34,197,94,0.08);color:#22c55e">${s.active_users} active · ${Math.round((s.active_users/Math.max(s.users,1))*100)}%</div></div>
      <div class="admin-stat-card"><div class="stat-row"><div><div class="stat-val">${s.conversations}</div><div class="stat-lbl">Conversations</div></div><div class="stat-icon c2">💬</div></div><div class="stat-sub" style="background:rgba(59,130,246,0.08);color:#3b82f6">${s.convs_today} today · ${s.convs_week} this week</div></div>
      <div class="admin-stat-card"><div class="stat-row"><div><div class="stat-val">${s.messages}</div><div class="stat-lbl">Messages</div></div><div class="stat-icon c3">📝</div></div><div class="stat-sub" style="background:rgba(168,85,247,0.08);color:#a855f7">${s.msgs_today} today · ${s.conversations>0?Math.round(s.messages/s.conversations):0} avg/chat</div></div>
      <div class="admin-stat-card"><div class="stat-row"><div><div class="stat-val">${(u.total_tokens||0).toLocaleString()}</div><div class="stat-lbl">Tokens</div></div><div class="stat-icon c6">T</div></div><div class="stat-sub" style="background:rgba(6,182,212,0.08);color:#06b6d4">${(u.output_tokens||0).toLocaleString()} output</div></div>
      <div class="admin-stat-card"><div class="stat-row"><div><div class="stat-val">${fmtCost(u.estimated_cost_usd)}</div><div class="stat-lbl">Cost</div></div><div class="stat-icon c5">$</div></div><div class="stat-sub" style="background:rgba(236,72,153,0.08);color:#ec4899">${u.truncated_responses||0} truncated</div></div>
      <div class="admin-stat-card"><div class="stat-row"><div><div class="stat-val">${s.max_response_tokens}</div><div class="stat-lbl">Max Tokens</div></div><div class="stat-icon c4">#</div></div><div class="stat-sub" style="background:rgba(245,158,11,0.08);color:#f59e0b">default ${s.default_max_tokens}</div></div>
      <div class="admin-stat-card"><div class="stat-row"><div><div class="stat-val">${s.admins||0}</div><div class="stat-lbl">Admins</div></div><div class="stat-icon c4">🛡</div></div><div class="stat-sub" style="background:rgba(245,158,11,0.08);color:#f59e0b">${Math.round((s.admins||0)/Math.max(s.users,1)*100)}% of users</div></div>
      <div class="admin-stat-card"><div class="stat-row"><div><div class="stat-val">${fmtSize(s.storage_bytes)}</div><div class="stat-lbl">Database</div></div><div class="stat-icon c5">💾</div></div><div class="stat-sub" style="background:rgba(236,72,153,0.08);color:#ec4899">SQLite</div></div>
      <div class="admin-stat-card"><div class="stat-row"><div><div class="stat-val">${s.users>0?Math.round(s.active_users/s.users*100):0}%</div><div class="stat-lbl">Engagement</div></div><div class="stat-icon c6">📈</div></div><div class="stat-sub" style="background:rgba(6,182,212,0.08);color:#06b6d4">${s.users-s.active_users} inactive users</div></div>
    `;
    el.navUsersCount.textContent=s.users; el.navConvsCount.textContent=s.conversations;
    el.usersCountBadge.textContent=s.users; el.convsCountBadge.textContent=s.conversations;
  }catch(e){}
}

async function loadDashActivity() {
  try {
    const r = await api('/api/admin/activity?limit=12');
    if(!r.ok)return; const d=await r.json();
    if(!d.activities||!d.activities.length){el.dashActivityFeed.innerHTML='<div class="admin-empty" style="padding:20px">No activity</div>';return;}
    el.dashActivityCount.textContent = d.activities.length+' events';
    el.dashActivityFeed.innerHTML = d.activities.map(a => {
      const dot = a.type==='message'?'message':'event';
      const detail = typeof a.detail==='object' ? (a.detail.role+': '+(a.detail.content||'').slice(0,80)) : (a.detail||'').slice(0,100);
      return `<div class="activity-item">
        <div class="ai-dot ${dot}"></div>
        <div class="ai-body">
          <div class="ai-header"><span class="ai-username">${esc(a.username)}</span> ${evBadge(a.event)}</div>
          <div class="ai-detail">${esc(detail)}</div>
        </div>
        <div class="ai-time">${ago(a.created)}</div>
      </div>`;
    }).join('');
  }catch(e){}
}

async function loadTopUsers() {
  try {
    const r = await api('/api/admin/users');
    if(!r.ok)return; const d=await r.json();
    const users = (d.users||[]).filter(u=>u.conv_count>0||u.last_active).sort((a,b)=>(b.conv_count||0)-(a.conv_count||0)).slice(0,5);
    if(!users.length){el.dashTopUsers.innerHTML='<div class="admin-empty" style="padding:20px">No active users</div>';return;}
    el.dashTopUsersCount.textContent = users.length+' users';
    const maxMsgs = Math.max(...users.map(u=>u.conv_count||0),1);
    el.dashTopUsers.innerHTML = users.map((u,i) => {
      const rank = i===0?'gold':i===1?'silver':i===2?'bronze':'';
      const pct = Math.round((u.conv_count||0)/maxMsgs*100);
      return `<div class="top-user-item" onclick="openUserModal(${u.id})">
        <div class="tu-rank ${rank}">#${i+1}</div>
        <div class="tu-avatar">${(u.username||'?')[0].toUpperCase()}</div>
        <div class="tu-name">${esc(u.username)}</div>
        <div class="tu-msgs">${u.conv_count} chats</div>
        <div class="tu-bar"><div class="fill" style="width:${pct}%"></div></div>
      </div>`;
    }).join('');
  }catch(e){}
}

async function loadMsgChart() {
  try {
    const r = await api('/api/admin/activity?limit=200');
    if(!r.ok)return; const d=await r.json();
    const msgs = (d.activities||[]).filter(a=>a.type==='message');
    const days = {};
    for(let i=6;i>=0;i--){const t=new Date(Date.now()-i*86400000);days[t.toLocaleDateString('en',{month:'short',day:'numeric'})]=0}
    msgs.forEach(m=>{const k=new Date(m.created).toLocaleDateString('en',{month:'short',day:'numeric'});if(k in days)days[k]++});
    const vals=Object.values(days), max=Math.max(...vals,1);
    el.dashMsgChart.innerHTML = Object.entries(days).map(([k,v])=>{
      const h=Math.max(Math.round(v/max*60),4);
      return `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px"><div class="bar" style="height:${h}px;width:100%"></div><span style="font-size:9px;color:var(--text-muted)">${k}</span></div>`;
    }).join('');
  }catch(e){}
}

// ── FULL ACTIVITY ──
async function loadFullActivity() {
  try {
    const r = await api('/api/admin/activity?limit=100');
    if(!r.ok)return; const d=await r.json();
    if(!d.activities||!d.activities.length){el.adminActivityList.innerHTML='<div class="admin-empty">No activity</div>';return;}
    el.activityTotalLabel.textContent = d.activities.length+' entries';
    el.adminActivityList.innerHTML = d.activities.map(a => {
      const dot = a.type==='message'?'message':'event';
      const detail = typeof a.detail==='object' ? `${a.detail.role}: ${(a.detail.content||'').slice(0,120)}` : (a.detail||'—').slice(0,120);
      return `<div class="activity-item">
        <div class="ai-dot ${dot}"></div>
        <div class="ai-body">
          <div class="ai-header"><span class="ai-username">${esc(a.username)}</span> ${evBadge(a.event)} ${a.ip ? `<span style="font-size:11px;color:var(--text-muted);font-family:var(--font-mono)">${esc(a.ip)}</span>`:''}</div>
          <div class="ai-detail">${esc(detail)}</div>
        </div>
        <div class="ai-time">${ago(a.created)}</div>
      </div>`;
    }).join('');
  }catch(e){}
}

// ── USERS ──
async function loadUsers() {
  try {
    const r = await api('/api/admin/users');
    if(!r.ok){el.userList.innerHTML='<tr><td colspan="8" class="admin-empty">Failed</td></tr>';return;}
    const d=await r.json();
    if(!d.users||!d.users.length){el.userList.innerHTML='<tr><td colspan="8" class="admin-empty"><div class="empty-icon">👥</div><div class="empty-text">No users</div></td></tr>';return;}
    el.userList.innerHTML = d.users.map(u => {
      const initial = (u.username||'?')[0].toUpperCase();
      const lastAgo = ago(u.last_active);
      const lastTitle = u.last_active ? new Date(u.last_active).toLocaleString() : '';
      return `<tr style="cursor:pointer" onclick="openUserModal(${u.id})">
        <td><span class="cell-name">${esc(u.username)}</span></td>
        <td><span class="cell-sm">${esc(u.email||'—')}</span></td>
        <td><span class="role-badge ${u.role}">${u.role==='admin'?'🛡':'👤'} ${u.role}</span></td>
        <td><span class="status-dot ${u.is_active?'active':'inactive'}">${u.is_active?'Active':'Disabled'}</span></td>
        <td><span class="cell-mono">${u.conv_count||0}</span></td>
        <td><span class="cell-sm" title="${lastTitle}">${lastAgo}</span></td>
        <td><span class="cell-sm" title="${new Date(u.created_at).toLocaleString()}">${ago(u.created_at)}</span></td>
        <td onclick="event.stopPropagation()">${u.id!==1?`
          <button class="action-btn ${u.is_active?'danger':'success'}" onclick="toggleUser(${u.id})" title="${u.is_active?'Disable':'Enable'}">${u.is_active?'⛔':'✅'}</button>
          <button class="action-btn danger" onclick="delUser(${u.id})" title="Delete">🗑</button>
        `:'<span class="cell-sm">—</span>'}</td>
      </tr>`;
    }).join('');
  }catch(e){el.userList.innerHTML='<tr><td colspan="8" class="admin-empty">Error</td></tr>';}
}
async function toggleUser(id){await api(`/api/admin/users/${id}/toggle`,{method:'PUT'});loadUsers();loadQuickStats();}
function delUser(id){if(confirm('Delete user and all data?'))api(`/api/admin/users/${id}`,{method:'DELETE'}).then(()=>{loadUsers();loadQuickStats();});}

// ── USER MODAL ──
async function openUserModal(id) {
  S.umUserId = id;
  el.userModal.style.display = '';
  el.umAvatar.textContent='?'; el.umName.textContent='Loading...'; el.umMeta.textContent='';
  el.umActivityTab.innerHTML='<div class="admin-empty">Loading...</div>'; el.umConversationsTab.innerHTML='<div class="admin-empty">Loading...</div>';
  switchUmTab('activity');
  try {
    const r = await api(`/api/admin/users/${id}`);
    if(!r.ok)return; const d=await r.json(); const u=d.user;
    el.umAvatar.textContent=(u.username||'?')[0].toUpperCase();
    el.umName.textContent=`${esc(u.username)} ${u.role==='admin'?'🛡':''}`;
    el.umMeta.textContent=`${esc(u.email)} · ${u.conv_count} conversations · ${u.msg_count||0} messages · Joined ${ago(u.created_at)} · Last active ${ago(u.last_active)}`;

    // Activity tab
    if(!d.activity||!d.activity.length){
      el.umActivityTab.innerHTML='<div class="admin-empty">No activity</div>';
    }else{
      el.umActivityTab.innerHTML = d.activity.map(l=> {
        const d2 = l.detail;
        const ds = typeof d2 === 'string' ? d2.slice(0,150) : (d2 ? JSON.stringify(d2).slice(0,150) : '—');
        return `<div class="activity-item">
          <div class="ai-dot event"></div>
          <div class="ai-body">
            <div class="ai-header">${evBadge(l.event)} ${l.ip?`<span style="font-size:11px;color:var(--text-muted);font-family:var(--font-mono)">${esc(l.ip)}</span>`:''}</div>
            <div class="ai-detail">${esc(ds)}</div>
          </div>
          <div class="ai-time">${ago(l.created)}</div>
        </div>`;
      }).join('');
    }

    // Conversations tab
    if(!d.conversations||!d.conversations.length){
      el.umConversationsTab.innerHTML='<div class="admin-empty">No conversations</div>';
    }else{
      el.umConversationsTab.innerHTML = `<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Title</th><th>Messages</th><th>Created</th><th>Updated</th></tr></thead><tbody>${
        d.conversations.map(c=>`<tr><td><span class="cell-name">${esc((c.title||'Untitled').slice(0,50))}</span></td><td><span class="cell-mono">${c.msg_count}</span></td><td><span class="cell-sm">${ago(c.created)}</span></td><td><span class="cell-sm">${ago(c.updated)}</span></td></tr>`).join('')
      }</tbody></table></div>`;
    }
  }catch(e){el.umName.textContent='Error loading user';}
}

function closeUserModal(){el.userModal.style.display='none';S.umUserId=null;}
window.openUserModal=openUserModal; window.closeUserModal=closeUserModal;

function switchUmTab(tab){
  $$('.user-modal-tab').forEach(t=>t.classList.toggle('active',t.dataset.umtab===tab));
  el.umActivityTab.style.display = tab==='activity'?'':'none';
  el.umConversationsTab.style.display = tab==='conversations'?'':'none';
}
document.querySelectorAll('.user-modal-tab').forEach(t=>t.addEventListener('click',()=>switchUmTab(t.dataset.umtab)));

// ── MODELS ──
let _modelsCache = [];
async function loadModels() {
  try {
    const [cr,sr] = await Promise.all([api('/api/models/catalog'),api('/api/admin/system')]);
    if(!cr.ok){el.modelList.innerHTML='<tr><td colspan="7" class="admin-empty">Failed</td></tr>';return;}
    const c=await cr.json(); S.catalogModels=c.models||[];
    const installed = S.catalogModels.filter(m=>m.installed); S.installedModels=installed;
    S.modelDetails = sr.ok ? (await sr.json()).model_details||[] : [];
    el.navModelsCount.textContent=installed.length; el.modelsCountBadge.textContent=installed.length;
    _modelsCache = installed;
    renderModels(installed);
  }catch(e){el.modelList.innerHTML='<tr><td colspan="7" class="admin-empty">Error</td></tr>';}
}
function renderModels(list) {
  if(!list.length){el.modelList.innerHTML='<tr><td colspan="7" class="admin-empty"><div class="empty-icon">🤖</div><div class="empty-text">No models</div><div class="empty-sub">Pull a model above</div></td></tr>';return;}
  el.modelList.innerHTML = list.map(m => {
    const dt=S.modelDetails.find(d=>d.name===m.name);
    return `<tr><td><span class="cell-name">${esc(m.name)}</span></td><td><span class="role-badge" style="background:${catBg(m.category)};color:${catFg(m.category)}">${m.category}</span></td><td><span class="cell-sm">${esc(m.description)}</span></td><td><span class="size-badge">${dt?fmtSize(dt.size):'—'}</span></td><td><span class="cell-sm">${dt?ago(dt.modified):'—'}</span></td><td><span style="font-family:var(--font-mono);font-size:11px;color:var(--text-muted)">${dt?dt.digest:'—'}</span></td><td><button class="action-btn danger" onclick="delModel('${m.name.replace(/'/g,"\\'")}')">🗑</button></td></tr>`;
  }).join('');
}
el.modelFilter && el.modelFilter.addEventListener('input', () => {
  const q = (el.modelFilter.value||'').toLowerCase();
  renderModels(_modelsCache.filter(m=>m.name.toLowerCase().includes(q)));
});
// Catalog suggestions for model pull input
el.modelInput.addEventListener('input', () => {
  const q = el.modelInput.value.trim().toLowerCase();
  const sg = el.modelSuggest;
  if (!S.catalogModels.length || q.length < 1) { sg.style.display='none'; return; }
  const matches = S.catalogModels.filter(m => !m.installed && m.name.toLowerCase().includes(q)).slice(0, 8);
  if (!matches.length) { sg.style.display='none'; return; }
  sg.innerHTML = matches.map(m =>
    `<div class="cs-item" data-name="${esc(m.name)}">
      <span class="cs-dot" style="background:${catFg(m.category)}"></span>
      <span>${esc(m.name)}</span>
      <span class="cs-cat">${m.category}</span>
    </div>`
  ).join('');
  sg.style.display = '';
  sg.querySelectorAll('.cs-item').forEach(item => item.addEventListener('click', () => {
    el.modelInput.value = item.dataset.name;
    sg.style.display='none';
    el.modelPullBtn.click();
  }));
});
document.addEventListener('click', e => { if (!e.target.closest('#adminModelInput') && !e.target.closest('#adminModelSuggest')) el.modelSuggest.style.display='none'; });
async function delModel(n){if(confirm(`Delete "${n}"?`)){await api(`/api/admin/models/${encodeURIComponent(n)}`,{method:'DELETE'});loadModels();}}
el.modelPullBtn.addEventListener('click',pullModel);
el.modelInput.addEventListener('keydown',e=>{if(e.key==='Enter')pullModel();});
async function pullModel() {
  const n=el.modelInput.value.trim(); if(!n)return;
  el.modelPullBtn.disabled=true; el.modelStatus.textContent=`⏳ Pulling ${n}...`; el.modelStatus.className='model-pull-status pulling';
  el.pullProgressBar.style.display=''; el.pullProgressFill.style.width='0%';
  try {
    const r=await api('/api/models/pull',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n})});
    if(!r.ok){el.modelStatus.textContent=`❌ ${r.status}`;el.modelStatus.className='model-pull-status error';el.pullProgressBar.style.display='none';el.modelPullBtn.disabled=false;return;}
    const rd=r.body.getReader(),dec=new TextDecoder();let buf='',last=0;
    while(true){const{done,value}=await rd.read();if(done)break;buf+=dec.decode(value,{stream:true});
      for(const l of buf.split('\n')){const t=l.trim();if(!t.startsWith('data: '))continue;const d=t.slice(6).trim();if(d==='[DONE]')continue;
        try{const p=JSON.parse(d);if(p.error){el.modelStatus.textContent=`❌ ${p.error}`;el.modelStatus.className='model-pull-status error';el.pullProgressBar.style.display='none';el.modelPullBtn.disabled=false;return;}
          el.modelStatus.textContent=p.status||'';if(p.progress&&p.progress.total){const pct=Math.min(Math.round(p.progress.completed/p.progress.total*100),100);if(pct!==last){el.pullProgressFill.style.width=pct+'%';last=pct;}}
          if(p.done){el.modelStatus.textContent=`✅ ${n} installed!`;el.modelStatus.className='model-pull-status success';el.pullProgressFill.style.width='100%';setTimeout(()=>{el.pullProgressBar.style.display='none'},1500);el.modelInput.value='';loadModels();}
        }catch(e){}
      }buf='';
    }
  }catch(e){el.modelStatus.textContent=`❌ ${e.message}`;el.modelStatus.className='model-pull-status error';el.pullProgressBar.style.display='none';}
  el.modelPullBtn.disabled=false;
}

// ── CONVERSATIONS ──
let _convsCache = [];
async function loadConvs() {
  try {
    const r=await api('/api/admin/conversations?limit=100');
    if(!r.ok){el.convList.innerHTML='<tr><td colspan="6" class="admin-empty">Failed</td></tr>';return;}
    const d=await r.json();
    if(!d.conversations||!d.conversations.length){el.convList.innerHTML='<tr><td colspan="6" class="admin-empty"><div class="empty-icon">💬</div><div class="empty-text">No conversations</div></td></tr>';return;}
    el.convsCountBadge.textContent = d.total||d.conversations.length;
    _convsCache = d.conversations;
    renderConvs(d.conversations);
  }catch(e){el.convList.innerHTML='<tr><td colspan="6" class="admin-empty">Error</td></tr>';}
}
function renderConvs(list) {
  if(!list.length){el.convList.innerHTML='<tr><td colspan="6" class="admin-empty"><div class="empty-icon">💬</div><div class="empty-text">No matching conversations</div></td></tr>';return;}
  el.convList.innerHTML = list.map(c=>
    `<tr><td><span class="cell-name">${esc((c.title||'Untitled').slice(0,50))}</span></td><td><span class="cell-mono">${esc(c.username)}</span></td><td><span class="cell-mono">${c.msg_count}</span></td><td><div class="conv-preview" title="${esc(c.last_message||'')}">${esc((c.last_message||'—').slice(0,100))}</div></td><td><span class="cell-sm" title="${new Date(c.created).toLocaleString()}">${ago(c.created)}</span></td><td><span class="cell-sm" title="${new Date(c.updated).toLocaleString()}">${ago(c.updated)}</span></td></tr>`
  ).join('');
}
el.convSearch && el.convSearch.addEventListener('input', () => {
  const q = (el.convSearch.value||'').toLowerCase();
  renderConvs(_convsCache.filter(c=>(c.title||'').toLowerCase().includes(q)));
});
el.convRefreshBtn && el.convRefreshBtn.addEventListener('click', loadConvs);

// ── AUDIT ──
let _auditCache = [];
async function loadAudit() {
  try {
    const r=await api('/api/admin/audit?limit=200');
    if(!r.ok){el.auditList.innerHTML='<tr><td colspan="5" class="admin-empty">Failed</td></tr>';return;}
    const d=await r.json();
    if(!d.logs||!d.logs.length){el.auditList.innerHTML='<tr><td colspan="5" class="admin-empty"><div class="empty-icon">🔍</div><div class="empty-text">No logs</div></td></tr>';return;}
    _auditCache = d.logs;
    el.auditCountBadge.textContent = d.logs.length;
    renderAudit(d.logs);
  }catch(e){el.auditList.innerHTML='<tr><td colspan="5" class="admin-empty">Error</td></tr>';}
}
function renderAudit(list) {
  if(!list.length){el.auditList.innerHTML='<tr><td colspan="5" class="admin-empty"><div class="empty-icon">🔍</div><div class="empty-text">No matching entries</div></td></tr>';return;}
  el.auditList.innerHTML = list.map(l=> {
    const d = l.detail;
    const ds = typeof d === 'string' ? d.slice(0,120) : (d ? JSON.stringify(d).slice(0,120) : '—');
    return `<tr><td>${evBadge(l.event)}</td><td><span class="cell-sm">${esc(ds)}</span></td><td><span class="cell-mono">${esc(l.username||'—')}</span></td><td><span style="font-family:var(--font-mono);font-size:11px;color:var(--text-muted)">${esc(l.ip||'—')}</span></td><td><span class="cell-sm" title="${new Date(l.created).toLocaleString()}">${ago(l.created)}</span></td></tr>`;
  }).join('');
}
function filterAudit() {
  const ev = (el.auditEventFilter.value||'').toLowerCase();
  const usr = (el.auditUserSearch.value||'').toLowerCase();
  renderAudit(_auditCache.filter(l => {
    if(ev && l.event !== ev) return false;
    if(usr && !(l.username||'').toLowerCase().includes(usr)) return false;
    return true;
  }));
}
el.auditEventFilter && el.auditEventFilter.addEventListener('change', filterAudit);
el.auditUserSearch && el.auditUserSearch.addEventListener('input', filterAudit);

// ── SYSTEM ──
async function loadSystem() {
  try {
    const r=await api('/api/admin/system');
    if(!r.ok){el.sysInfo.innerHTML='<div class="admin-empty">Failed</div>';return;}
    const s=await r.json();
    const u=s.usage||{}, ai=s.ai_log||{};
    const rp=s.ram_percent||0, rc=rp>80?'err':rp>60?'warn':'ok';
    const dp=s.disk_total?Math.round(s.disk_used/s.disk_total*100):0, dc=dp>85?'err':dp>70?'warn':'ok';
    el.sysInfo.innerHTML = `
      <div class="admin-sys-card"><h3><span class="sys-card-icon">🦙</span> Ollama</h3><div class="admin-sys-row"><span class="sys-label">Status</span><span class="sys-value ${s.ollama_ok?'ok':'err'}">${s.ollama_ok?'● Connected':'● Disconnected'}</span></div><div class="admin-sys-row"><span class="sys-label">Version</span><span class="sys-value">${s.ollama_version||'N/A'}</span></div><div class="admin-sys-row"><span class="sys-label">Models</span><span class="sys-value">${s.ollama_models}</span></div><div class="admin-sys-row"><span class="sys-label">API</span><span class="sys-value" style="font-size:12px;font-family:var(--font-mono)">127.0.0.1:11434</span></div></div>
      <div class="admin-sys-card"><h3><span class="sys-card-icon">🖥</span> Resources</h3><div class="admin-sys-row"><span class="sys-label">RAM</span><span class="sys-value ${rc}">${fmtSize(s.ram_total-s.ram_available)} / ${fmtSize(s.ram_total)} (${rp}%)</span></div><div class="admin-sys-progress"><div class="fill" style="width:${rp}%;background:${rc==='err'?'#ef4444':rc==='warn'?'#f59e0b':'#22c55e'}"></div></div><div class="admin-sys-row" style="margin-top:6px"><span class="sys-label">Disk</span><span class="sys-value ${dc}">${fmtSize(s.disk_used)} / ${fmtSize(s.disk_total)} (${dp}%)</span></div><div class="admin-sys-progress"><div class="fill" style="width:${dp}%;background:${dc==='err'?'#ef4444':dc==='warn'?'#f59e0b':'#22c55e'}"></div></div><div class="admin-sys-row" style="margin-top:6px"><span class="sys-label">Free</span><span class="sys-value ${s.disk_free<1073741824?'err':'ok'}">${fmtSize(s.disk_free)}</span></div></div>
      <div class="admin-sys-card"><h3><span class="sys-card-icon">⚙</span> Application</h3><div class="admin-sys-row"><span class="sys-label">Python</span><span class="sys-value">${s.python_version}</span></div><div class="admin-sys-row"><span class="sys-label">Platform</span><span class="sys-value">${s.platform}</span></div><div class="admin-sys-row"><span class="sys-label">Server</span><span class="sys-value">Uvicorn :8000</span></div><div class="admin-sys-row"><span class="sys-label">DB Size</span><span class="sys-value">${fmtSize(s.db_size_bytes)}</span></div></div>
      <div class="admin-sys-card"><h3><span class="sys-card-icon">🔋</span> Process</h3><div class="admin-sys-row"><span class="sys-label">Memory (RSS)</span><span class="sys-value">${s.process_memory_mb||'N/A'} MB</span></div><div class="admin-sys-row"><span class="sys-label">CPU</span><span class="sys-value">${s.process_cpu_percent||'N/A'}%</span></div><div class="admin-sys-row"><span class="sys-label">Uptime</span><span class="sys-value">${s.uptime||'N/A'}</span></div></div>
      <div class="admin-sys-card full"><h3><span class="sys-card-icon">AI</span> AI Runtime</h3><div class="admin-sys-row"><span class="sys-label">Default / hard max tokens</span><span class="sys-value">${s.default_max_tokens} / ${s.max_response_tokens}</span></div><div class="admin-sys-row"><span class="sys-label">Context budget</span><span class="sys-value">${s.max_context_tokens}</span></div><div class="admin-sys-row"><span class="sys-label">Total tokens</span><span class="sys-value">${(u.total_tokens||0).toLocaleString()}</span></div><div class="admin-sys-row"><span class="sys-label">Estimated cost</span><span class="sys-value">${fmtCost(u.estimated_cost_usd)}</span></div><div class="admin-sys-row"><span class="sys-label">AI.log</span><span class="sys-value" title="${esc(ai.path||'')}">${ai.enabled ? fmtSize(ai.size_bytes||0) : 'Disabled'}</span></div></div>
    `;
  }catch(e){el.sysInfo.innerHTML='<div class="admin-empty">Error</div>';}
  // Load tunnel status
  try {
    const tr = await api('/api/admin/tunnel');
    if(tr.ok) {
      const ts = await tr.json();
      const s = document.getElementById('tunnelStatus');
      const u = document.getElementById('tunnelUrl');
      const sb = document.getElementById('tunnelStartBtn');
      const stb = document.getElementById('tunnelStopBtn');
      if(ts.running) {
        s.textContent = '● Running';
        s.style.color = '#22c55e';
        u.textContent = ts.url || 'Connecting...';
        sb.disabled = true; stb.disabled = false;
      } else {
        s.textContent = 'Not running';
        s.style.color = 'var(--text-muted)';
        u.textContent = '';
        sb.disabled = false; stb.disabled = true;
      }
    }
  } catch(e) {}
}
document.addEventListener('click', e => {
  const sb = document.getElementById('tunnelStartBtn');
  const stb = document.getElementById('tunnelStopBtn');
  if(e.target.id === 'tunnelStartBtn') {
    sb.disabled = true; stb.disabled = true;
    const s = document.getElementById('tunnelStatus');
    const u = document.getElementById('tunnelUrl');
    s.textContent = '⏳ Starting...'; s.style.color = 'var(--accent)';
    api('/api/admin/tunnel/start', {method:'POST'}).then(r=>r.json()).then(d=>{
      s.textContent = '● Running'; s.style.color = '#22c55e';
      u.textContent = d.url || 'Connecting...';
      sb.disabled = true; stb.disabled = false;
    }).catch(()=>{
      s.textContent = 'Failed'; s.style.color = '#ef4444';
      sb.disabled = false; stb.disabled = true;
    });
  }
  if(e.target.id === 'tunnelStopBtn') {
    sb.disabled = true; stb.disabled = true;
    api('/api/admin/tunnel/stop', {method:'POST'}).then(()=>{
      document.getElementById('tunnelStatus').textContent = 'Stopped';
      document.getElementById('tunnelUrl').textContent = '';
      sb.disabled = false; stb.disabled = true;
    });
  }
});

// ── INIT ──
async function init() {
  const t=localStorage.getItem('ollama_token'); if(!t){window.location.href='/';return;}
  const r=await api('/api/auth/me'); if(!r.ok){window.location.href='/';return;}
  const u=await r.json(); if(u.role!=='admin'){window.location.href='/chat';return;}
  document.getElementById('adminSidebarAvatar').textContent=(u.username||'A')[0].toUpperCase();
  el.sidebarName.textContent=u.username; el.topbarName.textContent=u.username;
  nav('dashboard');
}
init();
