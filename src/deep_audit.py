"""Deep audit of refined papers with DeepSeek: usage roles, subfields, proof trends."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm

from .config import load_settings
from .db import utc_now
from .llm_client import chat_json, get_deepseek_client
from .paths import ensure_data_dirs, resolve

SYSTEM_PROMPT = """You are an expert bibliographer of AI-for-mathematics research.

Given an arXiv math paper (title + abstract + keyword hints), produce a DEEP structured audit.
Return ONLY a JSON object with this schema:

{
  "confirm_keep": boolean,
  "confirm_reason": string,          // <= 25 words; why keep or drop on second review
  "ai_roles": [string],              // multi-select from ROLE list below (can be empty if drop)
  "primary_ai_role": string,         // single best role, or "none"
  "ai_centrality": string,           // "core" | "substantial" | "peripheral" | "none"
  "human_ai_relation": string,       // "ai_led" | "human_led_ai_assist" | "joint" | "ai_method_only" | "none"
  "result_type": string,             // from RESULT list
  "proof_style": [string],           // multi-select from PROOF list
  "math_subfields": [string],        // 1-3 from SUBFIELD list (prefer arXiv-aligned)
  "open_problem": boolean,           // touches named open problem / conjecture / prize problem
  "open_problem_name": string|null,  // short name if any
  "formal_system": [string],         // e.g. ["lean4","isabelle","coq","none"]
  "models_mentioned": [string],      // e.g. ["chatgpt","gpt-5","claude","alphaproof"] lowercase
  "trend_tags": [string],            // free short tags like "erdos","unit-distance","imo","autoformalization"
  "year_signal": string,             // "pre_chatgpt" | "early_llm" | "formal_wave" | "open_problem_wave" | "unclear"
  "confidence": number,              // 0-1
  "one_line_summary": string         // <= 30 words: what AI actually did here
}

ROLE list (ai_roles / primary_ai_role):
- proof_generation: AI drafts or finds proofs/lemmas
- counterexample_search: AI finds counterexamples / disproofs
- formalization: AI writes or searches Lean/Isabelle/Coq proofs
- conjecture_discovery: AI proposes conjectures/constructions
- exploration_search: AI guides large-scale search / evolutionary math discovery
- verification_check: AI checks steps / finds bugs in proofs
- method_system_benchmark: paper builds/evaluates AI-for-math systems (not a single math theorem)
- code_numerics: AI helps scientific computing / numerics only
- writing_only: prose/editing only
- none

RESULT list (result_type):
- new_theorem
- open_problem_resolution
- improved_bound_construction
- formalization_of_known_result
- method_or_system
- benchmark_evaluation
- survey_position
- educational_demo
- other

PROOF list (proof_style):
- informal_natural_language
- formal_machine_checked
- computer_assisted_search
- probabilistic_method
- constructive_example
- olympiad_style
- research_level_argument
- none_or_na

SUBFIELD list (math_subfields) — pick closest:
- combinatorics
- number_theory
- algebra
- algebraic_geometry
- topology_geometry
- analysis
- probability_stats
- logic_foundations
- optimization
- discrete_geometry
- graph_theory
- dynamical_systems
- mathematical_physics
- cs_theory_adjacent
- general_or_multiple
- other

Rules:
- Be strict: if AI is only for writing English, confirm_keep=false, primary_ai_role=writing_only.
- Pure classical Lean formalization with no AI -> confirm_keep=false.
- Method/system papers about AI math CAN be keep=true with primary_ai_role=method_system_benchmark.
- Prefer evidence in abstract; do not invent model names not implied.
"""


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _load_cache(path: Path) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    for obj in _load_jsonl(path):
        aid = obj.get("arxiv_id")
        if aid:
            cache[aid] = obj
    return cache


def _user_prompt(item: dict[str, Any]) -> str:
    abstract = (item.get("abstract") or "")[:2200]
    terms = ", ".join((item.get("matched_terms") or [])[:15])
    return (
        f"arxiv_id: {item.get('arxiv_id')}\n"
        f"title: {item.get('title')}\n"
        f"published: {item.get('published')}\n"
        f"primary_category: {item.get('primary_category')}\n"
        f"categories: {item.get('categories')}\n"
        f"prior_keyword_level: {item.get('keyword_level') or item.get('level')}\n"
        f"prior_category: {item.get('category')}\n"
        f"prior_reason: {item.get('refine_reason')}\n"
        f"matched_terms: {terms}\n"
        f"abstract:\n{abstract}\n"
    )


def _normalize_audit(raw: dict[str, Any], arxiv_id: str) -> dict[str, Any]:
    keep = bool(raw.get("confirm_keep"))
    roles = raw.get("ai_roles") or []
    if not isinstance(roles, list):
        roles = [str(roles)]
    roles = [str(x) for x in roles]

    proof_style = raw.get("proof_style") or []
    if not isinstance(proof_style, list):
        proof_style = [str(proof_style)]

    subfields = raw.get("math_subfields") or []
    if not isinstance(subfields, list):
        subfields = [str(subfields)]

    formal = raw.get("formal_system") or []
    if not isinstance(formal, list):
        formal = [str(formal)]

    models = raw.get("models_mentioned") or []
    if not isinstance(models, list):
        models = [str(models)]

    tags = raw.get("trend_tags") or []
    if not isinstance(tags, list):
        tags = [str(tags)]

    try:
        conf = float(raw.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5

    centrality = str(raw.get("ai_centrality") or "none")
    if centrality not in {"core", "substantial", "peripheral", "none"}:
        centrality = "substantial" if keep else "none"

    return {
        "arxiv_id": arxiv_id,
        "confirm_keep": keep,
        "confirm_reason": str(raw.get("confirm_reason") or "")[:300],
        "ai_roles": roles,
        "primary_ai_role": str(raw.get("primary_ai_role") or ("none" if not keep else "other")),
        "ai_centrality": centrality,
        "human_ai_relation": str(raw.get("human_ai_relation") or "none"),
        "result_type": str(raw.get("result_type") or "other"),
        "proof_style": [str(x) for x in proof_style],
        "math_subfields": [str(x) for x in subfields][:3],
        "open_problem": bool(raw.get("open_problem")),
        "open_problem_name": raw.get("open_problem_name"),
        "formal_system": [str(x).lower() for x in formal],
        "models_mentioned": [str(x).lower() for x in models],
        "trend_tags": [str(x) for x in tags][:8],
        "year_signal": str(raw.get("year_signal") or "unclear"),
        "confidence": max(0.0, min(1.0, conf)),
        "one_line_summary": str(raw.get("one_line_summary") or "")[:400],
        "audited_at": utc_now(),
    }


def audit_one(client: Any, item: dict[str, Any], model: str) -> dict[str, Any]:
    raw = chat_json(
        client,
        system=SYSTEM_PROMPT,
        user=_user_prompt(item),
        model=model,
        temperature=0.05,
        max_tokens=900,
    )
    return _normalize_audit(raw, item["arxiv_id"])


def run_deep_audit(
    settings: dict[str, Any] | None = None,
    *,
    model: str = "deepseek-v4-flash",
    workers: int = 6,
    limit: int | None = None,
    force: bool = False,
    source: str = "refined",
) -> dict[str, Any]:
    settings = settings or load_settings()
    ensure_data_dirs(settings)
    curated_dir = resolve(settings["paths"]["curated_dir"])
    stats_dir = resolve(settings["paths"]["stats_dir"])
    curated_dir.mkdir(parents=True, exist_ok=True)
    stats_dir.mkdir(parents=True, exist_ok=True)

    src_path = curated_dir / ("refined.jsonl" if source == "refined" else "curated.jsonl")
    papers = _load_jsonl(src_path)
    if not papers:
        raise FileNotFoundError(f"No papers at {src_path}; run refine first")

    if limit is not None:
        papers = papers[:limit]

    cache_path = curated_dir / "deep_audit_cache.jsonl"
    out_path = curated_dir / "deep_audit.jsonl"
    out_json = curated_dir / "deep_audit.json"
    confirmed_path = curated_dir / "deep_confirmed.jsonl"
    demoted_path = curated_dir / "deep_demoted.jsonl"
    summary_path = curated_dir / "deep_audit_summary.json"
    report_md = resolve("docs") / "deep_audit_report.md"

    cache = {} if force else _load_cache(cache_path)
    if force and cache_path.exists():
        cache_path.unlink()
        cache = {}

    client = get_deepseek_client()
    results: dict[str, dict[str, Any]] = {}
    todo: list[dict[str, Any]] = []
    for p in papers:
        aid = p["arxiv_id"]
        if aid in cache:
            results[aid] = cache[aid]
        else:
            todo.append(p)

    print(f"Deep audit: total={len(papers)} cached={len(results)} todo={len(todo)} model={model}")

    errors = 0

    def work(p: dict[str, Any]) -> dict[str, Any]:
        row = audit_one(client, p, model)
        row["model"] = model
        return row

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {ex.submit(work, p): p for p in todo}
        for fut in tqdm(as_completed(futs), total=len(futs), desc="deep-audit"):
            p = futs[fut]
            try:
                row = fut.result()
            except Exception as e:  # noqa: BLE001
                errors += 1
                row = {
                    "arxiv_id": p["arxiv_id"],
                    "confirm_keep": True,  # fail-open to prior refine keep
                    "confirm_reason": f"audit error: {type(e).__name__}",
                    "ai_roles": [],
                    "primary_ai_role": "unknown",
                    "ai_centrality": "unknown",
                    "human_ai_relation": "unknown",
                    "result_type": "other",
                    "proof_style": [],
                    "math_subfields": [],
                    "open_problem": False,
                    "open_problem_name": None,
                    "formal_system": [],
                    "models_mentioned": [],
                    "trend_tags": [],
                    "year_signal": "unclear",
                    "confidence": 0.2,
                    "one_line_summary": "audit failed",
                    "model": model,
                    "audited_at": utc_now(),
                    "error": str(e)[:200],
                }
            results[p["arxiv_id"]] = row
            _append_jsonl(cache_path, row)

    print(f"LLM errors: {errors}")

    # Merge paper metadata + audit
    merged: list[dict[str, Any]] = []
    confirmed: list[dict[str, Any]] = []
    demoted: list[dict[str, Any]] = []
    for p in papers:
        audit = results.get(p["arxiv_id"], {})
        row = {
            **p,
            **{f"audit_{k}" if k in p else k: v for k, v in audit.items() if k != "arxiv_id"},
            # clean explicit fields
            "confirm_keep": audit.get("confirm_keep"),
            "confirm_reason": audit.get("confirm_reason"),
            "ai_roles": audit.get("ai_roles"),
            "primary_ai_role": audit.get("primary_ai_role"),
            "ai_centrality": audit.get("ai_centrality"),
            "human_ai_relation": audit.get("human_ai_relation"),
            "result_type": audit.get("result_type"),
            "proof_style": audit.get("proof_style"),
            "math_subfields": audit.get("math_subfields"),
            "open_problem": audit.get("open_problem"),
            "open_problem_name": audit.get("open_problem_name"),
            "formal_system": audit.get("formal_system"),
            "models_mentioned": audit.get("models_mentioned"),
            "trend_tags": audit.get("trend_tags"),
            "year_signal": audit.get("year_signal"),
            "audit_confidence": audit.get("confidence"),
            "one_line_summary": audit.get("one_line_summary"),
            "audit_model": audit.get("model"),
        }
        # strip accidental audit_arxiv_id noise
        merged.append(row)
        if audit.get("confirm_keep"):
            confirmed.append(row)
        else:
            demoted.append(row)

    with out_path.open("w", encoding="utf-8") as f:
        for row in merged:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    with confirmed_path.open("w", encoding="utf-8") as f:
        for row in confirmed:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with demoted_path.open("w", encoding="utf-8") as f:
        for row in demoted:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = build_summary(merged, confirmed, demoted, model=model)
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Stats exports for charts
    export_trend_tables(confirmed, stats_dir)
    write_report(summary, confirmed, demoted, report_md)

    # Point curated.jsonl at deep-confirmed for dashboard
    curated_jsonl = curated_dir / "curated.jsonl"
    with curated_jsonl.open("w", encoding="utf-8") as f:
        for row in confirmed:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (curated_dir / "curated_summary.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "count": len(confirmed),
                "source": "deep_audit",
                "demoted_from_refined": len(demoted),
                "by_primary_ai_role": summary["by_primary_ai_role"],
                "by_subfield": summary["by_subfield"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    # Also overwrite refined keep-set? Keep refined.jsonl as first-pass; confirmed is second-pass.
    print(json.dumps({k: summary[k] for k in (
        "input", "confirmed", "demoted", "by_primary_ai_role", "by_result_type",
        "by_subfield", "by_centrality", "open_problem_count"
    )}, indent=2, ensure_ascii=False))
    print(f"Deep confirmed -> {confirmed_path}")
    print(f"Report -> {report_md}")
    return summary


def build_summary(
    merged: list[dict[str, Any]],
    confirmed: list[dict[str, Any]],
    demoted: list[dict[str, Any]],
    *,
    model: str,
) -> dict[str, Any]:
    def count_field(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        return dict(Counter(str(r.get(key) or "unknown") for r in rows))

    def count_list_field(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        c: Counter[str] = Counter()
        for r in rows:
            vals = r.get(key) or []
            if isinstance(vals, list):
                for v in vals:
                    c[str(v)] += 1
            elif vals:
                c[str(vals)] += 1
        return dict(c.most_common())

    # yearly
    yearly: dict[str, int] = Counter()
    yearly_role: dict[str, Counter[str]] = defaultdict(Counter)
    yearly_subfield: dict[str, Counter[str]] = defaultdict(Counter)
    for r in confirmed:
        pub = r.get("published") or ""
        year = pub[:4] if len(pub) >= 4 else "unknown"
        yearly[year] += 1
        yearly_role[year][str(r.get("primary_ai_role") or "unknown")] += 1
        subs = r.get("math_subfields") or []
        if isinstance(subs, list) and subs:
            yearly_subfield[year][str(subs[0])] += 1
        else:
            yearly_subfield[year]["unknown"] += 1

    open_problems = [
        {
            "arxiv_id": r.get("arxiv_id"),
            "title": r.get("title"),
            "name": r.get("open_problem_name"),
            "primary_ai_role": r.get("primary_ai_role"),
            "url": r.get("url") or f"https://arxiv.org/abs/{r.get('arxiv_id')}",
        }
        for r in confirmed
        if r.get("open_problem")
    ]

    return {
        "generated_at": utc_now(),
        "model": model,
        "input": len(merged),
        "confirmed": len(confirmed),
        "demoted": len(demoted),
        "by_primary_ai_role": count_field(confirmed, "primary_ai_role"),
        "by_ai_roles_multi": count_list_field(confirmed, "ai_roles"),
        "by_centrality": count_field(confirmed, "ai_centrality"),
        "by_human_ai_relation": count_field(confirmed, "human_ai_relation"),
        "by_result_type": count_field(confirmed, "result_type"),
        "by_proof_style_multi": count_list_field(confirmed, "proof_style"),
        "by_subfield": count_list_field(confirmed, "math_subfields"),
        "by_formal_system": count_list_field(confirmed, "formal_system"),
        "by_models": count_list_field(confirmed, "models_mentioned"),
        "by_trend_tags": count_list_field(confirmed, "trend_tags"),
        "by_year_signal": count_field(confirmed, "year_signal"),
        "yearly_counts": dict(sorted(yearly.items())),
        "yearly_primary_role": {y: dict(c) for y, c in sorted(yearly_role.items())},
        "yearly_top_subfield": {y: dict(c) for y, c in sorted(yearly_subfield.items())},
        "open_problem_count": len(open_problems),
        "open_problems": open_problems[:50],
        "demoted_reasons": dict(
            Counter(str(r.get("confirm_reason") or "")[:80] for r in demoted).most_common(20)
        ),
        "mean_audit_confidence": (
            sum(float(r.get("audit_confidence") or 0) for r in confirmed) / len(confirmed)
            if confirmed
            else 0.0
        ),
    }


def export_trend_tables(confirmed: list[dict[str, Any]], stats_dir: Path) -> None:
    if not confirmed:
        return
    rows = []
    for r in confirmed:
        pub = r.get("published") or ""
        year = pub[:4] if len(pub) >= 4 else None
        month = pub[:7] if len(pub) >= 7 else None
        subs = r.get("math_subfields") or []
        primary_sub = subs[0] if isinstance(subs, list) and subs else "unknown"
        rows.append(
            {
                "arxiv_id": r.get("arxiv_id"),
                "title": r.get("title"),
                "published": pub,
                "year": year,
                "year_month": month,
                "primary_ai_role": r.get("primary_ai_role"),
                "ai_centrality": r.get("ai_centrality"),
                "result_type": r.get("result_type"),
                "primary_subfield": primary_sub,
                "open_problem": bool(r.get("open_problem")),
                "level": r.get("level") or r.get("refined_level"),
                "url": r.get("url") or f"https://arxiv.org/abs/{r.get('arxiv_id')}",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(stats_dir / "deep_papers.csv", index=False)

    if "year" in df.columns:
        y = df.groupby(["year", "primary_ai_role"]).size().reset_index(name="count")
        y.to_csv(stats_dir / "deep_yearly_role.csv", index=False)
        ys = df.groupby(["year", "primary_subfield"]).size().reset_index(name="count")
        ys.to_csv(stats_dir / "deep_yearly_subfield.csv", index=False)
        yr = df.groupby(["year", "result_type"]).size().reset_index(name="count")
        yr.to_csv(stats_dir / "deep_yearly_result.csv", index=False)

    # also update main summary-ish counts from deep confirmed for dashboard
    monthly = (
        df.dropna(subset=["year_month"])
        .groupby("year_month")
        .size()
        .reset_index(name="count")
        .sort_values("year_month")
    )
    monthly.to_csv(stats_dir / "monthly_counts.csv", index=False)

    yearly = (
        df.dropna(subset=["year"])
        .groupby("year")
        .size()
        .reset_index(name="count")
        .sort_values("year")
    )
    yearly.to_csv(stats_dir / "yearly_counts.csv", index=False)

    # level-like from centrality/result for stack plot compatibility
    level_map = {
        "core": "L3",
        "substantial": "L2",
        "peripheral": "L1",
        "unknown": "L1",
        "none": "L0",
    }
    df["level"] = df["ai_centrality"].map(lambda x: level_map.get(str(x), "L1"))
    if not monthly.empty:
        pivot = (
            df.pivot_table(
                index="year_month",
                columns="level",
                values="arxiv_id",
                aggfunc="count",
                fill_value=0,
            )
            .reset_index()
        )
        base = monthly.merge(pivot, on="year_month", how="left")
        for col in ("L0", "L1", "L2", "L3"):
            if col not in base.columns:
                base[col] = 0
        base.to_csv(stats_dir / "monthly_counts.csv", index=False)

    cats = (
        df["primary_subfield"]
        .fillna("unknown")
        .value_counts()
        .rename_axis("primary_category")
        .reset_index(name="count")
    )
    cats.to_csv(stats_dir / "category_counts.csv", index=False)

    top = df.sort_values(["open_problem", "year"], ascending=[False, False]).head(100)
    top.to_csv(stats_dir / "top_papers.csv", index=False)

    summary = {
        "total_candidates": int(len(df)),
        "by_level": df["level"].value_counts().to_dict(),
        "writing_only": 0,
        "date_min": str(df["published"].min()) if len(df) else None,
        "date_max": str(df["published"].max()) if len(df) else None,
        "mean_score": None,
        "source": "deep_audit",
    }
    with (stats_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def write_report(
    summary: dict[str, Any],
    confirmed: list[dict[str, Any]],
    demoted: list[dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Deep Audit Report — AI-Assisted Math on arXiv")
    lines.append("")
    lines.append(f"- Generated: `{summary.get('generated_at')}`")
    lines.append(f"- Model: `{summary.get('model')}`")
    lines.append(
        f"- Input (after first refine): **{summary.get('input')}** → "
        f"confirmed **{summary.get('confirmed')}**, demoted **{summary.get('demoted')}**"
    )
    lines.append(f"- Open-problem linked: **{summary.get('open_problem_count')}**")
    lines.append("")
    lines.append("## 1. How AI is used (primary role)")
    lines.append("")
    for k, v in sorted(
        (summary.get("by_primary_ai_role") or {}).items(), key=lambda x: -x[1]
    ):
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("### Multi-label AI roles")
    lines.append("")
    for k, v in list((summary.get("by_ai_roles_multi") or {}).items())[:15]:
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 2. AI centrality & human–AI relation")
    lines.append("")
    lines.append("### Centrality")
    for k, v in (summary.get("by_centrality") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("### Relation")
    for k, v in (summary.get("by_human_ai_relation") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## 3. Math subfields")
    lines.append("")
    for k, v in list((summary.get("by_subfield") or {}).items())[:20]:
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## 4. Result / proof morphology")
    lines.append("")
    lines.append("### Result type")
    for k, v in (summary.get("by_result_type") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("### Proof style (multi)")
    for k, v in list((summary.get("by_proof_style_multi") or {}).items())[:15]:
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 5. Formal systems & models mentioned")
    lines.append("")
    lines.append("### Formal systems")
    for k, v in list((summary.get("by_formal_system") or {}).items())[:12]:
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("### Models / systems")
    for k, v in list((summary.get("by_models") or {}).items())[:20]:
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 6. Yearly volume (confirmed)")
    lines.append("")
    for y, n in (summary.get("yearly_counts") or {}).items():
        lines.append(f"- **{y}**: {n}")
    lines.append("")
    lines.append("## 7. Open problems / notable targets (sample)")
    lines.append("")
    for op in (summary.get("open_problems") or [])[:25]:
        lines.append(
            f"- [{op.get('arxiv_id')}]({op.get('url')}) — {op.get('name') or 'open problem'}  \n"
            f"  {op.get('title')}"
        )
    lines.append("")
    lines.append("## 8. Second-pass demotions (sample)")
    lines.append("")
    for r in demoted[:15]:
        lines.append(
            f"- `{r.get('arxiv_id')}`: {r.get('confirm_reason')}  \n"
            f"  _{str(r.get('title') or '')[:100]}_"
        )
    lines.append("")
    lines.append("## 9. Trend reading (auto sketch)")
    lines.append("")
    lines.append(_trend_narrative(summary))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "Method note: labels come from title/abstract via DeepSeek V4 Flash; "
        "not full-PDF verification. Treat as a structured proxy for local exploration."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _trend_narrative(summary: dict[str, Any]) -> str:
    yearly = summary.get("yearly_counts") or {}
    roles = summary.get("by_primary_ai_role") or {}
    subs = summary.get("by_subfield") or {}
    results = summary.get("by_result_type") or {}
    years_sorted = sorted(yearly.keys())
    growth = ""
    if len(years_sorted) >= 2:
        early = years_sorted[0]
        late = years_sorted[-1]
        growth = (
            f"Confirmed volume moves from **{yearly[early]}** ({early}) "
            f"to **{yearly[late]}** ({late}). "
        )
    top_role = max(roles, key=roles.get) if roles else "n/a"
    top_sub = max(subs, key=subs.get) if subs else "n/a"
    top_res = max(results, key=results.get) if results else "n/a"
    return (
        f"{growth}"
        f"Dominant AI usage is **{top_role}**; densest subfield signal is **{top_sub}**; "
        f"most common result type is **{top_res}**. "
        f"Open-problem-linked papers: **{summary.get('open_problem_count', 0)}**. "
        f"Multi-role counts show whether formalization co-occurs with proof generation—"
        f"see `by_ai_roles_multi` in `deep_audit_summary.json`."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DeepSeek deep audit of refined papers")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--source", default="refined", choices=["refined", "curated"])
    args = parser.parse_args(argv)
    run_deep_audit(
        model=args.model,
        workers=args.workers,
        limit=args.limit,
        force=args.force,
        source=args.source,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
