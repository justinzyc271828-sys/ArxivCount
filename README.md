# ArxivCount

**AI-assisted mathematical work on arXiv — collect loosely, curate locally, visualize trends.**

Track how often `math.*` preprints mention LLMs, AI-assisted proofs, Lean/autoformalization, and related signals — especially around milestones such as the 2026 unit-distance conjecture disproof.

> This is a **reproducible proxy dashboard**, not an official census of every AI proof. Keyword methods have false positives (writing help) and false negatives (undisclosed AI use).

| | |
|---|---|
| Author | Justin Yao |
| GitHub | [justinzyc271828-sys/ArxivCount](https://github.com/justinzyc271828-sys/ArxivCount) |
| **Live timeline (EN)** | [justinzyc271828-sys.github.io/ArxivCount](https://justinzyc271828-sys.github.io/ArxivCount/) |
| **时间轴（中文）** | [justinzyc271828-sys.github.io/ArxivCount/zh/](https://justinzyc271828-sys.github.io/ArxivCount/zh/) |
| Scope (v1) | `math.*` only (cs.LO / cs.AI later) |

> Personal homepage integration is optional and **not** wired yet — share the GitHub Pages timeline URL for now.

---

## Idea in one diagram

```text
arXiv API  --loose keywords-->  data/raw (SQLite, local D:)
                                      |
                                      v
                              classifications (L0–L3)
                                      |
                    +-----------------+------------------+
                    v                                    v
            data/candidates                      data/curated (strict)
                    |                                    |
                    +-----------------+------------------+
                                      v
                              data/stats + Streamlit
                                      |
                                      v
                         GitHub repo + personal site card
```

1. **Stage A (loose)** — wide seed queries + local keyword net → high recall, stored on disk  
2. **Stage B (curate)** — drop weak writing-only hits, export L1+ set  
3. **Visualize** — monthly trend, levels, categories, milestone lines  

Heavy caches stay on your machine (`data/raw`, optional PDFs). Git only tracks code, configs, and small curated/sample stats.

---

## Quick start

```powershell
cd D:\Workspaces\Github\ArxivCount
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Smoke test (small pull)
python -m src.collect --max-per-query 30
python -m src.refine --limit 20              # needs DEEPSEEK_API_KEY
python -m src.aggregate
streamlit run app.py
```

Full local harvest + DeepSeek refine (stay local; no GitHub push required):

```powershell
python -m src.collect
python -m src.refine                         # rules + deepseek-v4-flash
python -m src.aggregate
streamlit run app.py
# or
.\scripts\run_pipeline.ps1
```

Useful flags:

```powershell
python -m src.collect --dry-run              # print queries only
python -m src.collect --reclassify-only      # re-score local DB after editing keywords
python -m src.curate --min-level L2          # keyword-only export (no LLM)
python -m src.refine                         # rule hard-filter + DeepSeek review
python -m src.refine --no-llm                # rules only
python -m src.refine --force                 # ignore LLM cache, re-label all
```

`src.refine` expects `DEEPSEEK_API_KEY` (optional `DEEPSEEK_BASE_URL`, default `https://api.deepseek.com`).  
Outputs: `data/curated/refined.jsonl` (keep), `dropped.jsonl`, `llm_labels_cache.jsonl` (resume cache).

### Deep audit (second pass)

Structured review of the refined set: AI usage roles, subfields, proof/result types, open problems, models/formal systems.

```powershell
python -m src.deep_audit                 # all refined papers
python -m src.deep_audit --force         # ignore cache
python -m src.deep_audit --limit 20      # smoke test
```

Outputs:

- `data/curated/deep_confirmed.jsonl` — second-pass keep set  
- `data/curated/deep_demoted.jsonl` — demoted on re-check  
- `data/curated/deep_audit_summary.json` — aggregates  
- `docs/deep_audit_report.md` — human-readable report  
- `data/stats/deep_*.csv` — trend tables  

### Full-text audit (highest precision so far)

Download PDF/HTML for the confirmed set, extract text, re-label with DeepSeek on head+tail full text (acknowledgements + body).

```powershell
python -m src.fulltext_audit                 # all deep_confirmed
python -m src.fulltext_audit --limit 10      # smoke
python -m src.fulltext_audit --force-audit   # re-label, keep PDFs
```

Outputs:

- `data/downloads/*.pdf|*.txt` — local full text (gitignored)  
- `data/curated/fulltext_confirmed.jsonl` — final keep  
- `data/curated/fulltext_demoted.jsonl`  
- `data/curated/fulltext_vs_abstract.json` — abstract vs full-text flips  
- `docs/fulltext_audit_report.md`

### Repair + human spot-check

```powershell
python -m src.repair_fulltext                 # retry failed fulltext downloads
python -m src.spotcheck --limit 40            # priority human review queue
python -m src.spotcheck --open-problem-only --limit 25 --name spotcheck_open_problems
```

- `docs/spotcheck_queue.md` — mixed high-priority papers  
- `docs/spotcheck_open_problems.md` — open-problem focus  
- Fill `human_verdict`: `confirm` / `demote` / `unsure`

### Contribution tiers + timeline (impact narrative)

```powershell
python -m src.contribution          # C0–C4 grading (uses fulltext cache)
python -m src.timeline              # canon milestones + C3/C4 paper timeline
streamlit run app.py                # wide/strict curves + timeline panel
```

| Set | Meaning | File |
|-----|---------|------|
| Wide C2+ | ecosystem | `data/curated/set_wide.jsonl` |
| Strict C3+ | material math impact claims | `data/curated/set_strict.jsonl` |
| C4 / milestone | decisive / highlight | `data/curated/set_c4_milestones.jsonl` |

Writing pack:

- `docs/report_ai_math_impact.md` — research report draft  
- `docs/article_outline_longform.md` — long-form essay outline（冷静计量）  
- `docs/timeline.md` — public timeline  

### Denominator (math totals → penetration)

```powershell
python -m src.denominator                 # fetch cat:math* yearly totals + rates
python -m src.denominator --skip-fetch    # recompute rates only
```

Outputs: `data/stats/penetration_yearly.csv`, `penetration_summary.json`

### Interactive timeline (GitHub Pages / local)

Modelrumor-style **← →** milestone browser (keyboard + on-screen buttons + rail ticks):

```powershell
python -m src.export_web
# then open:
#   web/timeline/index.html
# or: python -m http.server 8765 --directory web/timeline
```

Deploy: publish `web/timeline/` as GitHub Pages (project pages or copy into `justinzyc271828-sys.github.io`).

---

## Levels (heuristic)

| Level | Meaning |
|-------|---------|
| **L0** | Weak AI/LLM mention (often writing-related after demotion) |
| **L1** | Likely AI-assisted mathematical work |
| **L2** | Formal methods + AI signals (Lean/Isabelle/…) |
| **L3** | Strong AI + open-problem language (conjecture/disproof/…) |

Edit dictionaries in:

- `config/keywords_loose.yaml` — stage A recall  
- `config/keywords_strict.yaml` — scoring / curation boosts  
- `config/milestones.yaml` — narrative vertical lines  
- `config/settings.yaml` — categories, dates, paths  

---

## Data layout (local)

```text
data/
  raw/           # SQLite + full collected metadata (gitignored)
  downloads/     # optional PDFs later (gitignored)
  candidates/    # all loose hits export
  curated/       # stage-B L1+ set
  stats/         # CSV/JSON for charts
```

Default DB: `data/raw/arxiv_math.sqlite3`

---

## Personal website

Grenzgang is a static GitHub Pages site. Recommended integration:

1. Keep this repo public under `justinzyc271828-sys/ArxivCount`
2. Add an **AI** post/card linking here + 1–2 exported charts from `data/stats/`
3. Optionally enable GitHub Pages on this repo for a static plot page later

Do **not** commit multi‑GB raw dumps to Pages.

---

## Method limitations

- Disclosure bias: later authors may mention AI more (or less)  
- “ChatGPT polished the paper” ≠ “AI proved a theorem”  
- Formal Lean papers without LLM wording can still be human-only  
- Seed queries miss papers that never use our keywords  

Always report **method + version of keyword files** when sharing charts.

---

## Roadmap

- [x] Project skeleton, loose/strict configs, SQLite collect  
- [x] Aggregate + curate + Streamlit MVP  
- [ ] Larger historical backfill + baseline math.* volume (share of all math)  
- [ ] Optional PDF/HTML full-text for high-score candidates  
- [ ] Static HTML export for justinzyc271828-sys.github.io  
- [ ] Optional cs.LO / cs.AI expansion  

---

## License

MIT (see `LICENSE` if present). arXiv metadata remains subject to [arXiv terms](https://arxiv.org/help/api/tou).
