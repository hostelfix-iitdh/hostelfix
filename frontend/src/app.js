const API = "/api/v1";
const PAGE_SIZE = 9;
const state = {
  page: "login", userId: Number(localStorage.getItem("hf.userId") || 0), demoUsers: [],
  loggedIn: localStorage.getItem("hf.loggedIn") === "true", user: null,
  locations: [], problemTypes: [], hostels: [], categories: [], issues: [],
  currentIssue: null, editingIssue: null, myIssueIds: new Set(), listPage: 1, myPage: 1, search: "", filters: {status:"",hostel:"",floor:"",wing:"",area:"",category:"",problem:""},
  form: {hostelId:"",floorId:"",wingId:"",locationId:"",categoryId:"",problemTypeId:""}, pendingIssue: null, modal: null, notifications: []
};
const $ = (selector, root=document) => root.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const human = (value) => String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());
const date = (value, withTime=false) => { if(!value) return "—"; const d=new Date(value); return Number.isNaN(d.getTime())?"—":new Intl.DateTimeFormat("en-IN",withTime?{dateStyle:"medium",timeStyle:"short"}:{dateStyle:"medium"}).format(d); };
const initials = (name) => String(name || "HF").split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join("").toUpperCase();
const isHousekeeping = (category) => String(category || "").toLowerCase().includes("housekeeping");
const statusChip = (status) => `<span class="status status-${esc(String(status||"neutral").toLowerCase())}">${esc(human(status))}</span>`;
const locationLabel = (id) => { const l=state.locations.find(x=>Number(x.id)===Number(id)); return l ? `${l.hostel_name} · Floor ${l.floor_number} · Wing ${l.wing_name} · ${human(l.area_type)}` : `Location #${esc(id)}`; };
const problemLabel = (id) => { const p=state.problemTypes.find(x=>Number(x.id)===Number(id)); return p ? `${p.name} · ${p.category_name}` : `Problem type #${esc(id)}`; };
const selectedRole = () => state.user?.role || (state.userId===45?"administrator":state.userId>=41?"staff":"student");
const isStaff = () => ["staff","administrator"].includes(selectedRole());
const navItems = () => selectedRole()==="administrator" ? [{id:"staff",label:"Staff Dashboard"},{id:"admin",label:"Admin Dashboard"},{id:"community",label:"Community Issues"},{id:"profile",label:"Profile"}] : isStaff() ? [{id:"staff",label:"Staff Dashboard"},{id:"community",label:"Community Issues"},{id:"profile",label:"Profile"}] : [{id:"dashboard",label:"Dashboard"},{id:"report",label:"Report an Issue"},{id:"community",label:"Community Issues"},{id:"my-reports",label:"My Reports"},{id:"profile",label:"Profile"}];

async function api(path, options={}) {
  const headers = {Accept:"application/json", ...(options.headers||{})};
  if (options.body && !headers["Content-Type"]) headers["Content-Type"]="application/json";
  if (options.auth !== false) headers["X-User-Id"] = String(state.userId);
  const response = await fetch(`${API}${path}`, {...options, headers});
  if (response.status===204) return null;
  let body={}; try { body=await response.json(); } catch {}
  if(!response.ok){const detail=body?.error?.message || body?.detail || body?.message || `Request failed (${response.status})`;throw new Error(typeof detail==="string"?detail:"The request could not be completed.");}
  return body;
}
function toast(message, type="") {
  const region=$("#toast-region"); const node=document.createElement("div"); node.className=`toast ${type}`; node.textContent=message; region.appendChild(node); setTimeout(()=>node.remove(),4200);
}
function setPage(page) { state.page=page; state.modal=null; render(); if(page==="dashboard") loadDashboard(); if(page==="report") initReportForm(); if(page==="community") loadCommunity(); if(page==="my-reports") loadMyReports(); if(page==="profile") loadProfile(); if(page==="staff") loadStaffQueue(); if(page==="admin") loadAdmin(); }
function header(active) {
  const items=navItems();
  return `<header class="topbar"><a class="brand" href="#dashboard" data-page="${isStaff()?"staff":"dashboard"}">HostelFix</a>
    <button class="icon-button mobile-menu" data-action="toggle-menu" aria-label="Toggle navigation">☰</button>
    <nav class="main-nav" id="main-nav" aria-label="Main navigation">${items.map(n=>`<a href="#${n.id}" data-page="${n.id}" class="nav-link ${active===n.id?"active":""}">${esc(n.label)}</a>`).join("")}</nav>
    <div class="topbar-right">${!isStaff()?`<button class="icon-button" data-action="notifications" aria-label="Notifications" title="Notifications">♧${state.notifications.some(n=>!n.is_read)?'<span class="unread-dot"></span>':''}</button>`:""}<span class="user-name">${esc(state.user?.name || `Demo user #${state.userId}`)}</span><button class="icon-button" data-page="profile" aria-label="Profile" title="Profile"><span style="font-size:12px;font-weight:800">${esc(initials(state.user?.name || "HF"))}</span></button></div>
  </header>`;
}
function pageFrame(active, content) { return `${header(active)}<main class="page-main">${content}</main><footer class="footer"><span>HostelFix · IIT Dharwad</span><span>Development demo · Synthetic data only · Never share personal information in public reports</span></footer>${state.modal?renderModal():""}`; }
function loginView() {
  const options = state.demoUsers;
  const selectedUser = options.find(user => Number(user.id) === Number(state.userId)) || options.find(user => user.role === "student") || options[0];
  if (selectedUser && Number(selectedUser.id) !== Number(state.userId)) state.userId = Number(selectedUser.id);
  return `<div class="login-page"><header class="login-header"><a class="brand" href="#">HostelFix</a><span class="user-name">IIT Dharwad</span></header><main class="login-main"><section class="login-card" aria-labelledby="login-title"><div><p class="eyebrow">IIT DHARWAD · HOSTEL SERVICES</p><h1 id="login-title">Sign in</h1></div><p class="intro">Use your <strong>iitdh.ac.in</strong> account to report and track hostel issues.</p>
    <form id="login-form" class="stack"><div class="field"><label for="login-email">College email</label><input class="input" id="login-email" type="email" required placeholder="you@iitdh.ac.in" value="${esc(selectedUser?.email || "") }"></div><div class="field"><label for="login-password">Password</label><input class="input" id="login-password" type="password" required placeholder="Enter your password" value="HostelFix-Demo-2026!"></div><div class="row spread"><span></span><a href="#reset" data-action="reset-password" class="text-link">Forgot password?</a></div><button class="btn" type="submit">Sign in</button></form>
    <div class="or-divider">or</div><button class="btn btn-google" data-action="google-signin" type="button"><span style="font-weight:800">G</span> Continue with Google</button>
    <div class="login-footer">New to HostelFix? <a href="#register" data-action="register">Create account</a><br><a href="#staff-login" data-action="staff-login">Staff sign in</a> &nbsp;·&nbsp; <a href="#admin-login" data-action="admin-login">Administrator sign in</a></div>
    <div class="demo-panel"><label for="demo-user">Development demo identity</label><select class="select" id="demo-user">${options.map(user=>`<option value="${user.id}" ${Number(user.id)===Number(state.userId)?"selected":""}>${esc(user.name)} · ${esc(user.role)} (${esc(user.email)})</option>`).join("")}</select><p class="small" style="margin:8px 0 0;color:#1e3a8a;line-height:1.5">The current backend uses a development identity header, not production authentication. Choose a seeded demo role to explore role-specific screens.</p></div>
    </section></main></div>${state.modal?renderModal():""}`;
}
function authPlaceholderView(kind) {
  const isSignup = kind === "signup";
  const isGoogle = kind === "google-signin";
  const title = isSignup ? "Create your account" : isGoogle ? "Continue with Google" : "Reset your password";
  const description = isSignup
    ? "Student registration is planned for the next milestone. These fields are a preview only and will not create an account."
    : isGoogle
      ? "Google authentication is planned for the next milestone. No Google account is connected and this page will not sign you in."
      : "Password reset is planned for the next milestone. This preview will not send an email or change a password.";
  return `<div class="login-page"><header class="login-header"><a class="brand" href="#" data-action="back-to-login">HostelFix</a><span class="user-name">IIT Dharwad</span></header><main class="login-main"><section class="login-card" aria-labelledby="auth-placeholder-title"><p class="eyebrow">NEXT MILESTONE · PREVIEW</p><h1 id="auth-placeholder-title">${title}</h1><p class="intro">${description}</p>
    ${isSignup ? `<div class="stack" aria-label="Registration preview"><div class="field"><label>Full name</label><input class="input" placeholder="Your full name" disabled></div><div class="field"><label>College email</label><input class="input" type="email" placeholder="you@iitdh.ac.in" disabled></div><div class="field"><label>Password</label><input class="input" type="password" placeholder="Create a password" disabled></div><button class="btn" type="button" disabled>Registration coming next milestone</button></div>` : isGoogle ? `<div class="google-preview"><div class="google-preview-mark">G</div><strong>Google account selection</strong><p class="small muted">The real Google account chooser will be integrated in a future milestone.</p><button class="btn btn-secondary" type="button" disabled>Google sign-in unavailable</button></div>` : `<div class="stack"><div class="field"><label>College email</label><input class="input" type="email" placeholder="you@iitdh.ac.in" disabled></div><button class="btn" type="button" disabled>Password reset coming next milestone</button></div>`}
    <div class="login-footer"><a href="#login" data-action="back-to-login">← Back to sign in</a></div></section></main></div>`;
}

function render() {
  const app=$("#app");
  if(["signup","google-signin","reset-password"].includes(state.page)) { app.innerHTML=authPlaceholderView(state.page); return; }
  if(!state.loggedIn || state.page==="login") { app.innerHTML=loginView(); return; }
  let content="";
  if(state.page==="dashboard") content=dashboardView();
  else if(state.page==="report") content=reportView();
  else if(state.page==="community") content=communityView();
  else if(state.page==="issue") content=issueView();
  else if(state.page==="my-reports") content=myReportsView();
  else if(state.page==="profile") content=profileView();
  else if(state.page==="staff") content=staffView();
  else if(state.page==="admin") content=adminView();
  else if(state.page==="notifications") content=notificationsView();
  else content=dashboardView();
  app.innerHTML=pageFrame(state.page,content);
}
function canEditOrDelete(issue) {
  return !isStaff() && state.myIssueIds.has(Number(issue.id)) && issue.status === "submitted";
}

function issueRow(issue, showActions=true) {
  const ownerActions = canEditOrDelete(issue)
    ? `<button class="btn btn-secondary btn-small" data-action="edit-issue" data-id="${issue.id}">Edit</button><button class="btn btn-danger btn-small" data-action="delete-issue" data-id="${issue.id}">Delete</button>`
    : "";
  return `<div class="issue-row"><div class="issue-symbol">${isHousekeeping(problemLabel(issue.problem_type_id))?"✦":"⌁"}</div><div class="issue-main"><div class="row spread wrap"><a class="issue-title" href="#issue-${issue.id}" data-action="open-issue" data-id="${issue.id}">HF-${String(issue.id).padStart(4,"0")} · ${esc(issue.title)}</a>${statusChip(issue.status)}</div><div class="issue-meta">${esc(locationLabel(issue.location_id))} · ${esc(problemLabel(issue.problem_type_id))}<br>Reported ${esc(date(issue.created_at,true))}</div>${showActions?`<div class="issue-actions"><button class="btn btn-secondary btn-small" data-action="open-issue" data-id="${issue.id}">View details</button>${ownerActions}</div>`:""}</div></div>`;
}

function dashboardView() {
  return `<div class="page-heading"><div><p class="eyebrow">YOUR HOSTEL AT A GLANCE</p><h1 id="welcome-title">Good morning${state.user?.name?`, ${esc(state.user.name.split(" ")[0])}`:""}</h1><p>Stay up to date with maintenance and housekeeping across your hostel.</p></div><button class="btn" data-page="report">＋ Report an issue</button></div>
  <div class="grid grid-4" id="dashboard-metrics"><div class="card metric"><div class="metric-label">My reports</div><div class="metric-value">—</div><div class="metric-foot">All submitted issues</div></div><div class="card metric"><div class="metric-label">In progress</div><div class="metric-value">—</div><div class="metric-foot">Work is underway</div></div><div class="card metric"><div class="metric-label">Awaiting response</div><div class="metric-value">—</div><div class="metric-foot">Submitted or acknowledged</div></div><div class="card metric"><div class="metric-label">Community reports</div><div class="metric-value">—</div><div class="metric-foot">Publicly visible issues</div></div></div>
  <div class="grid grid-2" style="margin-top:22px;grid-template-columns:minmax(0,1.55fr) minmax(280px,1fr)"><section class="card card-pad"><div class="section-head"><div><h2>Recent reports</h2><p>Your latest submissions and their status.</p></div><a class="text-link" href="#my-reports" data-page="my-reports">View all</a></div><div id="recent-issues"><div class="empty-state"><span class="spinner"></span><p>Loading your reports…</p></div></div></section>
  <aside class="stack"><section class="card card-pad"><div class="section-head"><div><h2>Quick actions</h2><p>Get the help you need.</p></div></div><div class="stack"><button class="btn" data-page="report">＋ Report an issue</button><button class="btn btn-secondary" data-page="community">Browse community issues</button><button class="btn btn-secondary" data-page="my-reports">Track my reports</button></div></section><section class="card card-pad"><h2 class="card-title">How HostelFix works</h2><p class="card-subtitle" style="line-height:1.7">Describe the problem, select its exact location, and submit. You can follow status updates and confirm whether a reported fix has worked.</p><div class="divider"></div><div class="row"><span class="metric-icon">✓</span><div><strong style="font-size:13px">Track progress</strong><div class="small muted" style="margin-top:4px">Follow the complaint timeline.</div></div></div></section></aside></div>`;
}
function reportView() {
  return `<div class="page-heading"><div><p class="eyebrow">HELP US FIX IT</p><h1>Report an Issue</h1><p>Tell us what happened and where. Please avoid including personal or sensitive information.</p></div></div>
  <div class="grid" style="grid-template-columns:minmax(0,1.4fr) minmax(290px,.8fr);align-items:start"><section class="card card-pad"><div class="section-head"><div><h2>Describe the issue</h2><p>SmartReport can help organise your description into an editable draft.</p></div></div>
  <div class="field"><label for="smart-description">SmartReport</label><textarea class="textarea" id="smart-description" placeholder="Example: The tap in the fourth-floor bathroom of Hostel 1, Wing B has been leaking since yesterday."></textarea><div class="row spread wrap"><span class="hint">AI suggestions are optional. Review every field before submitting.</span><button class="btn btn-secondary btn-small" type="button" data-action="smart-draft">Draft with SmartReport</button></div></div><div id="smart-message" style="margin-top:12px"></div><div class="divider"></div>
  <form id="issue-form" class="stack"><div class="form-grid"><div class="field"><label for="hostel-select">Hostel <span class="subtle">*</span></label><select class="select" id="hostel-select" name="hostel" required><option value="">Loading hostels…</option></select></div><div class="field"><label for="floor-select">Floor <span class="subtle">*</span></label><select class="select" id="floor-select" name="floor" required disabled><option value="">Select hostel first</option></select></div><div class="field"><label for="wing-select">Wing <span class="subtle">*</span></label><select class="select" id="wing-select" name="wing" required disabled><option value="">Select floor first</option></select></div><div class="field"><label for="area-select">Area <span class="subtle">*</span></label><select class="select" id="area-select" name="location" required disabled><option value="">Select wing first</option></select></div><div class="field hide" id="room-field"><label for="room-label">Room label</label><input class="input" id="room-label" maxlength="80" placeholder="e.g. 412"><span class="hint">Only needed when reporting an individual room.</span></div><div class="field hide" id="asset-field"><label for="asset-select">Asset / equipment</label><select class="select" id="asset-select"><option value="">No specific asset</option></select></div><div class="field"><label for="category-select">Category <span class="subtle">*</span></label><select class="select" id="category-select" required><option value="">Loading categories…</option></select></div><div class="field"><label for="problem-select">Problem type <span class="subtle">*</span></label><select class="select" id="problem-select" required disabled><option value="">Select category first</option></select></div><div class="field hide" id="service-date-field"><label for="service-date">Service date</label><input class="input" id="service-date" type="date"><span class="hint">For housekeeping reports, if relevant.</span></div><div class="field full"><label for="issue-title">Short title <span class="subtle">*</span></label><input class="input" id="issue-title" required minlength="5" maxlength="180" placeholder="e.g. Leaking tap in bathroom"></div><div class="field full"><label for="issue-description">Description <span class="subtle">*</span></label><textarea class="textarea" id="issue-description" required minlength="10" maxlength="5000" placeholder="Describe the problem, when you noticed it, and how it affects the area."></textarea><span class="hint">10–5,000 characters. Do not include names, phone numbers or other private details.</span></div></div>
  <label class="checkbox-row"><input id="issue-public" type="checkbox" checked><span>Show this report in Community Issues. Your identity will not be displayed publicly.</span></label><div class="row spread wrap"><span class="small muted">Fields marked * are required.</span><button class="btn" type="submit">Review and submit →</button></div></form></section>
  <aside class="stack"><section class="card card-pad"><h2 class="card-title">Before you submit</h2><div class="stack" style="margin-top:16px;gap:14px"><div class="row" style="align-items:flex-start"><span class="metric-icon">⌖</span><div><strong style="font-size:13px">Choose the exact location</strong><p class="card-subtitle">Select hostel, floor, wing and area so the right team can find the issue.</p></div></div><div class="row" style="align-items:flex-start"><span class="metric-icon">✎</span><div><strong style="font-size:13px">Be specific</strong><p class="card-subtitle">A clear description helps staff understand what needs attention.</p></div></div><div class="row" style="align-items:flex-start"><span class="metric-icon">◷</span><div><strong style="font-size:13px">Follow the timeline</strong><p class="card-subtitle">After submitting, track status changes from My Reports.</p></div></div></div></section><section class="alert warning"><strong>SmartReport status</strong><br>The AI provider is not configured in this development build. The button can prepare an editable draft and suggest a category/problem for common symptoms; it does not submit anything automatically.</section></aside></div>`;
}
function communityView() {
  return `<div class="page-heading"><div><p class="eyebrow">PUBLIC-SAFE TRACKER</p><h1>Community Issues</h1><p>Browse reports shared by the community. Reporter identities and private staff notes are not shown.</p></div><button class="btn" data-page="report">＋ Report an issue</button></div>
  <section class="card card-pad"><div class="list-toolbar"><div class="search-wrap"><span class="search-icon">⌕</span><input class="input" id="community-search" type="search" placeholder="Search issues…" value="${esc(state.search)}"></div><select class="select" id="filter-status" aria-label="Status"><option value="">All statuses</option>${["submitted","acknowledged","in_progress","resolved","closed","rejected","reopened"].map(x=>`<option value="${x}" ${state.filters.status===x?"selected":""}>${human(x)}</option>`).join("")}</select><select class="select" id="filter-hostel" aria-label="Hostel"><option value="">All hostels</option>${state.hostels.map(h=>`<option value="${h.id}" ${state.filters.hostel==h.id?"selected":""}>${esc(h.name)}</option>`).join("")}</select><select class="select" id="filter-floor" aria-label="Floor"><option value="">All floors</option>${[...new Set(state.locations.map(l=>l.floor_number))].sort((a,b)=>a-b).map(n=>`<option value="${n}" ${state.filters.floor==n?"selected":""}>Floor ${n}</option>`).join("")}</select><select class="select" id="filter-wing" aria-label="Wing"><option value="">All wings</option>${[...new Set(state.locations.map(l=>l.wing_name))].sort().map(n=>`<option value="${n}" ${state.filters.wing===n?"selected":""}>Wing ${esc(n)}</option>`).join("")}</select><select class="select" id="filter-area" aria-label="Area"><option value="">All areas</option>${[...new Set(state.locations.map(l=>l.area_type))].sort().map(n=>`<option value="${n}" ${state.filters.area===n?"selected":""}>${esc(human(n))}</option>`).join("")}</select><select class="select" id="filter-category" aria-label="Category"><option value="">All categories</option>${state.categories.map(c=>`<option value="${c.id}" ${state.filters.category==c.id?"selected":""}>${esc(c.name)}</option>`).join("")}</select><select class="select" id="filter-problem" aria-label="Problem type"><option value="">All problem types</option>${state.problemTypes.map(p=>`<option value="${p.id}" ${state.filters.problem==p.id?"selected":""}>${esc(p.name)}</option>`).join("")}</select><button class="btn btn-secondary" data-action="clear-community">Clear filters</button></div>
  <div class="row spread wrap" style="margin-bottom:16px"><div><h2 class="card-title">Public reports</h2><p class="card-subtitle" id="community-summary">Loading reports…</p></div><label class="row small muted">Sort <select class="select" id="community-sort" style="width:auto;min-height:36px;padding:6px 30px 6px 10px"><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select></label></div><div id="community-list"><div class="empty-state"><span class="spinner"></span><p>Loading community reports…</p></div></div><div id="community-pagination" class="pagination"></div></section>`;
}
function issueView() {
  const i=state.currentIssue;
  if(!i) return `<div class="page-heading"><div><h1>Issue Details</h1><p>Loading issue…</p></div><span class="spinner"></span></div>`;
  const own=state.myIssueIds.has(Number(i.id));
  return `<div class="page-heading"><div><a href="#community" data-page="${own?"my-reports":"community"}" class="text-link">← Back to ${own?"My Reports":"Community Issues"}</a><p class="eyebrow" style="margin-top:16px">ISSUE HF-${String(i.id).padStart(4,"0")}</p><h1>${esc(i.title)}</h1><p>${esc(locationLabel(i.location_id))}</p></div><div class="row wrap">${statusChip(i.status)}${i.is_public?'<span class="chip">Public report</span>':'<span class="chip">Private report</span>'}</div></div>
  <div class="detail-layout"><div class="stack"><section class="card card-pad"><div class="section-head"><h2>Issue description</h2><div class="row wrap">${isStaff()?'<span class="chip">Staff view</span>':''}${canEditOrDelete(i)?`<button class="btn btn-secondary btn-small" data-action="edit-issue" data-id="${i.id}">Edit complaint</button><button class="btn btn-danger btn-small" data-action="delete-issue" data-id="${i.id}">Delete complaint</button>`:""}</div></div><p class="detail-description">${esc(i.description)}</p><div class="divider"></div><div class="meta-grid"><div class="meta-box"><small>Location</small><strong>${esc(locationLabel(i.location_id))}</strong></div><div class="meta-box"><small>Problem type</small><strong>${esc(problemLabel(i.problem_type_id))}</strong></div><div class="meta-box"><small>Reported on</small><strong>${esc(date(i.created_at,true))}</strong></div><div class="meta-box"><small>Service date</small><strong>${esc(date(i.service_date))}</strong></div></div><div class="row spread wrap" style="margin-top:18px"><div><strong id="confirmation-count" style="font-size:14px">Community confirmations</strong><div class="small muted" style="margin-top:4px">Other residents can confirm they are affected.</div></div>${i.is_public?`<button class="btn btn-secondary" data-action="toggle-confirm" data-id="${i.id}" id="confirm-button">Me too</button>`:""}</div></section>
  <section class="card card-pad"><div class="section-head"><div><h2>Status timeline</h2><p>Public-safe updates to this report.</p></div></div><div id="issue-timeline"><div class="empty-state"><span class="spinner"></span><p>Loading timeline…</p></div></div></section>
  ${own&&["resolved","closed"].includes(i.status)?`<section class="card card-pad"><h2 class="card-title">Has the issue been fixed?</h2><p class="card-subtitle">Your feedback helps keep the tracker accurate.</p><div class="field" style="margin-top:16px"><label for="resolution-comment">Optional comment</label><textarea class="textarea" id="resolution-comment" placeholder="Tell us whether the fix worked."></textarea></div><div class="row wrap" style="margin-top:14px"><button class="btn" data-action="resolution-feedback" data-outcome="resolved" data-id="${i.id}">Confirm fix</button><button class="btn btn-secondary" data-action="resolution-feedback" data-outcome="not_resolved" data-id="${i.id}">Still not fixed</button><button class="btn btn-secondary" data-action="show-reopen" data-id="${i.id}">Request reopening</button></div></section>`:""}
  </div><aside class="stack"><section class="card card-pad"><h2 class="card-title">Current status</h2><div style="margin:14px 0">${statusChip(i.status)}</div><p class="card-subtitle">Last updated ${esc(date(i.updated_at,true))}</p><div class="divider"></div><div class="row"><span class="metric-icon">◷</span><div><strong style="font-size:13px">Keep an eye on updates</strong><p class="card-subtitle">New status changes appear in the timeline.</p></div></div></section>
  ${isStaff()?`<section class="card card-pad"><h2 class="card-title">Staff actions</h2><p class="card-subtitle">Updates are recorded in the complaint timeline.</p><form id="staff-update-form" class="stack" style="margin-top:16px"><div class="field"><label for="staff-status">Set status</label><select class="select" id="staff-status">${["acknowledged","in_progress","resolved","closed","rejected","reopened"].map(s=>`<option value="${s}" ${s===i.status?"selected":""}>${human(s)}</option>`).join("")}</select></div><div class="field"><label for="staff-note">Progress / resolution note</label><textarea class="textarea" id="staff-note" placeholder="Describe the action taken, or give a rejection reason…"></textarea></div><label class="checkbox-row"><input type="checkbox" id="internal-note"><span>Internal note (not visible to students)</span></label><button class="btn" type="submit">Save update</button></form></section>`:""}</aside></div>`;
}
function myReportsView() { return `<div class="page-heading"><div><p class="eyebrow">YOUR SUBMISSIONS</p><h1>My Reports</h1><p>Track your own complaints, check progress, and confirm whether a fix worked.</p></div><button class="btn" data-page="report">＋ New report</button></div><section class="card card-pad"><div class="row spread wrap" style="margin-bottom:18px"><div><h2 class="card-title">Your reports</h2><p class="card-subtitle" id="my-summary">Loading your reports…</p></div><select class="select" id="my-status-filter" style="width:190px"><option value="">All statuses</option>${["submitted","acknowledged","in_progress","resolved","closed","rejected","reopened"].map(s=>`<option value="${s}">${human(s)}</option>`).join("")}</select></div><div id="my-list"><div class="empty-state"><span class="spinner"></span><p>Loading…</p></div></div><div id="my-pagination" class="pagination"></div></section>`; }
function profileView() { const u=state.user||{};return `<div class="page-heading"><div><p class="eyebrow">ACCOUNT SETTINGS</p><h1>Profile</h1><p>View your account details and manage your HostelFix session.</p></div></div><div class="grid" style="grid-template-columns:minmax(0,1.4fr) minmax(270px,.8fr);align-items:start"><section class="card card-pad"><div class="section-head"><h2>Personal information</h2><span class="chip">${esc(human(u.role||"student"))}</span></div><div class="profile-info"><div class="profile-avatar">${esc(initials(u.name))}</div><div><h2 style="font-size:18px;margin:0 0 5px">${esc(u.name||"HostelFix user")}</h2><p class="card-subtitle">${esc(u.email||"")}</p></div></div><div class="divider"></div><div class="meta-grid"><div class="meta-box"><small>Full name</small><strong>${esc(u.name||"—")}</strong></div><div class="meta-box"><small>Email address</small><strong>${esc(u.email||"—")}</strong></div><div class="meta-box"><small>Role</small><strong>${esc(human(u.role||"student"))}</strong></div><div class="meta-box"><small>Member since</small><strong>${esc(date(u.created_at))}</strong></div></div><div class="divider"></div><div class="row spread wrap"><div><strong style="font-size:13px">Session</strong><p class="card-subtitle">This development build uses a demo identity.</p></div><button class="btn btn-secondary" data-action="logout">Sign out</button></div></section><aside class="stack"><section class="card card-pad"><h2 class="card-title">Privacy and data</h2><p class="card-subtitle" style="line-height:1.7">Public reports do not display your identity. Do not include sensitive personal information in report titles or descriptions.</p></section><section class="card card-pad"><h2 class="card-title" style="color:#991b1b">Delete account</h2><p class="card-subtitle" style="line-height:1.7">Your account will be deactivated in this demo. Existing issue records are retained for audit history.</p><button class="btn btn-danger" style="margin-top:16px" data-action="confirm-delete-account">Delete my account</button></section></aside></div>`; }
function staffView() { return `<div class="page-heading"><div><p class="eyebrow">AUTHORISED WORK QUEUE</p><h1>Staff Dashboard</h1><p>Review issues in your authorised category, record progress, and keep residents informed. Reporter identity is hidden.</p></div><span class="chip">${esc(human(selectedRole()))}</span></div><div class="grid grid-4" id="staff-metrics"><div class="card metric"><div class="metric-label">Total in queue</div><div class="metric-value">—</div></div><div class="card metric"><div class="metric-label">Submitted</div><div class="metric-value">—</div></div><div class="card metric"><div class="metric-label">In progress</div><div class="metric-value">—</div></div><div class="card metric"><div class="metric-label">Resolved</div><div class="metric-value">—</div></div></div><section class="card card-pad" style="margin-top:22px"><div class="row spread wrap" style="margin-bottom:18px"><div><h2 class="card-title">Complaint queue</h2><p class="card-subtitle" id="staff-summary">Loading authorised issues…</p></div><select class="select" id="staff-status-filter" style="width:190px"><option value="">All statuses</option>${["submitted","acknowledged","in_progress","resolved","closed","rejected","reopened"].map(s=>`<option value="${s}">${human(s)}</option>`).join("")}</select></div><div id="staff-list"><div class="empty-state"><span class="spinner"></span><p>Loading queue…</p></div></div></section>`; }
function adminView() { return `<div class="page-heading"><div><p class="eyebrow">SYSTEM OVERVIEW</p><h1>Admin Dashboard</h1><p>Monitor complaint volume, review status distribution, and manage staff accounts.</p></div><button class="btn" data-action="open-staff-modal">＋ Create staff account</button></div><div class="grid grid-4" id="admin-metrics"><div class="card metric"><div class="metric-label">Total issues</div><div class="metric-value">—</div></div><div class="card metric"><div class="metric-label">Open issues</div><div class="metric-value">—</div></div><div class="card metric"><div class="metric-label">In progress</div><div class="metric-value">—</div></div><div class="card metric"><div class="metric-label">Resolved / closed</div><div class="metric-value">—</div></div></div><div class="grid grid-2" style="margin-top:22px"><section class="card card-pad"><h2 class="card-title">Issues by status</h2><p class="card-subtitle">Current complaint lifecycle distribution.</p><div id="admin-status-bars" style="margin-top:24px"><span class="spinner"></span></div></section><section class="card card-pad"><h2 class="card-title">Issues by category</h2><p class="card-subtitle">Maintenance and housekeeping volume.</p><div id="admin-category-bars" style="margin-top:24px"><span class="spinner"></span></div></section></div><section class="card card-pad" style="margin-top:22px"><div class="section-head"><div><h2>Recent complaints</h2><p>Open a complaint to inspect details and status history.</p></div><button class="btn btn-secondary btn-small" data-page="staff">Open staff queue</button></div><div id="admin-issues"><div class="empty-state"><span class="spinner"></span><p>Loading…</p></div></div></section>`; }
function notificationsView() { return `<div class="page-heading"><div><p class="eyebrow">UPDATES</p><h1>Notifications</h1><p>Keep track of complaint status changes.</p></div><button class="btn btn-secondary" data-page="dashboard">Back to dashboard</button></div><section class="card card-pad"><div id="notifications-list"><div class="empty-state"><span class="spinner"></span><p>Loading notifications…</p></div></div></section>`; }
function renderModal() {
  if (state.modal === "edit-issue" && state.editingIssue) {
    const issue = state.editingIssue;
    return `<div class="modal-backdrop" data-action="close-modal"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="edit-issue-title"><h2 id="edit-issue-title">Edit complaint</h2><p>Edits are available only while the complaint is still submitted. Once acknowledged, the record is locked.</p><form id="edit-issue-form" class="stack"><div class="field"><label for="edit-title">Title</label><input class="input" id="edit-title" required minlength="5" maxlength="180" value="${esc(issue.title)}"></div><div class="field"><label for="edit-description">Description</label><textarea class="textarea" id="edit-description" required minlength="10" maxlength="5000">${esc(issue.description)}</textarea></div><div class="field"><label for="edit-location">Location</label><select class="select" id="edit-location" required>${state.locations.map(location=>`<option value="${location.id}" ${Number(location.id)===Number(issue.location_id)?"selected":""}>${esc(locationLabel(location.id))}</option>`).join("")}</select></div><div class="field"><label for="edit-problem">Problem type / category</label><select class="select" id="edit-problem" required>${state.problemTypes.map(problem=>`<option value="${problem.id}" ${Number(problem.id)===Number(issue.problem_type_id)?"selected":""}>${esc(problem.name)} — ${esc(problem.category_name)}</option>`).join("")}</select><span class="hint">Choose the problem based on the actual fault, not just the room or team responsible for the area.</span></div><div class="field"><label for="edit-room-label">Room label (optional)</label><input class="input" id="edit-room-label" maxlength="80" value="${esc(issue.room_label||"")}" placeholder="e.g. 412"></div><div class="field"><label for="edit-service-date">Housekeeping service date (optional)</label><input class="input" id="edit-service-date" type="date" value="${esc(issue.service_date||"")}"></div><label class="checkbox-row"><input id="edit-public" type="checkbox" ${issue.is_public?"checked":""}><span>Show this complaint in Community Issues</span></label><div class="modal-actions"><button class="btn btn-secondary" type="button" data-action="close-modal">Cancel</button><button class="btn" type="submit">Save changes</button></div></form></section></div>`;
  }
  if(state.modal==="delete-issue") return `<div class="modal-backdrop" data-action="close-modal"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="delete-issue-title"><h2 id="delete-issue-title">Delete this complaint?</h2><p>This permanently removes your unacknowledged complaint. You cannot delete it after staff acknowledge it.</p><div class="modal-actions"><button class="btn btn-secondary" data-action="close-modal">Cancel</button><button class="btn btn-danger" data-action="confirm-delete-issue">Delete complaint</button></div></section></div>`;
  if(state.modal==="delete") return `<div class="modal-backdrop" data-action="close-modal"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><h2 id="modal-title">Delete your account?</h2><p>This will deactivate your demo account. Your existing complaint records remain for audit history. You will be signed out.</p><div class="modal-actions"><button class="btn btn-secondary" data-action="close-modal">Cancel</button><button class="btn btn-danger" data-action="delete-account">Delete account</button></div></section></div>`;
  if(state.modal==="staff") return `<div class="modal-backdrop" data-action="close-modal"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><h2 id="modal-title">Create staff account</h2><p>Create a staff identity for the development demo. Use an approved institutional address in a real deployment.</p><form id="staff-create-form" class="stack"><div class="field"><label for="new-staff-name">Full name</label><input class="input" id="new-staff-name" required maxlength="120" placeholder="e.g. Kavita Rao"></div><div class="field"><label for="new-staff-email">Email</label><input class="input" id="new-staff-email" required type="email" maxlength="255" placeholder="staff@iitdh.ac.in"></div><div class="field"><label for="new-staff-category">Category</label><select class="select" id="new-staff-category" required>${state.categories.map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join("")}</select></div><div class="modal-actions"><button class="btn btn-secondary" type="button" data-action="close-modal">Cancel</button><button class="btn" type="submit">Create account</button></div></form></section></div>`;
  if(state.modal==="reopen") return `<div class="modal-backdrop" data-action="close-modal"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><h2 id="modal-title">Request reopening</h2><p>Explain why the issue is still unresolved. This request will be added to the issue history.</p><form id="reopen-form" class="stack"><div class="field"><label for="reopen-reason">Reason</label><textarea class="textarea" id="reopen-reason" required minlength="5" placeholder="The tap is still leaking…"></textarea></div><div class="modal-actions"><button class="btn btn-secondary" type="button" data-action="close-modal">Cancel</button><button class="btn" type="submit">Request reopening</button></div></form></section></div>`;
  return "";
}

async function loadBaseData() {
  const [locs, pts, hostels, cats, demoUsers] = await Promise.all([
    api("/locations/catalog",{auth:false}), api("/problem-types/catalog",{auth:false}), api("/hostels?size=50",{auth:false}), api("/categories?size=50",{auth:false}), api("/demo-users",{auth:false})
  ]);
  state.locations=locs.items||[]; state.problemTypes=pts.items||[]; state.hostels=hostels.items||[]; state.categories=cats.items||[];
  state.demoUsers=demoUsers.items||[];
  if (!state.demoUsers.some(user => Number(user.id) === Number(state.userId))) {
    const student = state.demoUsers.find(user => user.role === "student");
    state.userId = Number(student?.id || state.demoUsers[0]?.id || 0);
    if (state.userId) localStorage.setItem("hf.userId", String(state.userId));
  }
}
async function login() {
  state.userId=Number($("#demo-user")?.value || state.userId);
  if (!state.userId) { toast("No demo users were found. Check that the database seed completed.", "error"); return; }
  localStorage.setItem("hf.userId",String(state.userId));
  try { state.user=await api("/me"); state.loggedIn=true;localStorage.setItem("hf.loggedIn","true");state.page=state.user.role==="administrator"?"admin":state.user.role==="staff"?"staff":"dashboard"; await loadBaseData(); render(); if(state.page==="admin")loadAdmin();else if(state.page==="staff")loadStaffQueue();else loadDashboard(); }
  catch(e){toast(`Demo sign-in failed: ${e.message}`,"error");}
}
async function loadDashboard() {
  try {
    const [mine, community] = await Promise.all([api("/my/issues?size=50"),api("/issues?size=50",{auth:false})]);
    const items=mine.items||[]; items.forEach(i=>state.myIssueIds.add(Number(i.id))); const statuses={progress:items.filter(i=>i.status==="in_progress").length,awaiting:items.filter(i=>["submitted","acknowledged"].includes(i.status)).length};
    const metrics=$("#dashboard-metrics"); if(metrics) metrics.innerHTML=metric("My reports",items.length,"All submitted issues")+metric("In progress",statuses.progress,"Work is underway")+metric("Awaiting response",statuses.awaiting,"Submitted or acknowledged")+metric("Community reports",community.total??(community.items||[]).length,"Publicly visible issues");
    const node=$("#recent-issues"); if(node)node.innerHTML=items.length?items.slice(0,4).map(i=>issueRow(i)).join(""):`<div class="empty-state"><div class="empty-icon">⌁</div><h3>No reports yet</h3><p>When you submit a complaint, it will appear here with its current status.</p><button class="btn" data-page="report">Report your first issue</button></div>`;
  } catch(e){const n=$("#recent-issues");if(n)n.innerHTML=errorState("Could not load your dashboard",e.message,"retry-dashboard");toast(e.message,"error");}
}
function metric(label,value,foot){return `<div class="card metric"><div class="metric-label">${esc(label)}</div><div class="metric-value">${esc(value)}</div><div class="metric-foot">${esc(foot)}</div></div>`;}
function errorState(title,message,action="") { return `<div class="empty-state"><div class="empty-icon">!</div><h3>${esc(title)}</h3><p>${esc(message)}</p>${action?`<button class="btn btn-secondary" data-action="${esc(action)}">Try again</button>`:""}</div>`; }
async function loadCommunity() {
  try {
    if(!state.hostels.length || !state.locations.length) await loadBaseData();
    const [first, mine]=await Promise.all([api(`/issues?page=1&size=50`,{auth:false}),api(`/my/issues?page=1&size=50`)]);
    const remainingPages=Math.max(0,Math.ceil((first.total||0)/50)-1);
    const remaining=await Promise.all(Array.from({length:remainingPages},(_,index)=>api(`/issues?page=${index+2}&size=50`,{auth:false})));
    state.issues=[...(first.items||[]),...remaining.flatMap(page=>page.items||[])];
    (mine.items||[]).forEach(i=>state.myIssueIds.add(Number(i.id))); renderCommunityList();
  } catch(e){const n=$("#community-list");if(n)n.innerHTML=errorState("Reports could not be loaded",e.message,"retry-community");}
}
function filteredCommunity() {
  let items=[...state.issues]; const q=state.search.trim().toLowerCase(), f=state.filters;
  if(q) items=items.filter(i=>`${i.title} ${i.description} ${locationLabel(i.location_id)} ${problemLabel(i.problem_type_id)}`.toLowerCase().includes(q));
  if(f.status)items=items.filter(i=>i.status===f.status);
  if(f.hostel)items=items.filter(i=>String(state.locations.find(l=>l.id===i.location_id)?.hostel_id)===String(f.hostel));
  if(f.floor)items=items.filter(i=>String(state.locations.find(l=>l.id===i.location_id)?.floor_number)===String(f.floor));
  if(f.wing)items=items.filter(i=>state.locations.find(l=>l.id===i.location_id)?.wing_name===f.wing);
  if(f.area)items=items.filter(i=>state.locations.find(l=>l.id===i.location_id)?.area_type===f.area);
  if(f.category)items=items.filter(i=>String(state.problemTypes.find(p=>p.id===i.problem_type_id)?.category_id)===String(f.category));
  if(f.problem)items=items.filter(i=>String(i.problem_type_id)===String(f.problem));
  if($("#community-sort")?.value==="oldest")items.sort((a,b)=>new Date(a.created_at)-new Date(b.created_at)); else items.sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));
  return items;
}
function renderCommunityList() {
  const node=$("#community-list");if(!node)return;const items=filteredCommunity();const pages=Math.max(1,Math.ceil(items.length/PAGE_SIZE));state.listPage=Math.min(state.listPage,pages);const shown=items.slice((state.listPage-1)*PAGE_SIZE,state.listPage*PAGE_SIZE);
  $("#community-summary").textContent=`${items.length} report${items.length===1?"":"s"} match your filters`;
  node.innerHTML=shown.length?shown.map(i=>`<div class="issue-row"><div class="issue-symbol">${isHousekeeping(problemLabel(i.problem_type_id))?"✦":"⌁"}</div><div class="issue-main"><div class="row spread wrap"><a class="issue-title" href="#issue-${i.id}" data-action="open-issue" data-id="${i.id}">HF-${String(i.id).padStart(4,"0")} · ${esc(i.title)}</a>${statusChip(i.status)}</div><div class="issue-meta">${esc(locationLabel(i.location_id))} · ${esc(problemLabel(i.problem_type_id))}<br>Reported ${esc(date(i.created_at,true))}</div><p class="issue-excerpt">${esc(i.description)}</p><div class="issue-actions"><button class="btn btn-secondary btn-small" data-action="open-issue" data-id="${i.id}">View details</button>${state.myIssueIds.has(Number(i.id))?'<span class="small muted">Your report</span>':`<button class="btn btn-secondary btn-small" data-action="toggle-confirm" data-id="${i.id}">＋ Me too</button>`}</div></div></div>`).join(""):`<div class="empty-state"><div class="empty-icon">⌕</div><h3>No reports found</h3><p>Try a different keyword or clear some filters to see more community issues.</p><button class="btn btn-secondary" data-action="clear-community">Clear filters</button></div>`;
  const p=$("#community-pagination");p.innerHTML=items.length?`<button class="btn btn-secondary btn-small" data-action="community-page" data-target-page="${state.listPage-1}" ${state.listPage<=1?"disabled":""}>← Previous</button><span>Page ${state.listPage} of ${pages}</span><button class="btn btn-secondary btn-small" data-action="community-page" data-target-page="${state.listPage+1}" ${state.listPage>=pages?"disabled":""}>Next →</button>`:"";
}
async function loadMyReports() {
  try { const status=$("#my-status-filter")?.value||"";const data=await api(`/my/issues?size=50${status?`&status=${encodeURIComponent(status)}`:""}`);const items=data.items||[];items.forEach(i=>state.myIssueIds.add(Number(i.id)));const node=$("#my-list");if(!node)return;$("#my-summary").textContent=`${data.total??items.length} report${(data.total??items.length)===1?"":"s"} submitted by you`;
    node.innerHTML=items.length?items.slice((state.myPage-1)*PAGE_SIZE,state.myPage*PAGE_SIZE).map(i=>issueRow(i)).join(""):`<div class="empty-state"><div class="empty-icon">⌁</div><h3>No reports yet</h3><p>Your submitted complaints will appear here so you can track progress and confirm resolution.</p><button class="btn" data-page="report">Create a report</button></div>`;
    const pages=Math.max(1,Math.ceil(items.length/PAGE_SIZE));const p=$("#my-pagination");if(p)p.innerHTML=items.length?`<button class="btn btn-secondary btn-small" data-action="my-page" data-target-page="${state.myPage-1}" ${state.myPage<=1?"disabled":""}>← Previous</button><span>Page ${state.myPage} of ${pages}</span><button class="btn btn-secondary btn-small" data-action="my-page" data-target-page="${state.myPage+1}" ${state.myPage>=pages?"disabled":""}>Next →</button>`:"";
  } catch(e){const n=$("#my-list");if(n)n.innerHTML=errorState("Could not load your reports",e.message,"retry-my-reports");}
}
async function openIssue(id) {
  try { state.currentIssue=await api(`/issues/${id}`);state.page="issue";render();const [updates,confirm]=await Promise.all([api(`/issues/${id}/updates?size=50`).catch(()=>({items:[]})),api(`/issues/${id}/confirmations`).catch(()=>({count:0,confirmed:false}))]);
    const timeline=$("#issue-timeline");if(timeline)timeline.innerHTML=(updates.items||[]).length?`<div class="timeline">${updates.items.map(u=>`<div class="timeline-item"><span class="timeline-dot"></span><div><div class="timeline-title">${esc(human(u.new_status))}</div><div class="timeline-meta">${esc(date(u.created_at,true))}</div>${u.comment?`<div class="timeline-note">${esc(u.comment)}</div>`:""}</div></div>`).join("")}</div>`:`<p class="small muted">No status updates are available yet.</p>`;
    const count=$("#confirmation-count");if(count)count.textContent=`${confirm.count||0} ${confirm.count===1?"person has":"people have"} confirmed this issue`;
    const button=$("#confirm-button");if(button){button.hidden=Boolean(confirm.is_reporter)||state.myIssueIds.has(Number(id));button.textContent=confirm.confirmed?"✓ Me too added":"＋ Me too";button.dataset.confirmed=String(confirm.confirmed);button.classList.toggle("btn",true);}
  } catch(e){toast(e.message,"error");}
}
async function toggleConfirm(id) {
  try { const summary=await api(`/issues/${id}/confirmations`);if(summary.confirmed){await api(`/issues/${id}/confirmations`,{method:"DELETE"});toast("Your confirmation was removed.");}else{await api(`/issues/${id}/confirmations`,{method:"POST"});toast("Thanks for confirming you are affected.","success");} if(state.page==="issue")await openIssue(id);else await loadCommunity(); }
  catch(e){toast(e.message,"error");}
}
async function loadProfile() { try { state.user=await api("/me");render(); }catch(e){toast(e.message,"error");} }
async function initReportForm() {
  try {
    if(!state.hostels.length || !state.locations.length) await loadBaseData();
    const hs=$("#hostel-select"), cs=$("#category-select");if(!hs||!cs)return;
    hs.innerHTML='<option value="">Choose a hostel</option>'+state.hostels.map(h=>`<option value="${h.id}">${esc(h.name)}</option>`).join("");
    cs.innerHTML='<option value="">Choose a category</option>'+state.categories.map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join("");
  }catch(e){toast(`Could not load reporting options: ${e.message}`,"error");}
}
async function updateFloors() {
  const hostelId=$("#hostel-select")?.value, floor=$("#floor-select"), wing=$("#wing-select"), area=$("#area-select");if(!floor)return;
  floor.innerHTML='<option value="">Choose a floor</option>';wing.innerHTML='<option value="">Choose a wing</option>';area.innerHTML='<option value="">Choose an area</option>';floor.disabled=wing.disabled=area.disabled=true;
  if(!hostelId)return;const data=await api(`/hostels/${hostelId}/floors?size=50`,{auth:false});floor.innerHTML+=(data.items||[]).map(x=>`<option value="${x.id}">Floor ${x.floor_number}</option>`).join("");floor.disabled=false;
}
async function updateWings() { const floorId=$("#floor-select")?.value,wing=$("#wing-select"),area=$("#area-select");if(!wing)return;wing.innerHTML='<option value="">Choose a wing</option>';area.innerHTML='<option value="">Choose an area</option>';wing.disabled=area.disabled=true;if(!floorId)return;const d=await api(`/floors/${floorId}/wings?size=50`,{auth:false});wing.innerHTML+=(d.items||[]).map(x=>`<option value="${x.id}">Wing ${esc(x.wing_name)}</option>`).join("");wing.disabled=false;}
async function updateAreas() { const wingId=$("#wing-select")?.value,area=$("#area-select");if(!area)return;area.innerHTML='<option value="">Choose an area</option>';area.disabled=true;if(!wingId)return;const d=await api(`/wings/${wingId}/locations?size=50`,{auth:false});area.innerHTML+=(d.items||[]).map(x=>`<option value="${x.id}" data-area-type="${esc(x.area_type)}">${esc(human(x.area_type))}</option>`).join("");area.disabled=false;}
async function updateProblemTypes() { const id=$("#category-select")?.value,p=$("#problem-select");if(!p)return;p.innerHTML='<option value="">Choose a problem type</option>';p.disabled=true;if(!id){toggleHousekeeping();return;}const types=state.problemTypes.filter(x=>String(x.category_id)===String(id));p.innerHTML += types.map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join("");p.disabled=false;toggleHousekeeping();}
function toggleHousekeeping() { const c=state.categories.find(x=>String(x.id)===$("#category-select")?.value);$("#service-date-field")?.classList.toggle("hide",!isHousekeeping(c?.name)); }
function toggleRoomAsset() { const selected=$("#area-select")?.selectedOptions[0];const type=selected?.dataset.areaType;$("#room-field")?.classList.toggle("hide",type!=="room");const assetField=$("#asset-field");if(assetField)assetField.classList.toggle("hide",type!=="lift_lobby"&&type!=="washing_machine_area"&&type!=="drinking_water_area");if(type && ["lift_lobby","washing_machine_area","drinking_water_area"].includes(type))loadAssets(Number(selected.value)); }
async function loadAssets(locationId) { try{const data=await api(`/locations/${locationId}/assets?size=50`,{auth:false});const sel=$("#asset-select");if(sel)sel.innerHTML='<option value="">No specific asset</option>'+(data.items||[]).map(a=>`<option value="${a.id}">${esc(a.name)}</option>`).join("");}catch{}}
const SMART_CLASSIFICATION_RULES = [
  { pattern: /\b(light switch|switch for (the )?light)\b.*\b(not working|broken|loose|repair)\b/i, category: "Maintenance", problem: "Switch repair", title: "Light switch needs repair" },
  { pattern: /\b(washing machine area)\b.*\b(dirty|unclean|cleaning|needs cleaning)\b/i, category: "Housekeeping", problem: "Washing machine area cleaning", title: "Washing machine area cleaning required" },
  { pattern: /\b(drinking water area|water dispenser area)\b.*\b(dirty|unclean|cleaning|needs cleaning)\b/i, category: "Housekeeping", problem: "Drinking water area cleaning", title: "Drinking water area cleaning required" },
  { pattern: /\b(lift lobby)\b.*\b(dirty|unclean|cleaning|needs cleaning)\b/i, category: "Housekeeping", problem: "Unclean lift lobby", title: "Lift lobby cleaning required" },
  { pattern: /\b(cloth drying area)\b.*\b(dirty|unclean|cleaning|needs cleaning)\b/i, category: "Housekeeping", problem: "Cloth drying area cleaning", title: "Cloth drying area cleaning required" },
  { pattern: /\b(light|bulb|tube ?light|lighting)\b.*\b(not working|broken|flicker|fault|repair)|\b(not working|broken|flicker)\b.*\b(light|bulb)\b/i, category: "Maintenance", problem: "Light fixture", title: "Light fixture not working" },
  { pattern: /\b(fan)\b.*\b(not working|broken|repair|noise)|\b(not working|broken)\b.*\bfan\b/i, category: "Maintenance", problem: "Fan repair", title: "Fan not working" },
  { pattern: /\b(socket|plug point|power point)\b.*\b(not working|loose|sparking|broken)|\b(electrical fault|power outage)\b/i, category: "Maintenance", problem: "Power socket", title: "Power socket issue" },
  { pattern: /\b(switch)\b.*\b(not working|broken|loose)|\b(light switch)\b/i, category: "Maintenance", problem: "Switch repair", title: "Switch needs repair" },
  { pattern: /\b(lift|elevator)\b.*\b(stuck|not working|broken|not responding|malfunction)/i, category: "Maintenance", problem: "Lift malfunction", title: "Lift malfunction" },
  { pattern: /\b(washing machine|washer)\b.*\b(not working|broken|leaking|repair|out of order)/i, category: "Maintenance", problem: "Washing machine", title: "Washing machine needs repair" },
  { pattern: /\b(water dispenser|water purifier)\b.*\b(not working|broken|leaking|repair)/i, category: "Maintenance", problem: "Water dispenser", title: "Water dispenser issue" },
  { pattern: /\b(tap|faucet|pipe|shower)\b.*\b(leak|leaking|dripping|broken)|\b(plumbing|water leak|leakage)\b/i, category: "Maintenance", problem: "Plumbing", title: "Plumbing leak" },
  { pattern: /\b(drain|drainage)\b.*\b(block|blocked|clog|clogged|overflow)|\b(blocked drain)\b/i, category: "Maintenance", problem: "Drainage", title: "Blocked drain" },
  { pattern: /\b(lock|latch|door)\b.*\b(broken|stuck|not locking|repair|damaged)/i, category: "Maintenance", problem: "Door/lock", title: "Door or lock needs repair" },
  { pattern: /\b(dustbin|garbage bin|trash bin|waste bin)\b.*\b(full|overflow|overflowing|empty|clean)|\b(garbage|waste)\b.*\b(not collected|overflow|collection)\b/i, category: "Housekeeping", problem: "Dustbin overflow", title: "Dustbin needs emptying" },
  { pattern: /\b(toilet|washroom)\b.*\b(dirty|unclean|cleaning|smell|stain)|\b(clean|cleaning)\b.*\b(toilet|washroom)\b/i, category: "Housekeeping", problem: "Toilet cleaning", title: "Toilet cleaning required" },
  { pattern: /\b(bathroom|shower area)\b.*\b(dirty|unclean|cleaning|stain)|\b(clean|cleaning)\b.*\bbathroom\b/i, category: "Housekeeping", problem: "Bathroom cleaning", title: "Bathroom cleaning required" },
  { pattern: /\b(corridor|hallway)\b.*\b(dirty|unclean|cleaning|sweep)|\b(clean|cleaning)\b.*\b(corridor|hallway)\b/i, category: "Housekeeping", problem: "Corridor cleaning", title: "Corridor cleaning required" },
  { pattern: /\b(room|floor|area)\b.*\b(dirty|dusty|unclean|needs cleaning)|\b(cleaning required|needs cleaning|unclean area)\b/i, category: "Housekeeping", problem: "Cleaning", title: "Cleaning required" },
  { pattern: /\b(pest|cockroach|mosquito|rat|rodent|ants|termite)\b/i, category: "Housekeeping", problem: "Pest issue", title: "Pest issue reported" },
  { pattern: /\b(wet floor|spillage|spilled|spill)\b/i, category: "Housekeeping", problem: "Wet floor", title: "Wet floor needs attention" },
];

function smartDraft() {
  const text = $("#smart-description")?.value.trim();
  const out = $("#smart-message");
  if (!out) return;
  if (!text) {
    out.innerHTML = '<div class="alert warning">Describe the issue first, then try drafting.</div>';
    return;
  }

  const match = SMART_CLASSIFICATION_RULES.find(rule => rule.pattern.test(text));
  $("#issue-description").value = text;
  const suggestedTitle = match?.title || text.split(/\s+/).filter(Boolean).slice(0, 9).join(" ").replace(/[.,!?]+$/g, "");
  $("#issue-title").value = suggestedTitle.length >= 5 ? suggestedTitle.charAt(0).toUpperCase() + suggestedTitle.slice(1) : "Hostel issue requiring attention";

  if (match) {
    const category = state.categories.find(item => item.name === match.category);
    const problem = state.problemTypes.find(item => item.name === match.problem && item.category_name === match.category);
    if (category && problem) {
      $("#category-select").value = String(category.id);
      updateProblemTypes().then(() => { $("#problem-select").value = String(problem.id); });
    }
    out.innerHTML = `<div class="alert warning"><strong>Suggested classification: ${esc(match.category)} / ${esc(match.problem)}.</strong> Check the suggested category, problem type and exact location before submitting. This is a keyword-based draft, not an AI decision.</div>`;
  } else {
    out.innerHTML = '<div class="alert warning"><strong>No confident category suggestion.</strong> The description was copied into the form, but category and problem type were left unchanged. Choose the closest problem manually to avoid a misleading classification.</div>';
  }
}

function submitIssue(event) {
  event.preventDefault();const locationId=Number($("#area-select")?.value),problemTypeId=Number($("#problem-select")?.value),loc=state.locations.find(x=>x.id===locationId);const payload={title:$("#issue-title").value.trim(),description:$("#issue-description").value.trim(),location_id:locationId,problem_type_id:problemTypeId,is_public:$("#issue-public").checked};
  if(loc?.area_type==="room")payload.room_label=$("#room-label").value.trim()||null;
  const category=state.categories.find(c=>String(c.id)===$("#category-select").value);if(isHousekeeping(category?.name)&&$("#service-date").value)payload.service_date=$("#service-date").value;
  if(!payload.location_id||!payload.problem_type_id){toast("Select a complete location and problem type.","error");return;}
  state.pendingIssue=payload;
  const overlay=document.createElement("div");overlay.id="review-overlay";overlay.className="modal-backdrop";overlay.innerHTML=`<section class="modal" role="dialog" aria-modal="true" aria-labelledby="review-title"><p class="eyebrow">FINAL CHECK</p><h2 id="review-title">Review and submit</h2><p>Please check the location and description. Your report will only be submitted when you confirm below.</p><div class="meta-grid" style="margin-top:16px"><div class="meta-box"><small>Title</small><strong>${esc(payload.title)}</strong></div><div class="meta-box"><small>Category / problem</small><strong>${esc(problemLabel(payload.problem_type_id))}</strong></div><div class="meta-box" style="grid-column:1/-1"><small>Location</small><strong>${esc(locationLabel(payload.location_id))}</strong></div><div class="meta-box" style="grid-column:1/-1"><small>Description</small><strong style="font-weight:500;white-space:pre-wrap">${esc(payload.description)}</strong></div><div class="meta-box"><small>Visibility</small><strong>${payload.is_public?"Public-safe community report":"Private to you and authorised staff"}</strong></div></div><div class="modal-actions"><button class="btn btn-secondary" data-action="cancel-review" type="button">Go back</button><button class="btn" data-action="submit-reviewed" type="button">Confirm submission</button></div></section>`;document.body.appendChild(overlay);
}
async function openEditIssue(issueId) {
  try {
    const issue = await api(`/issues/${issueId}`);
    if (!state.myIssueIds.has(Number(issueId)) || issue.status !== "submitted") {
      throw new Error("Only your unacknowledged complaints can be edited.");
    }
    state.editingIssue = issue;
    state.modal = "edit-issue";
    render();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function saveIssueEdits(event) {
  event.preventDefault();
  const issue = state.editingIssue;
  if (!issue) return;
  const payload = {
    title: $("#edit-title").value.trim(),
    description: $("#edit-description").value.trim(),
    location_id: Number($("#edit-location").value),
    problem_type_id: Number($("#edit-problem").value),
    room_label: $("#edit-room-label").value.trim() || null,
    service_date: $("#edit-service-date").value || null,
    is_public: $("#edit-public").checked,
  };
  try {
    await api(`/issues/${issue.id}`, { method: "PATCH", body: JSON.stringify(payload) });
    state.modal = null;
    state.editingIssue = null;
    toast("Complaint updated.", "success");
    await openIssue(issue.id);
  } catch (error) {
    toast(error.message, "error");
  }
}

async function deleteIssue(issueId) {
  const issue = await api(`/issues/${issueId}`);
  if (!state.myIssueIds.has(Number(issueId)) || issue.status !== "submitted") {
    toast("Only your unacknowledged complaints can be deleted.", "error");
    return;
  }
  state.editingIssue = issue;
  state.modal = "delete-issue";
  render();
}

async function confirmDeleteIssue() {
  const issue = state.editingIssue;
  if (!issue) return;
  try {
    await api(`/issues/${issue.id}`, { method: "DELETE" });
    state.myIssueIds.delete(Number(issue.id));
    state.editingIssue = null;
    state.currentIssue = null;
    state.modal = null;
    toast("Complaint deleted.", "success");
    setPage("my-reports");
  } catch (error) {
    toast(error.message, "error");
  }
}

async function createIssueNow(){if(!state.pendingIssue)return;const payload=state.pendingIssue;const overlay=$("#review-overlay");if(overlay)overlay.remove();state.pendingIssue=null;try{const issue=await api("/issues",{method:"POST",body:JSON.stringify(payload)});state.myIssueIds.add(Number(issue.id));toast("Your report was submitted successfully.","success");await openIssue(issue.id);}catch(e){toast(e.message,"error");}}
async function loadStaffQueue() {
  try {const data=await api("/staff/issues?size=50");const all=data.items||[];const metrics=$("#staff-metrics");if(metrics)metrics.innerHTML=metric("Total in queue",data.total??all.length,"Authorised issues")+metric("Submitted",all.filter(i=>i.status==="submitted").length,"Awaiting acknowledgement")+metric("In progress",all.filter(i=>i.status==="in_progress").length,"Work underway")+metric("Resolved",all.filter(i=>i.status==="resolved").length,"Marked resolved");renderStaffItems(all);}catch(e){const n=$("#staff-list");if(n)n.innerHTML=errorState("Could not load staff queue",e.message);toast(e.message,"error");}
}
function renderStaffItems(items) {const n=$("#staff-list");if(!n)return;const status=$("#staff-status-filter")?.value||"";const filtered=status?items.filter(i=>i.status===status):items;$("#staff-summary").textContent=`${filtered.length} issue${filtered.length===1?"":"s"} in this view`;n.innerHTML=filtered.length?`<div class="table-wrap"><table class="table"><thead><tr><th>Issue</th><th>Location</th><th>Status</th><th>Reported</th><th>Action</th></tr></thead><tbody>${filtered.map(i=>`<tr><td><a class="issue-title" data-action="open-issue" data-id="${i.id}" href="#issue-${i.id}">HF-${String(i.id).padStart(4,"0")} · ${esc(i.title)}</a><div class="small muted" style="margin-top:5px">${esc(problemLabel(i.problem_type_id))}</div></td><td>${esc(locationLabel(i.location_id))}</td><td>${statusChip(i.status)}</td><td>${esc(date(i.created_at))}</td><td><button class="btn btn-secondary btn-small" data-action="open-issue" data-id="${i.id}">Manage</button></td></tr>`).join("")}</tbody></table></div>`:`<div class="empty-state"><div class="empty-icon">✓</div><h3>No matching issues</h3><p>Try a different status filter.</p></div>`;}
async function saveStaffUpdate(event) {event.preventDefault();if(!state.currentIssue)return;const payload={status:$("#staff-status").value,comment:$("#staff-note").value.trim()||null,is_internal:$("#internal-note").checked};try{await api(`/staff/issues/${state.currentIssue.id}/status`,{method:"PATCH",body:JSON.stringify(payload)});toast("Issue status updated.","success");await openIssue(state.currentIssue.id);}catch(e){toast(e.message,"error");}}
async function loadAdmin() {try{const [data,issues]=await Promise.all([api("/admin/analytics"),api("/staff/issues?size=10")]);const allStatus=data.by_status||[];const total=data.total_issues||0;const open=allStatus.filter(x=>!["resolved","closed"].includes(x.status)).reduce((s,x)=>s+x.count,0);const progress=allStatus.find(x=>x.status==="in_progress")?.count||0;const resolved=allStatus.filter(x=>["resolved","closed"].includes(x.status)).reduce((s,x)=>s+x.count,0);const m=$("#admin-metrics");if(m)m.innerHTML=metric("Total issues",total,"All complaint records")+metric("Open issues",open,"Not yet closed")+metric("In progress",progress,"Work underway")+metric("Resolved / closed",resolved,"Completed lifecycle");
  const statusNode=$("#admin-status-bars");if(statusNode)statusNode.innerHTML=allStatus.length?allStatus.map(x=>bar(x.status,x.count,total)).join(""):'<p class="small muted">No issue data yet.</p>';const catNode=$("#admin-category-bars");if(catNode)catNode.innerHTML=(data.by_category||[]).map(x=>bar(x.category,x.count,total)).join("")||'<p class="small muted">No category data yet.</p>';const issueNode=$("#admin-issues");if(issueNode)issueNode.innerHTML=(issues.items||[]).length?issues.items.map(i=>issueRow(i)).join(""):'<p class="small muted">No complaints yet.</p>';}
 catch(e){toast(e.message,"error");const n=$("#admin-status-bars");if(n)n.innerHTML=errorState("Could not load analytics",e.message);}}
function bar(label,count,total){const pct=total?Math.round(count/total*100):0;return `<div class="bar-row"><span>${esc(human(label))}</span><div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div><strong>${esc(count)}</strong></div>`;}
async function createStaff(event){event.preventDefault();const payload={name:$("#new-staff-name").value.trim(),email:$("#new-staff-email").value.trim(),category_id:Number($("#new-staff-category").value)};try{const u=await api("/admin/staff",{method:"POST",body:JSON.stringify(payload)});state.modal=null;render();loadAdmin();toast(`Staff account created for ${u.email}.`,"success");}catch(e){toast(e.message,"error");}}
async function loadNotifications(){try{const data=await api("/notifications?size=50");state.notifications=data.items||[];const n=$("#notifications-list");if(!n)return;n.innerHTML=state.notifications.length?state.notifications.map(x=>`<div class="notice-row ${x.is_read?"":"unread"}"><div class="row spread wrap"><div class="notice-title">${esc(x.title)}</div>${x.is_read?'<span class="chip">Read</span>':'<button class="btn btn-secondary btn-small" data-action="mark-read" data-id="'+x.id+'">Mark as read</button>'}</div><div class="notice-message">${esc(x.message)}</div><div class="notice-date">${esc(date(x.created_at,true))}</div>${x.issue_id?`<button class="btn btn-quiet btn-small" data-action="open-issue" data-id="${x.issue_id}">View issue →</button>`:""}</div>`).join(""):'<div class="empty-state"><div class="empty-icon">♧</div><h3>You are all caught up</h3><p>Notifications about complaint updates will appear here.</p></div>';renderHeaderOnly();}catch(e){toast(e.message,"error");}}
function renderHeaderOnly(){const app=$("#app");const old=app.querySelector(".topbar");if(old){const tmp=document.createElement("div");tmp.innerHTML=header(state.page);old.replaceWith(tmp.firstElementChild);}}
async function markRead(id){try{await api(`/notifications/${id}`,{method:"PATCH",body:JSON.stringify({is_read:true})});await loadNotifications();toast("Notification marked as read.","success");}catch(e){toast(e.message,"error");}}

// Delegated interaction handlers keep navigation and dynamically rendered rows functional.
document.addEventListener("click", async event=>{
  const pageLink=event.target.closest("[data-page]");if(pageLink){event.preventDefault();setPage(pageLink.dataset.page);return;}
  const el=event.target.closest("[data-action]");if(!el)return;const action=el.dataset.action;
  if(action==="toggle-menu"){$("#main-nav")?.classList.toggle("open");return;}
  if(action==="open-issue"){event.preventDefault();await openIssue(Number(el.dataset.id));return;}
  if(action==="edit-issue"){await openEditIssue(Number(el.dataset.id));return;}
  if(action==="delete-issue"){try{await deleteIssue(Number(el.dataset.id));}catch(error){toast(error.message,"error");}return;}
  if(action==="confirm-delete-issue"){await confirmDeleteIssue();return;}
  if(action==="toggle-confirm"){await toggleConfirm(Number(el.dataset.id));return;}
  if(action==="community-page"){state.listPage=Number(el.dataset.targetPage);renderCommunityList();return;}
  if(action==="my-page"){state.myPage=Number(el.dataset.targetPage);loadMyReports();return;}
  if(action==="clear-community"){state.search="";state.filters={status:"",hostel:"",floor:"",wing:"",area:"",category:"",problem:""};state.listPage=1;render();loadCommunity();return;}
  if(action==="smart-draft"){smartDraft();return;}
  if(action==="cancel-review"){$("#review-overlay")?.remove();state.pendingIssue=null;return;}
  if(action==="submit-reviewed"){await createIssueNow();return;}
  if(action==="google-signin"){state.page="google-signin";render();return;}
  if(action==="register"){state.page="signup";render();return;}
  if(action==="reset-password"){state.page="reset-password";render();return;}
  if(action==="back-to-login"){state.page="login";render();return;}
  if(action==="staff-login"){const user=state.demoUsers.find(item=>item.role==="staff"&&item.email.startsWith("maintenance-"))||state.demoUsers.find(item=>item.role==="staff");if(user){state.userId=user.id;localStorage.setItem("hf.userId",String(user.id));$("#demo-user").value=String(user.id);}toast("Choose Sign in to continue as demo staff.");return;}
  if(action==="admin-login"){const user=state.demoUsers.find(item=>item.role==="administrator");if(user){state.userId=user.id;localStorage.setItem("hf.userId",String(user.id));$("#demo-user").value=String(user.id);}toast("Choose Sign in to continue as demo administrator.");return;}
  if(action==="logout"){state.loggedIn=false;localStorage.removeItem("hf.loggedIn");state.user=null;state.page="login";render();return;}
  if(action==="confirm-delete-account"){state.modal="delete";render();return;}
  if(action==="delete-account"){try{await api("/me",{method:"DELETE"});state.modal=null;state.loggedIn=false;localStorage.removeItem("hf.loggedIn");toast("Your demo account has been deactivated.","success");render();}catch(e){toast(e.message,"error");}return;}
  if(action==="close-modal"){if(event.target===el || el.tagName==="BUTTON"){state.modal=null;render();if(state.page==="admin")loadAdmin();if(state.page==="issue"&&state.currentIssue)openIssue(state.currentIssue.id);}return;}
  if(action==="open-staff-modal"){state.modal="staff";render();loadAdmin();return;}
  if(action==="show-reopen"){state.modal="reopen";render();return;}
  if(action==="resolution-feedback"){const payload={outcome:el.dataset.outcome,comment:$("#resolution-comment")?.value.trim()||null};try{await api(`/issues/${el.dataset.id}/resolution-feedback`,{method:"POST",body:JSON.stringify(payload)});toast(payload.outcome==="resolved"?"Thanks for confirming the fix.":payload.outcome==="not_resolved"?"Thanks for the feedback.":"Reopening requested.","success");await openIssue(Number(el.dataset.id));}catch(e){toast(e.message,"error");}return;}
  if(action==="notifications"){state.page="notifications";render();loadNotifications();return;}
  if(action==="mark-read"){await markRead(Number(el.dataset.id));return;}
  if(action==="retry-dashboard"){loadDashboard();return;}if(action==="retry-community"){loadCommunity();return;}if(action==="retry-my-reports"){loadMyReports();return;}
});
document.addEventListener("submit", async event=>{
  if(event.target.id==="login-form"){event.preventDefault();await login();}
  if(event.target.id==="issue-form")await submitIssue(event);
  if(event.target.id==="edit-issue-form")await saveIssueEdits(event);
  if(event.target.id==="staff-update-form")await saveStaffUpdate(event);
  if(event.target.id==="staff-create-form")await createStaff(event);
  if(event.target.id==="reopen-form"){event.preventDefault();const reason=$("#reopen-reason").value.trim();try{await api(`/issues/${state.currentIssue.id}/resolution-feedback`,{method:"POST",body:JSON.stringify({outcome:"reopen_requested",comment:reason})});state.modal=null;toast("Reopening requested. The issue has been marked for review.","success");await openIssue(state.currentIssue.id);}catch(e){toast(e.message,"error");}}
});
document.addEventListener("change", async event=>{
  const id=event.target.id;
  try {
    if(id==="demo-user"){state.userId=Number(event.target.value);localStorage.setItem("hf.userId",String(state.userId));}
    if(id==="hostel-select")await updateFloors();if(id==="floor-select")await updateWings();if(id==="wing-select")await updateAreas();if(id==="area-select")toggleRoomAsset();if(id==="category-select")await updateProblemTypes();
    if(id==="community-search"){state.search=event.target.value;state.listPage=1;renderCommunityList();}
    if(id==="filter-status"){state.filters.status=event.target.value;state.listPage=1;renderCommunityList();}
    if(id==="filter-hostel"){state.filters.hostel=event.target.value;state.listPage=1;renderCommunityList();}
    if(id==="filter-category"){state.filters.category=event.target.value;state.listPage=1;renderCommunityList();}if(id==="filter-floor"){state.filters.floor=event.target.value;state.listPage=1;renderCommunityList();}if(id==="filter-wing"){state.filters.wing=event.target.value;state.listPage=1;renderCommunityList();}if(id==="filter-area"){state.filters.area=event.target.value;state.listPage=1;renderCommunityList();}if(id==="filter-problem"){state.filters.problem=event.target.value;state.listPage=1;renderCommunityList();}
    if(id==="community-sort")renderCommunityList();if(id==="my-status-filter"){state.myPage=1;loadMyReports();}if(id==="staff-status-filter")loadStaffQueue();
  }catch(e){toast(e.message,"error");}
});
document.addEventListener("input",event=>{if(event.target.id==="community-search"){state.search=event.target.value;state.listPage=1;renderCommunityList();}});
document.addEventListener("keydown",event=>{if(event.key==="Escape"&&state.modal){state.modal=null;render();}});

(async function boot(){
  try { await loadBaseData(); } catch(e) { console.warn("Initial catalog load failed",e); }
  if(state.loggedIn){try{state.user=await api("/me");state.page=state.user.role==="administrator"?"admin":state.user.role==="staff"?"staff":"dashboard";}catch{state.loggedIn=false;localStorage.removeItem("hf.loggedIn");state.page="login";}}
  render();if(state.loggedIn){if(state.page==="dashboard")loadDashboard();else if(state.page==="staff")loadStaffQueue();else if(state.page==="admin")loadAdmin();}
})();
