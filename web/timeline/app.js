/* Clean hero timeline + isolated data zone (English UI) */

(function () {
  const data = window.ARXIVCOUNT_DATA;
  if (!data) {
    document.body.innerHTML =
      '<p style="color:#ccc;padding:2rem;font-family:sans-serif">Missing data.js — run: python -m src.export_web</p>';
    return;
  }

  const nav = data.navigable || [];
  let idx = Math.max(
    0,
    nav.findIndex(
      (e) =>
        e.type === "canon_milestone" &&
        (e.id === "chatgpt" || (e.label || "").includes("ChatGPT"))
    )
  );
  if (idx < 0) idx = 0;

  const $ = (id) => document.getElementById(id);

  const ICONS = {
    model: `<svg viewBox="0 0 24 24" fill="none" stroke="#6ea8ff" stroke-width="1.7"><rect x="4" y="5" width="16" height="12" rx="2"/><path d="M8 19h8M12 17v2"/><circle cx="9" cy="11" r="1" fill="#6ea8ff"/><circle cx="15" cy="11" r="1" fill="#6ea8ff"/></svg>`,
    system: `<svg viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="1.7"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/></svg>`,
    result: `<svg viewBox="0 0 24 24" fill="none" stroke="#e8b84a" stroke-width="1.7"><path d="M12 3l2.4 4.9 5.4.8-3.9 3.8.9 5.4L12 15.9 7.2 18l.9-5.4L4.2 8.7l5.4-.8L12 3z"/></svg>`,
    trend: `<svg viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="1.7"><path d="M4 18V6M4 18h16"/><path d="M7 14l4-4 3 3 5-6"/></svg>`,
    paper: `<svg viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.7"><path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></svg>`,
    policy: `<svg viewBox="0 0 24 24" fill="none" stroke="#fb7185" stroke-width="1.7"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg>`,
  };

  function iconFor(e) {
    if (e.type === "canon_milestone") {
      return ICONS[e.kind] || ICONS.system;
    }
    if (e.contribution_tier === "C4" || e.open_problem) return ICONS.result;
    return ICONS.paper;
  }

  function fmtDate(d) {
    if (!d) return "—";
    const s = String(d).slice(0, 10);
    const [y, m, day] = s.split("-");
    if (!m) return s;
    return `${y} · ${m}-${day || "01"}`;
  }

  function kindLabel(e) {
    if (e.type === "canon_milestone") {
      const map = {
        model: "Model",
        system: "System",
        result: "Result",
        trend: "Trend",
        policy: "Policy",
        community: "Community",
      };
      return map[e.kind] || "Milestone";
    }
    return e.contribution_tier || "Paper";
  }

  function renderFocus() {
    const e = nav[idx] || {};
    const card = $("focusCard");
    card.style.animation = "none";
    void card.offsetWidth;
    card.style.animation = "";

    $("focusIcon").innerHTML = iconFor(e);
    $("focusKind").textContent = kindLabel(e);
    $("focusDate").textContent = fmtDate(e.date);
    $("focusTitle").textContent = e.label || e.title || e.id || "—";
    $("focusNote").textContent =
      e.note || e.open_problem_name || e.ai_role_summary || "No summary available.";

    const tags = [];
    if (e.type === "canon_milestone") tags.push(["", "canon"]);
    if (e.contribution_tier === "C4") tags.push(["hot", "C4 decisive"]);
    if (e.contribution_tier === "C3") tags.push(["ok", "C3 material"]);
    if (e.open_problem) tags.push(["hot", "open problem"]);
    if (e.phase) tags.push(["", e.phase]);
    if (Array.isArray(e.subfields)) {
      e.subfields.slice(0, 2).forEach((s) => tags.push(["", s]));
    }
    $("focusTags").innerHTML = tags
      .map(([cls, t]) => `<span class="tag ${cls}">${t}</span>`)
      .join("");

    const link = $("focusLink");
    if (e.url) {
      link.href = e.url;
      link.style.visibility = "visible";
      link.textContent = e.arxiv_id ? `arXiv ${e.arxiv_id}` : "Open source";
    } else {
      link.removeAttribute("href");
      link.style.visibility = "hidden";
    }

    $("progressPill").textContent = `${idx + 1} / ${nav.length}`;
    $("btnPrev").disabled = idx <= 0;
    $("btnNext").disabled = idx >= nav.length - 1;

    document.querySelectorAll(".tick").forEach((el, i) => {
      el.classList.toggle("active", i === idx);
    });
    const active = document.querySelector(".tick.active");
    if (active) {
      active.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
    }
  }

  function renderScrub() {
    const track = $("scrubTrack");
    track.innerHTML = nav
      .map((e, i) => {
        const cls = ["tick"];
        if (e.type === "canon_milestone") cls.push("canon");
        if (e.contribution_tier === "C4") cls.push("c4");
        if (i === idx) cls.push("active");
        const tip = (e.label || e.id || "").toString().replace(/"/g, "&quot;");
        return `<button type="button" class="${cls.join(" ")}" data-i="${i}" aria-label="${tip}">
          <span class="tip">${fmtDate(e.date)} · ${tip.length > 36 ? tip.slice(0, 34) + "…" : tip}</span>
        </button>`;
      })
      .join("");
    track.querySelectorAll(".tick").forEach((el) => {
      el.addEventListener("click", () => {
        idx = Number(el.dataset.i);
        renderFocus();
      });
    });
  }

  function renderMetrics() {
    const c = data.contribution || {};
    const p = data.penetration || {};
    const latest = p.latest || {};
    const items = [
      { k: "Wide C2+", v: c.wide_n ?? "—", h: "ecosystem (incl. assistive)" },
      { k: "Strict C3+", v: c.strict_n ?? "—", h: "material impact claims" },
      {
        k: "Strict / 10k",
        v: latest.strict_per_10k != null ? Number(latest.strict_per_10k).toFixed(1) : "—",
        h: latest.year ? `${latest.year} math.*` : "run denominator",
      },
      { k: "Timeline events", v: nav.length, h: "browse with ← →" },
    ];
    $("metricRow").innerHTML = items
      .map(
        (r) =>
          `<div class="metric"><div class="k">${r.k}</div><div class="v">${r.v}</div><div class="h">${r.h}</div></div>`
      )
      .join("");
  }

  function renderCharts() {
    const c = data.contribution || {};
    const years = Array.from(
      new Set([
        ...Object.keys(c.yearly_wide || {}),
        ...Object.keys(c.yearly_strict || {}),
      ])
    ).sort();

    const box = $("chartCounts");
    if (!years.length) {
      box.innerHTML = `<p class="legend">No contribution yearly data yet.</p>`;
    } else {
      const max = Math.max(
        ...years.map((y) =>
          Math.max(
            Number((c.yearly_wide || {})[y] || 0),
            Number((c.yearly_strict || {})[y] || 0)
          )
        ),
        1
      );
      box.innerHTML = years
        .map((y) => {
          const w = Number((c.yearly_wide || {})[y] || 0);
          const s = Number((c.yearly_strict || {})[y] || 0);
          const ww = Math.max(w ? 4 : 0, Math.round((w / max) * 100));
          const sw = Math.max(s ? 4 : 0, Math.round((s / max) * 100));
          return `
            <div class="bar-row"><div>${y}</div>
              <div class="bar-track"><div class="bar-fill wide" style="width:${ww}%"></div></div>
              <div>${w}</div></div>
            <div class="bar-row"><div></div>
              <div class="bar-track"><div class="bar-fill strict" style="width:${sw}%"></div></div>
              <div style="color:#e8b84a">${s}</div></div>`;
        })
        .join("");
    }

    const penYears = (data.penetration && data.penetration.years) || [];
    const penBox = $("chartPen");
    if (!penYears.length) {
      penBox.innerHTML = `<p class="legend">Run: python -m src.denominator</p>`;
    } else {
      const show = penYears.filter((r) => r.year >= 2022);
      const max = Math.max(...show.map((r) => Number(r.strict_per_10k || 0)), 0.01);
      penBox.innerHTML = show
        .map((r) => {
          const v = Number(r.strict_per_10k || 0);
          const w = Math.max(v ? 4 : 0, Math.round((v / max) * 100));
          return `<div class="bar-row"><div>${r.year}</div>
            <div class="bar-track"><div class="bar-fill strict" style="width:${w}%"></div></div>
            <div>${v.toFixed(1)}</div></div>`;
        })
        .join("");
      $("penFoot").textContent =
        "Per 10k = strict / math_total × 10000. 2026 is a partial year. Disclosed-proxy lower bound.";
    }
  }

  function renderPhases() {
    const phases = data.phases || [];
    $("phaseGrid").innerHTML = phases
      .map((ph) => {
        return `<div class="phase-item">
          <div>
            <strong>${ph.label || ph.id}</strong><br/>
            <span>${ph.start} → ${ph.end}</span>
          </div>
          <div class="n">${ph.strict_like ?? 0} strict</div>
        </div>`;
      })
      .join("");
  }

  function renderFoot() {
    const proj = data.project || {};
    const bits = [];
    if (proj.github) bits.push(`<a href="${proj.github}" target="_blank" rel="noopener">GitHub</a>`);
    if (proj.website) bits.push(`<a href="${proj.website}" target="_blank" rel="noopener">Website</a>`);
    bits.push(`Generated ${(data.generated_at || "").slice(0, 19)}`);
    $("dataFoot").innerHTML = bits.join(" · ");
  }

  function go(d) {
    idx = Math.min(nav.length - 1, Math.max(0, idx + d));
    renderFocus();
  }

  $("btnPrev").addEventListener("click", () => go(-1));
  $("btnNext").addEventListener("click", () => go(1));
  window.addEventListener("keydown", (ev) => {
    if (ev.key === "ArrowLeft") go(-1);
    if (ev.key === "ArrowRight") go(1);
  });

  let tx = null;
  $("focusCard").addEventListener(
    "touchstart",
    (e) => {
      tx = e.changedTouches[0].screenX;
    },
    { passive: true }
  );
  $("focusCard").addEventListener(
    "touchend",
    (e) => {
      if (tx == null) return;
      const dx = e.changedTouches[0].screenX - tx;
      if (Math.abs(dx) > 45) go(dx < 0 ? 1 : -1);
      tx = null;
    },
    { passive: true }
  );

  renderScrub();
  renderFocus();
  renderMetrics();
  renderCharts();
  renderPhases();
  renderFoot();
})();
