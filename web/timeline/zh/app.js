/* Chinese UI — same interaction as English timeline */

(function () {
  const raw = window.ARXIVCOUNT_DATA;
  if (!raw) {
    document.body.innerHTML =
      '<p style="color:#ccc;padding:2rem;font-family:sans-serif">缺少 data.js — 请运行: python -m src.export_web</p>';
    return;
  }

  const I18N = window.ARXIVCOUNT_ZH || {};
  const EVENT_ZH = I18N.events || {};
  const PHASE_ZH = I18N.phases || {};
  const SUBFIELD_ZH = I18N.subfields || {};

  function deepClone(o) {
    return JSON.parse(JSON.stringify(o));
  }

  function localizeEvent(e) {
    if (!e) return e;
    const z = EVENT_ZH[e.id] || {};
    const out = Object.assign({}, e);
    if (z.label) out.label = z.label;
    if (z.note) out.note = z.note;
    if (z.keystone_reason) out.keystone_reason = z.keystone_reason;
    if (z.open_problem_name) out.open_problem_name = z.open_problem_name;
    if (Array.isArray(out.subfields)) {
      out.subfields = out.subfields.map((s) => SUBFIELD_ZH[s] || s);
    }
    return out;
  }

  const data = deepClone(raw);
  if (data.project) {
    data.project.title = "arXiv 上的 AI 辅助数学证明";
  }
  if (Array.isArray(data.phases)) {
    data.phases = data.phases.map((ph) =>
      Object.assign({}, ph, { label: PHASE_ZH[ph.id] || ph.label })
    );
  }
  if (Array.isArray(data.navigable)) {
    data.navigable = data.navigable.map(localizeEvent);
  }
  if (Array.isArray(data.events)) {
    data.events = data.events.map(localizeEvent);
  }
  if (data.keystones && Array.isArray(data.keystones.items)) {
    data.keystones.items = data.keystones.items.map((it) => {
      const z = EVENT_ZH[it.id] || {};
      return Object.assign({}, it, {
        label: z.label || it.label,
        reason: z.keystone_reason || it.reason,
      });
    });
  }
  if (data.dual && data.dual.labels) {
    data.dual.labels = {
      core: "核心贡献 — AI 对真实数学主张/结果有实质作用",
      rigorous: "严格过程 — AI 参与形式化 / 验证 / 严格证明步骤",
    };
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
    if (e.type === "canon_milestone") return ICONS[e.kind] || ICONS.system;
    if (e.is_core_contribution || e.open_problem) return ICONS.result;
    if (e.is_rigorous_process) return ICONS.system;
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
        model: "模型",
        system: "系统",
        result: "结果",
        trend: "趋势",
        policy: "政策",
        community: "社区",
      };
      return map[e.kind] || "里程碑";
    }
    return "论文";
  }

  function trackLabel(e) {
    const t = e.public_track;
    if (t === "both") return { text: "核心 + 严格", cls: "both" };
    if (t === "core" || e.is_core_contribution) return { text: "核心贡献", cls: "core" };
    if (t === "rigorous" || e.is_rigorous_process) return { text: "严格过程", cls: "rigorous" };
    if (e.type === "canon_milestone") return { text: "正典里程碑", cls: "" };
    return { text: "其他", cls: "" };
  }

  function jumpKeystone(dir) {
    const ranks = nav
      .map((e, i) => ({ i, r: e.keystone_rank, k: e.is_keystone }))
      .filter((x) => x.k);
    if (!ranks.length) return;
    ranks.sort((a, b) => (a.r || 99) - (b.r || 99));
    const pos = ranks.findIndex((x) => x.i === idx);
    let next;
    if (pos < 0) {
      next =
        dir > 0
          ? ranks.find((x) => x.i > idx) || ranks[0]
          : [...ranks].reverse().find((x) => x.i < idx) || ranks[ranks.length - 1];
    } else {
      const j = (pos + dir + ranks.length) % ranks.length;
      next = ranks[j];
    }
    idx = next.i;
    renderFocus();
  }

  function renderFocus() {
    const e = nav[idx] || {};
    const cardEl = $("focusCard");
    cardEl.style.animation = "none";
    void cardEl.offsetWidth;
    cardEl.style.animation = "";

    $("focusIcon").innerHTML = iconFor(e);
    $("focusKind").textContent = kindLabel(e);
    const tr = trackLabel(e);
    const trackEl = $("focusTrack");
    const banner = $("keystoneBanner");
    const card = $("focusCard");
    if (e.is_keystone) {
      trackEl.textContent = `关键节点 #${e.keystone_rank || "—"}`;
      trackEl.className = "chip chip-keystone";
      banner.hidden = false;
      $("keystoneBannerText").textContent = `关键节点 #${e.keystone_rank} / 10`;
      card.classList.add("is-keystone");
    } else {
      trackEl.textContent = tr.text;
      trackEl.className = "chip chip-track " + (tr.cls || "");
      banner.hidden = true;
      card.classList.remove("is-keystone");
    }
    $("focusDate").textContent = fmtDate(e.date);
    $("focusTitle").textContent = e.label || e.title || e.id || "—";
    const noteBits = [];
    if (e.is_keystone && e.keystone_reason) noteBits.push(e.keystone_reason);
    noteBits.push(e.note || e.open_problem_name || e.ai_role_summary || "暂无摘要。");
    $("focusNote").textContent = noteBits.join(" — ");

    const tags = [];
    if (e.is_keystone) tags.push(["hot", `★ 关键节点 #${e.keystone_rank}`]);
    if (e.type === "canon_milestone") tags.push(["", "正典"]);
    if (e.is_core_contribution) tags.push(["hot", "核心贡献"]);
    if (e.is_rigorous_process) tags.push(["ok", "严格过程"]);
    if (e.open_problem) tags.push(["hot", "开放问题"]);
    if (Array.isArray(e.subfields)) {
      e.subfields.slice(0, 2).forEach((s) => tags.push(["", s]));
    }
    $("focusTags").innerHTML = tags
      .map(([cls, t]) => `<span class="tag ${cls}">${t}</span>`)
      .join("");

    document.querySelectorAll(".ks-btn").forEach((btn) => {
      const bi = Number(btn.dataset.i);
      btn.classList.toggle("active", bi === idx);
    });

    const link = $("focusLink");
    const pdf = $("focusPdf");
    if (e.url) {
      link.href = e.url;
      link.style.visibility = "visible";
      link.textContent = e.arxiv_id ? `打开论文 · ${e.arxiv_id}` : "打开来源";
    } else {
      link.removeAttribute("href");
      link.style.visibility = "hidden";
    }
    if (e.pdf_url || e.arxiv_id) {
      pdf.href = e.pdf_url || `https://arxiv.org/pdf/${e.arxiv_id}.pdf`;
      pdf.style.display = "inline-flex";
    } else {
      pdf.style.display = "none";
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

  function renderKeystoneStrip() {
    const box = $("keystoneButtons");
    if (!box) return;
    const items = nav
      .map((e, i) => ({ e, i }))
      .filter((x) => x.e.is_keystone)
      .sort((a, b) => (a.e.keystone_rank || 99) - (b.e.keystone_rank || 99));
    box.innerHTML = items
      .map(({ e, i }) => {
        const lab = (e.label || "").toString().replace(/"/g, "&quot;");
        return `<button type="button" class="ks-btn${i === idx ? " active" : ""}" data-i="${i}" title="#${e.keystone_rank} ${lab}">${e.keystone_rank}</button>`;
      })
      .join("");
    box.querySelectorAll(".ks-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        idx = Number(btn.dataset.i);
        renderFocus();
      });
    });
  }

  function renderScrub() {
    const track = $("scrubTrack");
    track.innerHTML = nav
      .map((e, i) => {
        const cls = ["tick"];
        if (e.is_keystone) cls.push("keystone");
        else if (e.type === "canon_milestone") cls.push("canon");
        else if (e.is_core_contribution) cls.push("core-tick");
        if (i === idx) cls.push("active");
        const tip = (e.label || e.id || "").toString().replace(/"/g, "&quot;");
        const star = e.is_keystone ? `★#${e.keystone_rank} · ` : "";
        const num = e.is_keystone
          ? `<span class="ks-num">${e.keystone_rank}</span>`
          : "";
        return `<button type="button" class="${cls.join(" ")}" data-i="${i}" aria-label="${tip}" title="${star}${tip}">
          ${num}
          <span class="tip">${star}${fmtDate(e.date)} · ${tip.length > 32 ? tip.slice(0, 30) + "…" : tip}</span>
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
    const d = data.dual || {};
    const c = data.contribution || {};
    const p = data.penetration || {};
    const latest = p.latest || {};
    const ks = (data.keystones && data.keystones.count) || nav.filter((e) => e.is_keystone).length;
    const items = [
      { k: "核心贡献", v: d.core_n ?? c.strict_n ?? "—", h: "实质数学主张" },
      { k: "严格过程", v: d.rigorous_n ?? "—", h: "形式化 / 验证步骤" },
      { k: "关键节点", v: ks, h: "金色刻度 · Shift+←/→" },
      {
        k: "核心 / 万篇 math",
        v: latest.strict_per_10k != null ? Number(latest.strict_per_10k).toFixed(1) : "—",
        h: latest.year ? `${latest.year} · 若为 2026 则为不完全年` : "分母",
      },
    ];
    $("metricRow").innerHTML = items
      .map(
        (r) =>
          `<div class="metric"><div class="k">${r.k}</div><div class="v">${r.v}</div><div class="h">${r.h}</div></div>`
      )
      .join("");
  }

  function renderCharts() {
    const d = data.dual || {};
    const c = data.contribution || {};
    const coreY = d.yearly_core || c.yearly_strict || {};
    const rigY = d.yearly_rigorous || {};
    const years = Array.from(new Set([...Object.keys(coreY), ...Object.keys(rigY)])).sort();

    const box = $("chartCounts");
    if (!years.length) {
      box.innerHTML = `<p class="legend">暂无逐年双轨数据。</p>`;
    } else {
      const max = Math.max(
        ...years.map((y) => Math.max(Number(coreY[y] || 0), Number(rigY[y] || 0))),
        1
      );
      box.innerHTML = years
        .map((y) => {
          const w = Number(coreY[y] || 0);
          const s = Number(rigY[y] || 0);
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
      penBox.innerHTML = `<p class="legend">请运行: python -m src.denominator</p>`;
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
        "每万篇基于核心/实质集合除以当年 math.* 总量。2026 为不完全年。为自我披露代理下界。";
    }
  }

  function renderPhases() {
    const phases = data.phases || [];
    $("phaseGrid").innerHTML = phases
      .map(
        (ph) => `<div class="phase-item">
          <div>
            <strong>${ph.label || ph.id}</strong><br/>
            <span>${ph.start} → ${ph.end}</span>
          </div>
          <div class="n">${ph.strict_like ?? 0} 核心向</div>
        </div>`
      )
      .join("");
  }

  function renderFoot() {
    const proj = data.project || {};
    const lr = data.link_report || {};
    const bits = [];
    if (proj.github) bits.push(`<a href="${proj.github}" target="_blank" rel="noopener">GitHub</a>`);
    bits.push(`带摘要页链接的论文：${lr.paper_events_with_abs ?? "—"}`);
    bits.push(`生成于 ${(data.generated_at || "").slice(0, 19)}`);
    bits.push(`<a href="../" hreflang="en">English</a>`);
    $("dataFoot").innerHTML = bits.join(" · ");
  }

  function go(d) {
    idx = Math.min(nav.length - 1, Math.max(0, idx + d));
    renderFocus();
  }

  $("btnPrev").addEventListener("click", () => go(-1));
  $("btnNext").addEventListener("click", () => go(1));
  window.addEventListener("keydown", (ev) => {
    if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      if (ev.shiftKey) jumpKeystone(-1);
      else go(-1);
    }
    if (ev.key === "ArrowRight") {
      ev.preventDefault();
      if (ev.shiftKey) jumpKeystone(1);
      else go(1);
    }
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

  renderKeystoneStrip();
  renderScrub();
  renderFocus();
  renderMetrics();
  renderCharts();
  renderPhases();
  renderFoot();
})();
