# Methodology

## Research question

How has the **volume and character** of arXiv `math.*` preprints that mention AI / LLMs / formal AI-proving tooling changed since ~2015, with special attention to 2022–2026 milestones (ChatGPT, AlphaGeometry/AlphaProof, Erdős-problem AI results, unit-distance disproof)?

## Proxy definition

We do **not** claim ground-truth labels for “AI proved this.” We build a **keyword proxy** with two stages:

### Stage A — Loose collection

- Restrict to `math.*` via arXiv API category filters.
- Run several **seed queries** (LLM names, Lean/formal, AI-assisted phrasing).
- Upsert all returned metadata into local SQLite.
- Score title+abstract with `keywords_loose.yaml` + boosts from `keywords_strict.yaml`.

### Stage B — Curation

- Export papers with level ≥ L1 by default.
- Demote writing-only language when strong proof signals are absent.
- Human review can further edit `data/curated/` later.

## Levels

| Level | Intent |
|-------|--------|
| L0 | Mention-level / weak |
| L1 | Plausible AI-assisted math work |
| L2 | Formal + AI co-signals |
| L3 | Open-problem language + strong AI signals |

Thresholds live in `config/settings.yaml` → `classify.levels`.

## Milestones

`config/milestones.yaml` is a **manual narrative layer**. Milestone dates mark the dashboard; they are not automatically joined to paper IDs except when notes include known arXiv IDs.

## Known biases

1. **Lexical bias** — English keywords; non-disclosing authors invisible.  
2. **Writing vs proving** — mitigations imperfect.  
3. **Category bias** — CS-adjacent AI proofs may sit in `cs.AI` / `cs.LO` (out of v1 scope).  
4. **API sampling** — seed queries ≠ full `math.*` scan; expand later with bulk metadata if needed.  
5. **Temporal disclosure** — norms for acknowledging AI change over time.

## Reproducibility checklist

When publishing a chart, record:

- git commit hash  
- `keywords_*.yaml` versions  
- collect run dates / `collect_runs` table  
- whether curated or loose set was used  
