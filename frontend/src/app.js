/**
 * Debug Logger — Client-Side Application Logic
 * Handles navigation, API calls, form submission, dashboard rendering, and detail view.
 */

(function () {
  "use strict";

  // ── API base (empty string = same origin, Nginx proxies /api/ to backend) ──
  // Use absolute URL for local dev server on port 3000, otherwise use relative path
  const API = window.location.port === "3000" ? "http://localhost:8000" : "";

  // ── DOM refs ──
  const $  = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);

  const views = {
    dashboard: $("#view-dashboard"),
    form:      $("#view-form"),
    detail:    $("#view-detail"),
  };

  const navBtns       = $$(".nav-btn");
  const logsGrid      = $("#logs-grid");
  const emptyState    = $("#empty-state");
  const filterInput   = $("#input-filter-tag");
  const btnFilter     = $("#btn-filter");
  const btnClearFilter= $("#btn-clear-filter");
  const logForm       = $("#log-form");
  const btnBack       = $("#btn-back");
  const toast         = $("#toast");

  // ── Navigation ──
  function showView(name) {
    Object.values(views).forEach((v) => v.classList.remove("active"));
    navBtns.forEach((b) => b.classList.remove("active"));
    views[name].classList.add("active");
    const activeBtn = $(`[data-view="${name}"]`);
    if (activeBtn) activeBtn.classList.add("active");
  }

  navBtns.forEach((btn) => {
    btn.addEventListener("click", () => showView(btn.dataset.view));
  });

  btnBack.addEventListener("click", () => showView("dashboard"));

  // ── Toast helper ──
  let toastTimer;
  function showToast(msg, isError) {
    toast.textContent = msg;
    toast.className = "toast" + (isError ? " error" : "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.add("hidden"), 3000);
  }

  // ── API helpers ──
  async function apiGet(path) {
    const res = await fetch(API + path);
    if (!res.ok) throw new Error(res.statusText);
    return res.json();
  }

  async function apiPost(path, body) {
    const res = await fetch(API + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || res.statusText);
    }
    return res.json();
  }

  // ── Render helpers ──
  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
  }

  function formatDate(iso) {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      year: "numeric", month: "short", day: "numeric",
    });
  }

  function renderTags(csv) {
    if (!csv) return "";
    return csv.split(",").map((t) => t.trim()).filter(Boolean)
      .map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("");
  }

  function renderCard(log) {
    const card = document.createElement("div");
    card.className = "log-card";
    card.dataset.id = log.id;
    card.innerHTML = `
      <h3>${escapeHtml(log.title)}</h3>
      <div class="card-preview">${escapeHtml(log.anti_pattern)}</div>
      <div class="card-meta">
        <div class="tag-list">${renderTags(log.tags)}</div>
        <span class="card-date">${formatDate(log.created_at)}</span>
      </div>`;
    card.addEventListener("click", () => openDetail(log));
    return card;
  }

  // ── Dashboard ──
  async function loadLogs(tag) {
    try {
      const url = tag ? `/api/logs?tag=${encodeURIComponent(tag)}` : "/api/logs";
      const logs = await apiGet(url);
      logsGrid.innerHTML = "";
      if (logs.length === 0) {
        emptyState.classList.remove("hidden");
      } else {
        emptyState.classList.add("hidden");
        logs.forEach((l) => logsGrid.appendChild(renderCard(l)));
      }
    } catch (e) {
      showToast("Failed to load logs: " + e.message, true);
    }
  }

  btnFilter.addEventListener("click", () => {
    loadLogs(filterInput.value.trim());
  });

  filterInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadLogs(filterInput.value.trim());
  });

  btnClearFilter.addEventListener("click", () => {
    filterInput.value = "";
    loadLogs();
  });

  // ── Detail View ──
  function openDetail(log) {
    $("#detail-title").textContent = log.title;
    $("#detail-tags").innerHTML = renderTags(log.tags);
    $("#detail-date").textContent = formatDate(log.created_at);
    $("#detail-anti-pattern").textContent = log.anti_pattern;
    $("#detail-working-code").textContent = log.working_code;
    $("#detail-root-cause").textContent = log.root_cause;
    showView("detail");
  }

  // ── Form Submission ──
  logForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      title:        $("#input-title").value.trim(),
      anti_pattern: $("#input-anti-pattern").value,
      working_code: $("#input-working-code").value,
      root_cause:   $("#input-root-cause").value.trim(),
      tags:         $("#input-tags").value.trim(),
    };

    try {
      await apiPost("/api/logs", payload);
      showToast("Log saved successfully!");
      logForm.reset();
      showView("dashboard");
      loadLogs();
    } catch (err) {
      showToast("Error: " + err.message, true);
    }
  });

  // ── Init ──
  loadLogs();
})();
