/* Aura Portal — SPA Logic
 * Role-based dashboard with live API calls to /api/portal/*
 * Light theme, Diagrid-inspired layout
 */

// ── Role definitions ──────────────────────────────────────────────────────────

const ROLES = {
  procurement: {
    label: "Procurement Officer",
    icon: "🛒",
    sections: [
      {
        label: "HOME",
        items: [{ id: "overview", icon: "◉", label: "Overview" }],
      },
      {
        label: "OBSERVE",
        items: [
          { id: "history",   icon: "≡", label: "Request History" },
          { id: "pipelines", icon: "⟳", label: "Active Pipelines" },
        ],
      },
      {
        label: "ACT",
        items: [
          { id: "submit", icon: "+", label: "New Request" },
        ],
      },
    ],
    default: "overview",
  },
  finance: {
    label: "Finance Approver",
    icon: "💳",
    sections: [
      {
        label: "HOME",
        items: [{ id: "overview", icon: "◉", label: "Overview" }],
      },
      {
        label: "REVIEW",
        items: [
          { id: "pending",  icon: "⏳", label: "Pending Approvals" },
          { id: "approved", icon: "✔", label: "Approval History" },
        ],
      },
    ],
    default: "overview",
  },
  compliance: {
    label: "Compliance Officer",
    icon: "🔍",
    sections: [
      {
        label: "HOME",
        items: [{ id: "overview", icon: "◉", label: "Overview" }],
      },
      {
        label: "MONITOR",
        items: [
          { id: "events",  icon: "⚡", label: "Live Events" },
          { id: "blocked", icon: "✕", label: "Blocked Vendors" },
          { id: "stats",   icon: "◎", label: "Statistics" },
        ],
      },
    ],
    default: "overview",
  },
  itmanager: {
    label: "IT Manager",
    icon: "💻",
    sections: [
      {
        label: "HOME",
        items: [{ id: "overview", icon: "◉", label: "Overview" }],
      },
      {
        label: "CATALOG",
        items: [
          { id: "vendors",   icon: "≡", label: "Vendor Catalog" },
          { id: "contracts", icon: "📄", label: "Active Contracts" },
        ],
      },
    ],
    default: "overview",
  },
  admin: {
    label: "Admin",
    icon: "⚙",
    sections: [
      {
        label: "HOME",
        items: [{ id: "overview", icon: "◉", label: "Overview" }],
      },
      {
        label: "RUN & OPERATE",
        items: [
          { id: "metrics",  icon: "◈", label: "System Metrics" },
          { id: "policies", icon: "🛡", label: "Policies" },
          { id: "queue",    icon: "⏳", label: "Review Queue" },
        ],
      },
    ],
    default: "overview",
  },
};

// ── State ─────────────────────────────────────────────────────────────────────

let currentRole = "procurement";
let currentView = "history";
let searchTerm  = "";
let autoRefreshTimer = null;

// ── DOM refs ───────────────────────────────────────────────────────────────────

const viewEl         = document.getElementById("view");
const navEl          = document.getElementById("sidebarNav");
const roleSelect     = document.getElementById("roleSelect");
const breadcrumb     = document.getElementById("breadcrumb");
const breadcrumbView = document.getElementById("breadcrumbView");
const roleBadge      = document.getElementById("roleBadge");
const searchInput    = document.getElementById("searchInput");
const toolbarActions = document.getElementById("toolbarActions");
const refreshBtn     = document.getElementById("refreshBtn");
const submitModal    = document.getElementById("submitModal");

// ── Init ───────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  roleSelect.addEventListener("change", (e) => switchRole(e.target.value));
  refreshBtn.addEventListener("click", () => loadView(currentView));

  // Sidebar collapse toggle
  const sidebarEl     = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebarOpenBtn = document.getElementById("sidebarOpenBtn");
  if (sidebarToggle && sidebarEl) {
    sidebarToggle.addEventListener("click", () => {
      sidebarEl.classList.add("collapsed");
      if (sidebarOpenBtn) sidebarOpenBtn.style.display = "";
    });
  }
  if (sidebarOpenBtn && sidebarEl) {
    sidebarOpenBtn.addEventListener("click", () => {
      sidebarEl.classList.remove("collapsed");
      sidebarOpenBtn.style.display = "none";
    });
  }
  searchInput.addEventListener("input", (e) => {
    searchTerm = e.target.value.toLowerCase();
    loadView(currentView);
  });

  // Modal
  document.getElementById("modalClose").addEventListener("click", closeModal);
  document.getElementById("modalCancelBtn").addEventListener("click", closeModal);
  document.getElementById("modalSubmitBtn").addEventListener("click", submitRequest);

  switchRole("procurement");
});

// ── Role switching ─────────────────────────────────────────────────────────────

function switchRole(role) {
  currentRole = role;
  searchTerm = "";
  searchInput.value = "";
  clearAutoRefresh();

  const def = ROLES[role];
  breadcrumb.textContent = def.label;
  roleBadge.textContent  = def.label;

  // Build sidebar nav
  navEl.innerHTML = "";
  def.sections.forEach(sec => {
    const label = document.createElement("div");
    label.className = "nav-section-label";
    label.textContent = sec.label;
    navEl.appendChild(label);

    sec.items.forEach(item => {
      const a = document.createElement("div");
      a.className = "nav-item";
      a.dataset.view = item.id;
      a.innerHTML = `<span class="nav-icon">${item.icon}</span><span>${item.label}</span>`;
      a.addEventListener("click", () => {
        setActiveNav(item.id);
        loadView(item.id);
      });
      navEl.appendChild(a);
    });
  });

  loadView(def.default);
  setActiveNav(def.default);
}

function setActiveNav(viewId) {
  currentView = viewId;
  navEl.querySelectorAll(".nav-item").forEach(el => {
    el.classList.toggle("active", el.dataset.view === viewId);
  });

  // Update breadcrumb view label
  let label = viewId;
  ROLES[currentRole].sections.forEach(sec => {
    sec.items.forEach(item => { if (item.id === viewId) label = item.label; });
  });
  breadcrumbView.textContent = label;
}

// ── Auto-refresh ───────────────────────────────────────────────────────────────

function startAutoRefresh(intervalMs) {
  clearAutoRefresh();
  autoRefreshTimer = setInterval(() => loadView(currentView, true), intervalMs);
}

function clearAutoRefresh() {
  if (autoRefreshTimer) { clearInterval(autoRefreshTimer); autoRefreshTimer = null; }
}

// ── View loader ────────────────────────────────────────────────────────────────

async function loadView(viewId, silent = false) {
  currentView = viewId;
  clearAutoRefresh();
  setActiveNav(viewId);
  if (!silent) toolbarActions.innerHTML = "";

  const viewMap = {
    // Overview
    overview:  () => fetchAndRender("/api/portal/overview", renderOverview, 8000, silent),
    // Procurement
    history:   () => fetchAndRender("/api/portal/procurement/history",  renderHistory, 0, silent),
    pipelines: () => fetchAndRender("/api/portal/procurement/pipelines", renderPipelines, 0, silent),
    submit:    () => { if (!silent) renderSubmitPage(); },
    // Finance
    pending:   () => fetchAndRender("/api/portal/finance/pending",       renderPending, 0, silent),
    approved:  () => fetchAndRender("/api/portal/finance/history",        renderApprovalHistory, 0, silent),
    // Compliance
    events:    () => fetchAndRender("/api/portal/compliance/events",     renderEvents, 5000, silent),
    blocked:   () => fetchAndRender("/api/portal/compliance/blocked",    renderBlocked, 0, silent),
    stats:     () => fetchAndRenderMulti(
                       ["/api/portal/compliance/stats", "/api/portal/compliance/events", "/api/portal/compliance/blocked"],
                       renderComplianceStats, 0, silent),
    // IT Manager
    vendors:   () => fetchAndRender("/api/portal/itmanager/vendors",     renderVendors, 0, silent),
    contracts: () => fetchAndRender("/api/portal/itmanager/contracts",   renderContracts, 0, silent),
    // Admin
    metrics:   () => fetchAndRender("/api/portal/admin/metrics",         renderMetrics, 10000, silent),
    policies:  () => fetchAndRender("/api/portal/admin/policies",        renderPolicies, 0, silent),
    queue:     () => fetchAndRender("/api/portal/admin/queue",           renderAdminQueue, 0, silent),
  };

  const fn = viewMap[viewId];
  if (fn) fn();
}

async function fetchAndRender(url, renderFn, autoRefreshMs = 0, silent = false) {
  if (!silent) showLoading();
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderFn(data);
    if (autoRefreshMs > 0) startAutoRefresh(autoRefreshMs);
  } catch (e) {
    if (!silent) showError(e.message);
  }
}

async function fetchAndRenderMulti(urls, renderFn, autoRefreshMs = 0, silent = false) {
  if (!silent) showLoading();
  try {
    const results = await Promise.all(urls.map(u => fetch(u).then(r => r.json())));
    renderFn(...results);
    if (autoRefreshMs > 0) startAutoRefresh(autoRefreshMs);
  } catch (e) {
    if (!silent) showError(e.message);
  }
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function showLoading() {
  viewEl.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Loading…</p></div>`;
}

function showError(msg) {
  viewEl.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠</div><p>Error: ${msg}</p></div>`;
}

function badge(status) {
  const s = (status || "").toLowerCase().replace(/[^a-z_]/g, "");
  const labels = {
    settled: "SETTLED", completed: "COMPLETED", approved: "APPROVED",
    blocked: "BLOCKED", rejected: "REJECTED",
    running: "RUNNING", review: "REVIEW", pending: "PENDING",
    pending_approval: "PENDING APPROVAL",
    active: "ACTIVE",
  };
  const label = labels[s] || status || "—";
  return `<span class="badge badge-${s}"><span class="badge-dot"></span>${label}</span>`;
}

function usd(val) {
  return `$${Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function filterRows(rows, keys) {
  if (!searchTerm) return rows;
  return rows.filter(row =>
    keys.some(k => String(row[k] || "").toLowerCase().includes(searchTerm))
  );
}

function countLabel(n, singular) {
  return `${n} ${n === 1 ? singular : singular + "s"}`;
}

// ── Add "New Request" toolbar button ─────────────────────────────────────────

function addNewRequestBtn() {
  const btn = document.createElement("button");
  btn.className = "btn-primary";
  btn.textContent = "+ New Request";
  btn.addEventListener("click", openModal);
  toolbarActions.appendChild(btn);
}


// ── OVERVIEW: System dashboard ───────────────────────────────────────────────

function renderOverview(data) {
  toolbarActions.innerHTML = `<span style="font-size:12px;color:var(--text-muted)">↻ Auto-refresh every 8s</span>`;

  const agentMeta = {
    Architect: { icon: "🏛️", role: "Procurement Officer" },
    Governor:  { icon: "⚖️",  role: "Finance Controller" },
    Scout:     { icon: "🔭", role: "Category Manager" },
    Sentinel:  { icon: "🛡️", role: "Compliance Officer" },
    Closer:    { icon: "💳", role: "Payment Manager" },
  };

  const agentNodes = Object.entries(data.agents).map(([name, info], i, arr) => {
    const meta = agentMeta[name] || { icon: "◈", role: "" };
    const arrow = i < arr.length - 1 ? `<div class="ov-arrow">→</div>` : "";
    return `
      <div class="ov-agent">
        <div class="ov-agent-icon">${meta.icon}</div>
        <div class="ov-agent-name">${name}</div>
        <div class="ov-agent-role">${meta.role}</div>
        <div class="ov-agent-stat">${info.invocations} calls · ${info.avg_ms}ms</div>
      </div>${arrow}`;
  }).join("");

  const recentRows = (data.recent || []).map(r => `
    <tr>
      <td>${badge(r.status)}</td>
      <td><span class="td-mono">${r.id}</span></td>
      <td>${r.description}</td>
      <td>${r.vendor || "—"}</td>
      <td class="text-right td-amount">${usd(r.amount_usd)}</td>
    </tr>`).join("");

  viewEl.innerHTML = `
    <div class="overview-hero">
      <div class="overview-hero-left">
        <div class="overview-title">Aura <span class="overview-badge-demo">DEMO</span></div>
        <div class="overview-subtitle">Autonomous Reliable Agentic Commerce &middot; Google ADK + Gemini 2.5 Flash via Vertex AI</div>
        <div class="overview-tagline">5-agent sequential pipeline: intent &rarr; policy gate &rarr; vendor discovery &rarr; KYC/AML &rarr; AP2 settlement</div>
      </div>
      <div class="overview-hero-right">
        <div class="overview-live-dot"></div>
        <span class="overview-live-label">LIVE &mdash; ${data.active_pipelines} pipeline${data.active_pipelines !== 1 ? "s" : ""} active</span>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card teal">
        <div class="stat-value">${data.total_requests}</div>
        <div class="stat-label">Total Requests</div>
      </div>
      <div class="stat-card green">
        <div class="stat-value">${data.settled}</div>
        <div class="stat-label">Settled (${data.settlement_rate_pct}%)</div>
      </div>
      <div class="stat-card red">
        <div class="stat-value">${data.blocked}</div>
        <div class="stat-label">Blocked by AML / KYC</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-value">${data.review}</div>
        <div class="stat-label">Under Review</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${(data.avg_latency_ms / 1000).toFixed(1)}s</div>
        <div class="stat-label">Avg Pipeline Latency</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${data.blocked_vendors_count}</div>
        <div class="stat-label">Blocked Vendors</div>
      </div>
    </div>

    <div class="overview-pipeline-card">
      <div class="table-card-header">
        <span class="table-card-title">Agent Pipeline &mdash; 5-Stage Sequential Flow</span>
        <span class="table-card-meta">Updated: ${data.last_updated}</span>
      </div>
      <div class="overview-pipeline">${agentNodes}</div>
      <div class="overview-pipeline-footer">
        All agents invoke <strong>Gemini 2.5 Flash</strong> via Vertex AI
        &nbsp;&middot;&nbsp; Protocols: <strong>UCP</strong> &middot; <strong>BMS</strong> &middot; <strong>AP2</strong>
        &nbsp;&middot;&nbsp; Orchestrated by <strong>Google ADK</strong>
      </div>
    </div>

    ${data.recent && data.recent.length ? `
    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">Recent Requests</span>
        <span class="table-card-meta">Last ${data.recent.length} of ${data.total_requests}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Status</th><th>Request ID</th><th>Description</th><th>Vendor</th><th class="text-right">Amount</th>
          </tr>
        </thead>
        <tbody>${recentRows}</tbody>
      </table>
    </div>` : ""}`;
}

// ── PROCUREMENT: History ──────────────────────────────────────────────────────

function renderHistory(data) {
  addNewRequestBtn();
  const rows = filterRows(data, ["id", "description", "vendor", "status", "category"]);

  const settled = data.filter(r => r.status === "SETTLED").length;
  const blocked = data.filter(r => r.status === "BLOCKED").length;
  const review  = data.filter(r => r.status === "REVIEW").length;

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Request History</div>
      <div class="page-subtitle">All procurement requests submitted through Aura</div>
    </div>

    <div class="stats-row">
      <div class="stat-card teal">
        <div class="stat-value">${data.length}</div>
        <div class="stat-label">Total Requests</div>
      </div>
      <div class="stat-card green">
        <div class="stat-value">${settled}</div>
        <div class="stat-label">Settled</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-value">${review}</div>
        <div class="stat-label">In Review</div>
      </div>
      <div class="stat-card red">
        <div class="stat-value">${blocked}</div>
        <div class="stat-label">Blocked</div>
      </div>
    </div>

    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">Request Executions</span>
        <span class="table-card-meta">Total Rows: ${rows.length}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Request ID</th>
            <th>Description</th>
            <th>Vendor</th>
            <th>Category</th>
            <th class="text-right">Amount</th>
            <th>Settlement ID</th>
            <th>Submitted At</th>
          </tr>
        </thead>
        <tbody>
          ${rows.length === 0 ? `<tr><td colspan="8" class="text-center td-muted" style="padding:30px">No results</td></tr>` : ""}
          ${rows.map(r => `
            <tr>
              <td>${badge(r.status)}</td>
              <td><span class="td-mono">${r.id}</span></td>
              <td>${r.description}</td>
              <td>${r.vendor || "—"}</td>
              <td><span class="td-muted">${r.category}</span></td>
              <td class="text-right td-amount">${usd(r.amount_usd)}</td>
              <td>
                ${r.settlement_id
                  ? `<span class="td-mono">${r.settlement_id}</span>`
                  : `<span class="td-muted">—</span>`}
              </td>
              <td class="td-muted">${r.submitted_at}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

// ── PROCUREMENT: Active Pipelines ─────────────────────────────────────────────

function renderPipelines(data) {
  addNewRequestBtn();
  const agentOrder = ["Architect", "Governor", "Scout", "Sentinel", "Closer"];

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Active Pipelines</div>
      <div class="page-subtitle">Real-time agent pipeline status for in-progress requests</div>
    </div>
    ${data.length === 0
      ? `<div class="empty-state"><div class="empty-icon">✓</div><p>No active pipelines — all requests have completed.</p></div>`
      : `<div class="pipeline-grid">
          ${data.map(p => `
            <div class="pipeline-card">
              <div class="pipeline-card-header">
                <span class="pipeline-req-id">${p.request_id}</span>
                <span class="pipeline-desc">${p.description}</span>
                ${badge("REVIEW")}
              </div>
              <div class="agent-steps">
                ${agentOrder.map((name, i) => {
                  const st = p.agents[name] || "idle";
                  return `<div class="agent-step">
                    <span class="agent-pill ${st}">
                      <span class="badge-dot"></span>${name}
                    </span>
                    ${i < agentOrder.length - 1 ? `<span class="step-arrow">→</span>` : ""}
                  </div>`;
                }).join("")}
              </div>
              <div class="pipeline-stage">Current stage: ${p.current_stage} · Started: ${p.started_at}</div>
            </div>`).join("")}
        </div>`}`;

  startAutoRefresh(3000);
}

// ── PROCUREMENT: Submit page ──────────────────────────────────────────────────

function renderSubmitPage() {
  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">New Request</div>
      <div class="page-subtitle">Submit a natural language procurement request to the Aura agent pipeline</div>
    </div>
    <div class="table-card" style="max-width:620px;padding:24px 24px 20px">
      <div class="page-title" style="font-size:15px;margin-bottom:14px">Describe what you need</div>
      <label class="form-label">Procurement request</label>
      <textarea id="inlineMsg" class="form-textarea" rows="4"
        placeholder="e.g. Buy 5 Laptop Pro 15 from the cheapest compliant vendor"></textarea>
      <div class="form-hint">Aura will discover vendors, run KYC/AML compliance, and settle payment automatically (demo mode).</div>
      <div style="margin-top:14px;display:flex;gap:8px">
        <button class="btn-primary" id="inlineSubmitBtn">Submit Request</button>
        <button class="btn-secondary" onclick="loadView('history')">View History</button>
      </div>
      <div id="submitResult" style="margin-top:14px"></div>
    </div>

    <div class="page-header" style="margin-top:24px">
      <div class="page-title" style="font-size:15px">Quick Demo Scenarios</div>
    </div>
    <div class="stats-row" style="max-width:720px">
      <div class="stat-card" style="cursor:pointer" onclick="fillDemo('Buy 3 Laptop Pro 15 units from best vendor')">
        <div class="stat-label" style="margin-bottom:6px;font-size:12px;color:var(--teal)">HAPPY PATH</div>
        <div class="stat-value" style="font-size:14px;font-weight:600">Buy 3 Laptop Pro 15</div>
        <div class="stat-label">Full settlement · AP2 mandate issued</div>
      </div>
      <div class="stat-card" style="cursor:pointer" onclick="fillDemo('Buy 5 server units from ShadowHardware')">
        <div class="stat-label" style="margin-bottom:6px;font-size:12px;color:var(--red)">BLOCK DEMO</div>
        <div class="stat-value" style="font-size:14px;font-weight:600">Buy from ShadowHardware</div>
        <div class="stat-label">AML blacklist hit · Pipeline blocked</div>
      </div>
      <div class="stat-card" style="cursor:pointer" onclick="fillDemo('Buy AWS cloud hosting 12-month reserved for $4800')">
        <div class="stat-label" style="margin-bottom:6px;font-size:12px;color:var(--yellow)">REVIEW DEMO</div>
        <div class="stat-value" style="font-size:14px;font-weight:600">High-value cloud hosting</div>
        <div class="stat-label">High-value · Finance review required</div>
      </div>
    </div>`;

  document.getElementById("inlineSubmitBtn").addEventListener("click", async () => {
    const msg = document.getElementById("inlineMsg").value.trim();
    if (!msg) return showToast("Please enter a request message", "error");
    await doSubmit(msg, document.getElementById("submitResult"));
  });
}

function fillDemo(text) {
  const ta = document.getElementById("inlineMsg");
  if (ta) ta.value = text;
}

// ── Pipeline card helpers ──────────────────────────────────────────────────────

const AGENT_ORDER = ["Architect", "Governor", "Scout", "Sentinel", "Closer"];
const AGENT_ICONS = {
  Architect: { icon: "🏛️", role: "Procurement Officer" },
  Governor:  { icon: "⚖️",  role: "Finance Controller" },
  Scout:     { icon: "🔭", role: "Category Manager" },
  Sentinel:  { icon: "🛡️", role: "Compliance Officer" },
  Closer:    { icon: "💳", role: "Payment Manager" },
};

function renderPipelineCards(container) {
  container.innerHTML = AGENT_ORDER.map(name => {
    const meta = AGENT_ICONS[name] || { icon: "◈", role: "" };
    return `
    <div class="pipeline-agent-card" id="agent-card-${name}" style="
      display:flex;align-items:center;gap:12px;padding:12px 16px;
      background:var(--surface);border:1px solid var(--border);border-radius:8px;
      margin-bottom:8px;transition:border-color 0.2s,background 0.2s">
      <span style="font-size:20px;width:28px;text-align:center">${meta.icon}</span>
      <div style="flex:1">
        <div style="font-weight:600;font-size:13px">${meta.role}</div>
        <div class="agent-detail" style="font-size:12px;color:var(--text-muted);margin-top:2px">Idle</div>
      </div>
      <span class="agent-badge" style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;
        background:var(--gray-bg);color:var(--text-muted)">IDLE</span>
    </div>`;
  }).join("");
}

function updateAgentCard(container, name, status, detail) {
  const card = container.querySelector(`#agent-card-${name}`);
  if (!card) return;
  const colors = {
    running: { bg: "var(--blue-bg)", border: "var(--blue-border)", badge: "var(--blue)", text: "#fff", label: "RUNNING" },
    done:    { bg: "var(--green-bg)", border: "var(--green-border)", badge: "var(--green)", text: "#fff", label: "DONE" },
    blocked: { bg: "var(--red-bg)", border: "var(--red-border)", badge: "var(--red)", text: "#fff", label: "BLOCKED" },
    idle:    { bg: "var(--surface)", border: "var(--border)", badge: "var(--gray-bg)", text: "var(--text-muted)", label: "IDLE" },
  };
  const c = colors[status] || colors.idle;
  card.style.background = c.bg;
  card.style.borderColor = c.border;
  card.querySelector(".agent-detail").textContent = detail || "";
  const badge = card.querySelector(".agent-badge");
  badge.textContent = c.label;
  badge.style.background = c.badge;
  badge.style.color = c.text;
}

function renderPipelineResult(container, ev) {
  const bestVendor = ev.settlement ? (ev.compliance || []).find(c => c.name === ev.settlement.vendor_name) || {} : null;
  container.insertAdjacentHTML("beforeend", `
    <div style="margin-top:16px;background:var(--green-bg);border:1px solid var(--green-border);border-radius:8px;padding:16px">
      <div style="color:var(--green);font-weight:700;font-size:14px;margin-bottom:10px">✓ Procurement Complete — ${ev.settlement?.settlement_id || ""}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px">
        <div><span style="color:var(--text-muted)">Vendor:</span> <strong>${ev.settlement?.vendor_name || "—"}</strong></div>
        <div><span style="color:var(--text-muted)">Amount:</span> <strong>${ev.settlement?.amount_usd != null ? "$" + ev.settlement.amount_usd.toLocaleString() : "—"}</strong></div>
        <div><span style="color:var(--text-muted)">Status:</span> <strong>${ev.settlement?.status || "—"}</strong></div>
        <div><span style="color:var(--text-muted)">Compliance:</span> <strong>${(ev.compliance || []).filter(c => c.status === "APPROVED").length} / ${(ev.compliance || []).length} cleared</strong></div>
      </div>
    </div>`);
}

function renderPipelineBlocked(container, ev) {
  container.insertAdjacentHTML("beforeend", `
    <div style="margin-top:16px;background:var(--red-bg);border:1px solid var(--red-border);border-radius:8px;padding:16px">
      <div style="color:var(--red);font-weight:700;font-size:14px;margin-bottom:6px">🚫 Pipeline Blocked — Compliance Failure</div>
      <div style="font-size:13px"><span style="color:var(--text-muted)">Vendor:</span> <strong>${ev.vendor}</strong></div>
      <div style="font-size:13px;margin-top:4px"><span style="color:var(--text-muted)">Reason:</span> ${ev.reason}</div>
      <div style="font-size:12px;margin-top:8px;color:var(--text-muted)">No payment has been initiated. Transaction aborted by Sentinel.</div>
    </div>`);
}

async function doSubmit(message, resultEl) {
  // Detect live vs demo mode
  let geminiAvailable = false;
  try {
    const cap = await fetch("/api/portal/capabilities");
    if (cap.ok) { const d = await cap.json(); geminiAvailable = d.gemini_available; }
  } catch (_) { /* default to demo */ }

  if (geminiAvailable) {
    // ── Live mode: POST /run ────────────────────────────────────────────────
    resultEl.innerHTML = `<div class="loading-state" style="padding:16px 0"><div class="spinner"></div><p>Running live agent pipeline…</p></div>`;
    try {
      const res = await fetch("/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      resultEl.innerHTML = `
        <div style="background:var(--green-bg);border:1px solid var(--green-border);border-radius:8px;padding:14px 16px">
          <div style="color:var(--green);font-weight:700;margin-bottom:6px">✓ Live Pipeline Complete</div>
          <div style="font-size:13px;white-space:pre-wrap">${data.response || JSON.stringify(data, null, 2)}</div>
        </div>`;
      showToast("Pipeline completed", "success");
    } catch (e) {
      resultEl.innerHTML = `<div style="color:var(--red);font-size:13px">Error: ${e.message}</div>`;
    }
    return;
  }

  // ── Demo mode: SSE /api/portal/run/demo ─────────────────────────────────
  resultEl.innerHTML = `<div style="margin-bottom:8px;font-size:12px;color:var(--text-muted)">Demo mode — streaming agent pipeline</div>`;
  const cardsWrap = document.createElement("div");
  resultEl.appendChild(cardsWrap);
  renderPipelineCards(cardsWrap);

  try {
    const res = await fetch("/api/portal/run/demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop(); // keep incomplete line
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        let ev;
        try { ev = JSON.parse(line.slice(6)); } catch (_) { continue; }
        if (ev.type === "agent") {
          updateAgentCard(cardsWrap, ev.name, ev.status, ev.detail);
        } else if (ev.type === "result") {
          renderPipelineResult(resultEl, ev);
          showToast("Pipeline completed successfully", "success");
        } else if (ev.type === "blocked") {
          renderPipelineBlocked(resultEl, ev);
          showToast("Pipeline blocked — compliance failure", "error");
        }
      }
    }
  } catch (e) {
    resultEl.innerHTML += `<div style="color:var(--red);font-size:13px;margin-top:8px">Stream error: ${e.message}</div>`;
  }
}

// ── FINANCE: Pending approvals ─────────────────────────────────────────────────

function renderPending(data) {
  const pending = filterRows(data.filter(r => r.status === "PENDING"), ["id", "description", "vendor"]);
  const totalAmt = pending.reduce((s, r) => s + r.amount_usd, 0);

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Pending Approvals</div>
      <div class="page-subtitle">High-value transactions (> $4,000) awaiting finance approval</div>
    </div>
    <div class="stats-row">
      <div class="stat-card yellow">
        <div class="stat-value">${pending.length}</div>
        <div class="stat-label">Awaiting Approval</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${usd(totalAmt)}</div>
        <div class="stat-label">Total Exposure</div>
      </div>
    </div>
    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">Approval Queue</span>
        <span class="table-card-meta">Total Rows: ${pending.length}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Request ID</th>
            <th>Description</th>
            <th>Vendor</th>
            <th>Submitted By</th>
            <th class="text-right">Amount</th>
            <th>Submitted At</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${pending.length === 0 ? `<tr><td colspan="8" class="text-center td-muted" style="padding:30px">No pending approvals</td></tr>` : ""}
          ${pending.map(r => `
            <tr id="row-${r.id}">
              <td>${badge(r.status)}</td>
              <td><span class="td-mono">${r.id}</span></td>
              <td>${r.description}</td>
              <td>${r.vendor}</td>
              <td class="td-muted">${r.submitted_by}</td>
              <td class="text-right td-amount">${usd(r.amount_usd)}</td>
              <td class="td-muted">${r.submitted_at}</td>
              <td>
                <div class="row-gap">
                  <button class="btn-approve" onclick="financeAction('${r.id}', 'approve')">Approve</button>
                  <button class="btn-reject"  onclick="financeAction('${r.id}', 'reject')">Reject</button>
                </div>
              </td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

async function financeAction(id, action) {
  try {
    const url = `/api/portal/finance/${action}/${id}`;
    const res = await fetch(url, { method: "POST" });
    const data = await res.json();

    const row = document.getElementById(`row-${id}`);
    if (row) {
      const statusCell = row.querySelector("td:first-child");
      const actionsCell = row.querySelector("td:last-child");
      if (statusCell) statusCell.innerHTML = badge(data.status);
      if (actionsCell) actionsCell.innerHTML = `<span class="td-muted">–</span>`;
    }
    showToast(`${id} ${action === "approve" ? "approved" : "rejected"}`, "success");
  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
}

// ── FINANCE: Approval history ─────────────────────────────────────────────────

function renderApprovalHistory(data) {
  const done = filterRows(data.filter(r => r.status !== "PENDING"), ["id", "description", "vendor", "status"]);

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Approval History</div>
      <div class="page-subtitle">Previously reviewed high-value transactions</div>
    </div>
    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">Resolved Items</span>
        <span class="table-card-meta">Total Rows: ${done.length}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Request ID</th>
            <th>Description</th>
            <th>Vendor</th>
            <th class="text-right">Amount</th>
            <th>Submitted By</th>
            <th>Submitted At</th>
          </tr>
        </thead>
        <tbody>
          ${done.length === 0 ? `<tr><td colspan="7" class="text-center td-muted" style="padding:30px">No resolved items yet</td></tr>` : ""}
          ${done.map(r => `
            <tr>
              <td>${badge(r.status)}</td>
              <td><span class="td-mono">${r.id}</span></td>
              <td>${r.description}</td>
              <td>${r.vendor}</td>
              <td class="text-right td-amount">${usd(r.amount_usd)}</td>
              <td class="td-muted">${r.submitted_by}</td>
              <td class="td-muted">${r.submitted_at}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

// ── COMPLIANCE: Live Events ────────────────────────────────────────────────────

function renderEvents(data) {
  const rows = filterRows(data, ["vendor", "event_type", "reason", "request_id"]);

  toolbarActions.innerHTML = `<span style="font-size:12px;color:var(--text-muted)">↻ Auto-refresh every 5s</span>`;

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Live Compliance Events</div>
      <div class="page-subtitle">Real-time KYC/AML event feed from the Sentinel agent</div>
    </div>
    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">Event Log</span>
        <span class="table-card-meta">Total Rows: ${rows.length}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Event ID</th>
            <th>Event Type</th>
            <th>Vendor</th>
            <th>Country</th>
            <th>Severity</th>
            <th>Reason</th>
            <th>Compliance Hash</th>
            <th>Request ID</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(e => `
            <tr>
              <td>${badge(e.status)}</td>
              <td><span class="td-mono">${e.id}</span></td>
              <td><span class="td-muted">${e.event_type}</span></td>
              <td><strong>${e.vendor}</strong></td>
              <td><span class="td-mono">${e.vendor_country}</span></td>
              <td><span class="severity-${(e.severity||"").toLowerCase()}">${e.severity}</span></td>
              <td style="max-width:280px;word-break:break-word">${e.reason}</td>
              <td><span class="hash-cell" title="${e.compliance_hash}">${e.compliance_hash}</span></td>
              <td><span class="td-mono">${e.request_id}</span></td>
              <td class="td-muted">${e.timestamp}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

// ── COMPLIANCE: Blocked Vendors ───────────────────────────────────────────────

function renderBlocked(data) {
  const rows = filterRows(data, ["vendor", "country", "reason", "block_type"]);

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Blocked Vendors</div>
      <div class="page-subtitle">Vendors permanently blocked by AML blacklist or country sanction</div>
    </div>
    <div class="stats-row">
      <div class="stat-card red">
        <div class="stat-value">${data.length}</div>
        <div class="stat-label">Blocked Vendors</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${data.reduce((s,v) => s + v.request_count, 0)}</div>
        <div class="stat-label">Total Attempts</div>
      </div>
    </div>
    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">Block List</span>
        <span class="table-card-meta">Total Rows: ${rows.length}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Block Type</th>
            <th>Vendor</th>
            <th>Country</th>
            <th>Reason</th>
            <th>Attempts</th>
            <th>Blocked Since</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(v => `
            <tr>
              <td>${badge("blocked")}</td>
              <td><strong>${v.vendor}</strong></td>
              <td><span class="td-mono">${v.country}</span></td>
              <td>${v.reason}</td>
              <td class="text-center">${v.request_count}</td>
              <td class="td-muted">${v.blocked_at}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

// ── COMPLIANCE: Statistics ─────────────────────────────────────────────────────

function renderComplianceStats(stats, events, blocked) {
  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Compliance Statistics</div>
      <div class="page-subtitle">Aggregated KYC/AML pass/fail metrics</div>
    </div>
    <div class="stats-row">
      <div class="stat-card teal">
        <div class="stat-value">${stats.total_checks}</div>
        <div class="stat-label">Total Checks</div>
      </div>
      <div class="stat-card green">
        <div class="stat-value">${stats.approved}</div>
        <div class="stat-label">Approved (${stats.approval_rate_pct}%)</div>
      </div>
      <div class="stat-card red">
        <div class="stat-value">${stats.blocked}</div>
        <div class="stat-label">Blocked (${stats.block_rate_pct}%)</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-value">${stats.review}</div>
        <div class="stat-label">In Review</div>
      </div>
    </div>

    <div class="table-card" style="max-width:440px;margin-bottom:18px">
      <div class="table-card-header"><span class="table-card-title">Pass Rate</span></div>
      <div style="padding:16px 18px">
        <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-muted);margin-bottom:6px">
          <span>Approved</span><span>${stats.approval_rate_pct}%</span>
        </div>
        <div style="height:10px;background:var(--surface-2);border-radius:5px;border:1px solid var(--border);overflow:hidden">
          <div style="height:100%;width:${stats.approval_rate_pct}%;background:var(--teal);border-radius:5px"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-muted);margin-top:10px;margin-bottom:6px">
          <span>Blocked</span><span>${stats.block_rate_pct}%</span>
        </div>
        <div style="height:10px;background:var(--surface-2);border-radius:5px;border:1px solid var(--border);overflow:hidden">
          <div style="height:100%;width:${stats.block_rate_pct}%;background:var(--red);border-radius:5px"></div>
        </div>
      </div>
    </div>

    <div class="table-card" style="max-width:440px">
      <div class="table-card-header"><span class="table-card-title">Blocked Vendor Summary</span></div>
      <table>
        <thead><tr><th>Vendor</th><th>Country</th><th>Block Type</th></tr></thead>
        <tbody>
          ${blocked.map(v => `
            <tr>
              <td><strong>${v.vendor}</strong></td>
              <td><span class="td-mono">${v.country}</span></td>
              <td>${badge("blocked")}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

// ── IT MANAGER: Vendor Catalog ────────────────────────────────────────────────

function renderVendors(data) {
  const rows = filterRows(data, ["name", "capability", "country", "compliance_status"]);

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Vendor Catalog</div>
      <div class="page-subtitle">UCP-discovered vendors and their compliance status</div>
    </div>
    <div class="stats-row">
      <div class="stat-card teal">
        <div class="stat-value">${data.length}</div>
        <div class="stat-label">Total Vendors</div>
      </div>
      <div class="stat-card green">
        <div class="stat-value">${data.filter(v => v.compliance_status === "APPROVED").length}</div>
        <div class="stat-label">Compliant</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-value">${data.filter(v => v.compliance_status === "REVIEW").length}</div>
        <div class="stat-label">Under Review</div>
      </div>
    </div>
    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">Vendor Directory</span>
        <span class="table-card-meta">Total Rows: ${rows.length}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Compliance</th>
            <th>Vendor ID</th>
            <th>Vendor Name</th>
            <th>Capability</th>
            <th>Products</th>
            <th>Country</th>
            <th class="text-right">Unit Price</th>
            <th class="text-right">Available Units</th>
            <th>Last Checked</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(v => `
            <tr>
              <td>${badge(v.compliance_status)}</td>
              <td><span class="td-mono">${v.id}</span></td>
              <td><strong>${v.name}</strong></td>
              <td><span class="td-muted">${v.capability}</span></td>
              <td style="max-width:200px;font-size:12px;color:var(--text-muted)">${v.products.join(", ")}</td>
              <td><span class="td-mono">${v.country}</span></td>
              <td class="text-right td-amount">${usd(v.unit_price_usd)}</td>
              <td class="text-right">${v.available_units}</td>
              <td class="td-muted">${v.last_checked}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

// ── IT MANAGER: Contracts ─────────────────────────────────────────────────────

function renderContracts(data) {
  const rows = filterRows(data, ["id", "type", "vendor", "description", "status"]);

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Active Contracts</div>
      <div class="page-subtitle">SSA (Statens Standardavtaler) contracts by type</div>
    </div>
    <div class="stats-row">
      <div class="stat-card teal">
        <div class="stat-value">${data.length}</div>
        <div class="stat-label">Total Contracts</div>
      </div>
      <div class="stat-card green">
        <div class="stat-value">${data.filter(c => c.status === "ACTIVE").length}</div>
        <div class="stat-label">Active</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-value">${data.filter(c => c.status === "PENDING_APPROVAL").length}</div>
        <div class="stat-label">Pending Approval</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${usd(data.reduce((s, c) => s + c.amount_usd, 0))}</div>
        <div class="stat-label">Total Value</div>
      </div>
    </div>
    <div class="contract-grid">
      ${rows.map(c => `
        <div class="contract-card">
          <div class="contract-type-badge">${c.type}</div>
          ${badge(c.status)}
          <div class="contract-title" style="margin-top:8px">${c.description}</div>
          <div class="contract-vendor">${c.type_label} · ${c.vendor}</div>
          <div class="contract-amount">${usd(c.amount_usd)}</div>
          <div class="contract-period">${c.start_date} → ${c.end_date}</div>
          <div class="contract-footer">
            <span class="td-muted font-mono">${c.id}</span>
            ${c.auto_renew ? `<span class="auto-renew-tag">↻ Auto-renew</span>` : ""}
          </div>
        </div>`).join("")}
    </div>`;
}

// ── ADMIN: System Metrics ─────────────────────────────────────────────────────

function renderMetrics(data) {
  toolbarActions.innerHTML = `<span style="font-size:12px;color:var(--text-muted)">↻ Auto-refresh every 10s</span>`;
  const agents = data.agents || {};
  const maxInvocations = Math.max(...Object.values(agents).map(a => a.invocations), 1);

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">System Metrics</div>
      <div class="page-subtitle">Live Aura agent pipeline performance · Updated: ${data.last_updated}</div>
    </div>
    <div class="stats-row">
      <div class="stat-card teal">
        <div class="stat-value">${data.total_requests}</div>
        <div class="stat-label">Total Requests</div>
      </div>
      <div class="stat-card green">
        <div class="stat-value">${data.settled}</div>
        <div class="stat-label">Settled</div>
      </div>
      <div class="stat-card red">
        <div class="stat-value">${data.blocked}</div>
        <div class="stat-label">Blocked</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-value">${data.review}</div>
        <div class="stat-label">In Review</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${data.avg_latency_ms.toLocaleString()} ms</div>
        <div class="stat-label">Avg Pipeline Latency</div>
      </div>
    </div>

    <div class="metrics-section">
      <div class="metrics-section-title">Agent Performance</div>
      <div class="agent-metrics-grid">
        ${Object.entries(agents).map(([name, a]) => `
          <div class="agent-metric-row">
            <div class="agent-metric-name">${name}</div>
            <div class="agent-metric-bar-wrap">
              <div class="agent-metric-bar" style="width:${Math.round(a.invocations / maxInvocations * 100)}%"></div>
            </div>
            <div class="agent-metric-stats">
              <div class="agent-metric-stat">
                <div class="agent-metric-stat-val">${a.invocations}</div>
                <div class="agent-metric-stat-lbl">Invocations</div>
              </div>
              <div class="agent-metric-stat">
                <div class="agent-metric-stat-val" style="color:${a.errors > 0 ? 'var(--red)' : 'var(--green)'}">
                  ${a.errors}
                </div>
                <div class="agent-metric-stat-lbl">Errors</div>
              </div>
              <div class="agent-metric-stat">
                <div class="agent-metric-stat-val">${a.avg_ms} ms</div>
                <div class="agent-metric-stat-lbl">Avg Latency</div>
              </div>
            </div>
          </div>`).join("")}
      </div>
    </div>`;
}

// ── ADMIN: Policies ───────────────────────────────────────────────────────────

function renderPolicies(data) {
  const rows = filterRows(data, ["id", "name", "rule_type", "description"]);

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Policy Rules</div>
      <div class="page-subtitle">Active procurement, payment, and compliance policies</div>
    </div>
    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">Policy Configuration</span>
        <span class="table-card-meta">Total Rows: ${rows.length}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Enabled</th>
            <th>Policy ID</th>
            <th>Name</th>
            <th>Rule Type</th>
            <th>Severity</th>
            <th>Parameters</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(p => `
            <tr>
              <td>
                <span class="badge ${p.enabled ? 'badge-active' : 'badge-blocked'}">
                  <span class="badge-dot"></span>${p.enabled ? "ENABLED" : "DISABLED"}
                </span>
              </td>
              <td><span class="td-mono">${p.id}</span></td>
              <td><strong>${p.name}</strong></td>
              <td><span class="td-muted">${p.rule_type}</span></td>
              <td><span class="severity-${(p.severity||"").toLowerCase()}">${p.severity}</span></td>
              <td><span class="hash-cell" title="${JSON.stringify(p.parameters)}">${JSON.stringify(p.parameters)}</span></td>
              <td style="max-width:280px">${p.description}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

// ── ADMIN: Review Queue ───────────────────────────────────────────────────────

function renderAdminQueue(data) {
  const rows = filterRows(data, ["id", "description", "vendor", "status"]);

  viewEl.innerHTML = `
    <div class="page-header">
      <div class="page-title">Review Queue</div>
      <div class="page-subtitle">Transactions flagged by policy rules and awaiting resolution</div>
    </div>
    <div class="stats-row">
      <div class="stat-card yellow">
        <div class="stat-value">${rows.filter(r => r.status === "PENDING").length}</div>
        <div class="stat-label">Pending</div>
      </div>
      <div class="stat-card teal">
        <div class="stat-value">${rows.length}</div>
        <div class="stat-label">Total in Queue</div>
      </div>
    </div>
    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">Review Items</span>
        <span class="table-card-meta">Total Rows: ${rows.length}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Request ID</th>
            <th>Description</th>
            <th>Vendor</th>
            <th>Submitted By</th>
            <th class="text-right">Amount</th>
            <th>Policy</th>
            <th>Submitted At</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${rows.length === 0 ? `<tr><td colspan="9" class="text-center td-muted" style="padding:30px">Queue is empty</td></tr>` : ""}
          ${rows.map(r => `
            <tr id="qrow-${r.id}">
              <td>${badge(r.status)}</td>
              <td><span class="td-mono">${r.id}</span></td>
              <td>${r.description}</td>
              <td>${r.vendor}</td>
              <td class="td-muted">${r.submitted_by}</td>
              <td class="text-right td-amount">${usd(r.amount_usd)}</td>
              <td><span class="td-mono">${r.policy_id}</span></td>
              <td class="td-muted">${r.submitted_at}</td>
              <td>
                ${r.status === "PENDING"
                  ? `<div class="row-gap">
                      <button class="btn-approve" onclick="adminQueueAction('${r.id}', 'approve')">Approve</button>
                      <button class="btn-reject" onclick="adminQueueAction('${r.id}', 'reject')">Reject</button>
                    </div>`
                  : `<span class="td-muted">–</span>`}
              </td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

async function adminQueueAction(id, action) {
  try {
    const res = await fetch(`/api/portal/admin/review-queue/resolve/${id}?action=${action}`, { method: "POST" });
    const data = await res.json();
    const row = document.getElementById(`qrow-${id}`);
    if (row) {
      row.querySelector("td:first-child").innerHTML = badge(data.status);
      row.querySelector("td:last-child").innerHTML = `<span class="td-muted">–</span>`;
    }
    showToast(`${id} ${action === "approve" ? "approved" : "rejected"}`, "success");
  } catch (e) {
    showToast(`Error: ${e.message}`, "error");
  }
}

// ── Modal ─────────────────────────────────────────────────────────────────────

function openModal() {
  submitModal.style.display = "flex";
  document.getElementById("submitMsg").value = "";
}

function closeModal() {
  submitModal.style.display = "none";
}

async function submitRequest() {
  const msg = document.getElementById("submitMsg").value.trim();
  if (!msg) return showToast("Please enter a request message", "error");
  closeModal();
  // Navigate to submit view and trigger
  loadView("submit");
  setTimeout(() => {
    const ta = document.getElementById("inlineMsg");
    if (ta) { ta.value = msg; document.getElementById("inlineSubmitBtn").click(); }
  }, 100);
}

// ── Toast ──────────────────────────────────────────────────────────────────────

function showToast(msg, type = "") {
  let toast = document.getElementById("aura-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "aura-toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  requestAnimationFrame(() => toast.classList.add("show"));
  setTimeout(() => toast.classList.remove("show"), 3000);
}
