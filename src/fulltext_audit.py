"""Full-text DeepSeek audit for higher-precision AI-for-math labeling."""

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
from .fulltext import download_fulltext, load_text, sample_for_llm
from .llm_client import chat_json, get_deepseek_client
from .paths import ensure_data_dirs, resolve

SYSTEM_PROMPT = """You are auditing arXiv math papers for AI-assisted mathematics research.
You are given FULL TEXT excerpts (beginning + end of the paper), not only the abstract.
Be stricter and more evidence-based than abstract-only labeling.

Return ONLY JSON:
{
  "confirm_keep": boolean,
  "confirm_reason": string,
  "ai_roles": [string],
  "primary_ai_role": string,
  "ai_centrality": "core"|"substantial"|"peripheral"|"none",
  "human_ai_relation": "ai_led"|"human_led_ai_assist"|"joint"|"ai_method_only"|"none",
  "result_type": string,
  "proof_style": [string],
  "math_subfields": [string],
  "open_problem": boolean,
  "open_problem_name": string|null,
  "formal_system": [string],
  "models_mentioned": [string],
  "trend_tags": [string],
  "ai_usage_evidence": [string],     // short quotes or paraphrases of WHERE AI is used (max 4)
  "ai_usage_locations": [string],    // multi: abstract|introduction|methods|results|acknowledgements|appendix|footnote|elsewhere|not_found
  "writing_only": boolean,
  "confidence": number,
  "one_line_summary": string,
  "changed_from_abstract": boolean,  // true if full text clearly changes the abstract-level story
  "change_note": string              // what changed, or ""
}

ROLE values:
proof_generation, counterexample_search, formalization, conjecture_discovery,
exploration_search, verification_check, method_system_benchmark, code_numerics,
writing_only, none

RESULT values:
new_theorem, open_problem_resolution, improved_bound_construction,
formalization_of_known_result, method_or_system, benchmark_evaluation,
survey_position, educational_demo, other

PROOF values:
informal_natural_language, formal_machine_checked, computer_assisted_search,
probabilistic_method, constructive_example, olympiad_style, research_level_argument, none_or_na

SUBFIELD values:
combinatorics, number_theory, algebra, algebraic_geometry, topology_geometry,
analysis, probability_stats, logic_foundations, optimization, discrete_geometry,
graph_theory, dynamical_systems, mathematical_physics, cs_theory_adjacent,
general_or_multiple, other

Rules:
1) Prefer explicit full-text evidence (acknowledgements, methods, "we used ChatGPT/Claude/Lean+AI").
2) If AI is only for English polishing -> writing_only=true, confirm_keep=false.
3) Pure human Lean formalization with no AI -> confirm_keep=false.
4) Method/system papers about AI-for-math can keep=true.
5) Do not invent model names not present or clearly implied.
6) math_subfields: 1-3 best fits from the mathematical content, not just arXiv category.
"""


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _load_cache(path: Path) -> dict[str, dict[str, Any]]:
    out = {}
    for obj in _load_jsonl(path):
        if obj.get("arxiv_id"):
            out[obj["arxiv_id"]] = obj
    return out


def _normalize(raw: dict[str, Any], arxiv_id: str) -> dict[str, Any]:
    def as_list(v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        return [str(v)]

    keep = bool(raw.get("confirm_keep"))
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
        "ai_roles": as_list(raw.get("ai_roles")),
        "primary_ai_role": str(raw.get("primary_ai_role") or ("none" if not keep else "other")),
        "ai_centrality": centrality,
        "human_ai_relation": str(raw.get("human_ai_relation") or "none"),
        "result_type": str(raw.get("result_type") or "other"),
        "proof_style": as_list(raw.get("proof_style")),
        "math_subfields": as_list(raw.get("math_subfields"))[:3],
        "open_problem": bool(raw.get("open_problem")),
        "open_problem_name": raw.get("open_problem_name"),
        "formal_system": [x.lower() for x in as_list(raw.get("formal_system"))],
        "models_mentioned": [x.lower() for x in as_list(raw.get("models_mentioned"))],
        "trend_tags": as_list(raw.get("trend_tags"))[:10],
        "ai_usage_evidence": as_list(raw.get("ai_usage_evidence"))[:4],
        "ai_usage_locations": as_list(raw.get("ai_usage_locations"))[:8],
        "writing_only": bool(raw.get("writing_only")),
        "confidence": max(0.0, min(1.0, conf)),
        "one_line_summary": str(raw.get("one_line_summary") or "")[:400],
        "changed_from_abstract": bool(raw.get("changed_from_abstract")),
        "change_note": str(raw.get("change_note") or "")[:300],
        "audited_at": utc_now(),
        "audit_mode": "fulltext",
    }


def audit_fulltext(
    client: Any,
    item: dict[str, Any],
    text: str,
    *,
    model: str,
    max_chars: int,
) -> dict[str, Any]:
    excerpt = sample_for_llm(text, max_chars=max_chars)
    prior = {
        "prior_primary_ai_role": item.get("primary_ai_role"),
        "prior_result_type": item.get("result_type"),
        "prior_subfields": item.get("math_subfields"),
        "prior_confirm_reason": item.get("confirm_reason") or item.get("refine_reason"),
        "prior_one_line": item.get("one_line_summary"),
    }
    user = (
        f"arxiv_id: {item.get('arxiv_id')}\n"
        f"title: {item.get('title')}\n"
        f"published: {item.get('published')}\n"
        f"primary_category: {item.get('primary_category')}\n"
        f"prior_abstract_audit: {json.dumps(prior, ensure_ascii=False)}\n"
        f"FULL TEXT EXCERPT (head+tail, {len(excerpt)} chars):\n"
        f"-----\n{excerpt}\n-----\n"
        "Audit with full-text evidence. JSON only."
    )
    raw = chat_json(
        client,
        system=SYSTEM_PROMPT,
        user=user,
        model=model,
        temperature=0.05,
        max_tokens=1100,
    )
    return _normalize(raw, item["arxiv_id"])


def run_fulltext_pipeline(
    settings: dict[str, Any] | None = None,
    *,
    model: str = "deepseek-v4-flash",
    workers: int = 4,
    download_workers: int = 3,
    limit: int | None = None,
    force_download: bool = False,
    force_audit: bool = False,
    max_chars: int = 90000,
    download_delay: float = 1.0,
    source: str = "deep_confirmed",
) -> dict[str, Any]:
    settings = settings or load_settings()
    ensure_data_dirs(settings)
    curated = resolve(settings["paths"]["curated_dir"])
    downloads = resolve(settings["paths"]["downloads_dir"])
    stats = resolve(settings["paths"]["stats_dir"])
    docs = resolve("docs")

    src_map = {
        "deep_confirmed": curated / "deep_confirmed.jsonl",
        "refined": curated / "refined.jsonl",
    }
    src_path = src_map.get(source, curated / "deep_confirmed.jsonl")
    papers = _load_jsonl(src_path)
    if not papers:
        raise FileNotFoundError(f"No papers in {src_path}")
    if limit is not None:
        papers = papers[:limit]

    # ---- Stage 1: download ----
    print(f"Downloading full text for {len(papers)} papers -> {downloads}")
    dl_meta: dict[str, dict[str, Any]] = {}
    dl_cache_path = curated / "fulltext_download_meta.jsonl"
    existing_meta = {} if force_download else _load_cache(dl_cache_path)

    def dl_one(p: dict[str, Any]) -> dict[str, Any]:
        aid = p["arxiv_id"]
        if aid in existing_meta and existing_meta[aid].get("ok") and not force_download:
            return existing_meta[aid]
        meta = download_fulltext(
            aid, downloads, delay=download_delay, force=force_download
        )
        return meta

    with ThreadPoolExecutor(max_workers=max(1, download_workers)) as ex:
        futs = {ex.submit(dl_one, p): p for p in papers}
        for fut in tqdm(as_completed(futs), total=len(futs), desc="download"):
            p = futs[fut]
            try:
                meta = fut.result()
            except Exception as e:  # noqa: BLE001
                meta = {
                    "arxiv_id": p["arxiv_id"],
                    "ok": False,
                    "error": f"{type(e).__name__}: {e}",
                    "chars": 0,
                }
            dl_meta[p["arxiv_id"]] = meta
            if p["arxiv_id"] not in existing_meta or force_download:
                _append_jsonl(dl_cache_path, meta)

    ok_dl = sum(1 for m in dl_meta.values() if m.get("ok"))
    print(f"Download OK: {ok_dl}/{len(papers)}")

    # ---- Stage 2: LLM fulltext audit ----
    cache_path = curated / "fulltext_audit_cache.jsonl"
    out_path = curated / "fulltext_audit.jsonl"
    confirmed_path = curated / "fulltext_confirmed.jsonl"
    demoted_path = curated / "fulltext_demoted.jsonl"
    summary_path = curated / "fulltext_audit_summary.json"
    compare_path = curated / "fulltext_vs_abstract.json"
    report_path = docs / "fulltext_audit_report.md"

    cache = {} if force_audit else _load_cache(cache_path)
    if force_audit and cache_path.exists():
        # keep file but ignore; rewrite by appending only new — cleaner to unlink
        cache_path.unlink()
        cache = {}

    client = get_deepseek_client()
    results: dict[str, dict[str, Any]] = {}
    todo: list[tuple[dict[str, Any], str]] = []

    for p in papers:
        aid = p["arxiv_id"]
        if aid in cache:
            results[aid] = cache[aid]
            continue
        meta = dl_meta.get(aid) or {}
        txt = meta.get("txt_path")
        if not meta.get("ok") or not txt or not Path(txt).exists():
            results[aid] = {
                "arxiv_id": aid,
                "confirm_keep": False,
                "confirm_reason": f"fulltext unavailable: {meta.get('error')}",
                "primary_ai_role": "none",
                "ai_centrality": "none",
                "human_ai_relation": "none",
                "result_type": "other",
                "ai_roles": [],
                "proof_style": [],
                "math_subfields": [],
                "open_problem": False,
                "open_problem_name": None,
                "formal_system": [],
                "models_mentioned": [],
                "trend_tags": [],
                "ai_usage_evidence": [],
                "ai_usage_locations": ["not_found"],
                "writing_only": False,
                "confidence": 0.1,
                "one_line_summary": "fulltext missing",
                "changed_from_abstract": True,
                "change_note": "could not load full text",
                "audited_at": utc_now(),
                "audit_mode": "fulltext_failed",
                "model": model,
            }
            _append_jsonl(cache_path, results[aid])
            continue
        text = load_text(Path(txt))
        if len(text) < 500:
            results[aid] = {
                "arxiv_id": aid,
                "confirm_keep": bool(p.get("confirm_keep", True)),
                "confirm_reason": "fulltext too short; kept prior abstract decision conservatively",
                "primary_ai_role": p.get("primary_ai_role") or "unknown",
                "ai_centrality": p.get("ai_centrality") or "unknown",
                "human_ai_relation": p.get("human_ai_relation") or "unknown",
                "result_type": p.get("result_type") or "other",
                "ai_roles": p.get("ai_roles") or [],
                "proof_style": p.get("proof_style") or [],
                "math_subfields": p.get("math_subfields") or [],
                "open_problem": bool(p.get("open_problem")),
                "open_problem_name": p.get("open_problem_name"),
                "formal_system": p.get("formal_system") or [],
                "models_mentioned": p.get("models_mentioned") or [],
                "trend_tags": p.get("trend_tags") or [],
                "ai_usage_evidence": [],
                "ai_usage_locations": ["not_found"],
                "writing_only": False,
                "confidence": 0.3,
                "one_line_summary": p.get("one_line_summary") or "",
                "changed_from_abstract": False,
                "change_note": "short fulltext",
                "audited_at": utc_now(),
                "audit_mode": "fulltext_short",
                "model": model,
            }
            _append_jsonl(cache_path, results[aid])
            continue
        todo.append((p, text))

    print(f"Fulltext LLM audit todo={len(todo)} cached={len(results)}")

    def work(pair: tuple[dict[str, Any], str]) -> dict[str, Any]:
        p, text = pair
        row = audit_fulltext(client, p, text, model=model, max_chars=max_chars)
        row["model"] = model
        row["fulltext_chars"] = len(text)
        row["fulltext_source"] = (dl_meta.get(p["arxiv_id"]) or {}).get("source")
        return row

    errors = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {ex.submit(work, pair): pair[0] for pair in todo}
        for fut in tqdm(as_completed(futs), total=len(futs), desc="fulltext-audit"):
            p = futs[fut]
            try:
                row = fut.result()
            except Exception as e:  # noqa: BLE001
                errors += 1
                row = {
                    "arxiv_id": p["arxiv_id"],
                    "confirm_keep": True,
                    "confirm_reason": f"llm error: {type(e).__name__}",
                    "primary_ai_role": p.get("primary_ai_role") or "unknown",
                    "ai_centrality": p.get("ai_centrality") or "unknown",
                    "human_ai_relation": p.get("human_ai_relation") or "unknown",
                    "result_type": p.get("result_type") or "other",
                    "ai_roles": p.get("ai_roles") or [],
                    "proof_style": p.get("proof_style") or [],
                    "math_subfields": p.get("math_subfields") or [],
                    "open_problem": bool(p.get("open_problem")),
                    "open_problem_name": p.get("open_problem_name"),
                    "formal_system": p.get("formal_system") or [],
                    "models_mentioned": p.get("models_mentioned") or [],
                    "trend_tags": [],
                    "ai_usage_evidence": [],
                    "ai_usage_locations": [],
                    "writing_only": False,
                    "confidence": 0.2,
                    "one_line_summary": "fulltext audit failed; retained abstract prior",
                    "changed_from_abstract": False,
                    "change_note": str(e)[:200],
                    "audited_at": utc_now(),
                    "audit_mode": "fulltext_error",
                    "model": model,
                }
            results[p["arxiv_id"]] = row
            _append_jsonl(cache_path, row)

    print(f"LLM errors: {errors}")

    # merge + export
    merged: list[dict[str, Any]] = []
    confirmed: list[dict[str, Any]] = []
    demoted: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []

    for p in papers:
        a = results.get(p["arxiv_id"], {})
        row = {
            **p,
            "ft_confirm_keep": a.get("confirm_keep"),
            "ft_confirm_reason": a.get("confirm_reason"),
            "ft_primary_ai_role": a.get("primary_ai_role"),
            "ft_ai_roles": a.get("ai_roles"),
            "ft_ai_centrality": a.get("ai_centrality"),
            "ft_human_ai_relation": a.get("human_ai_relation"),
            "ft_result_type": a.get("result_type"),
            "ft_proof_style": a.get("proof_style"),
            "ft_math_subfields": a.get("math_subfields"),
            "ft_open_problem": a.get("open_problem"),
            "ft_open_problem_name": a.get("open_problem_name"),
            "ft_formal_system": a.get("formal_system"),
            "ft_models_mentioned": a.get("models_mentioned"),
            "ft_trend_tags": a.get("trend_tags"),
            "ft_ai_usage_evidence": a.get("ai_usage_evidence"),
            "ft_ai_usage_locations": a.get("ai_usage_locations"),
            "ft_writing_only": a.get("writing_only"),
            "ft_confidence": a.get("confidence"),
            "ft_one_line_summary": a.get("one_line_summary"),
            "ft_changed_from_abstract": a.get("changed_from_abstract"),
            "ft_change_note": a.get("change_note"),
            "ft_audit_mode": a.get("audit_mode"),
            "ft_model": a.get("model"),
            "fulltext_chars": a.get("fulltext_chars") or (dl_meta.get(p["arxiv_id"]) or {}).get("chars"),
            "fulltext_source": a.get("fulltext_source") or (dl_meta.get(p["arxiv_id"]) or {}).get("source"),
        }
        # promote fulltext labels as canonical for keep-set
        if a.get("confirm_keep"):
            row["primary_ai_role"] = a.get("primary_ai_role")
            row["ai_roles"] = a.get("ai_roles")
            row["ai_centrality"] = a.get("ai_centrality")
            row["human_ai_relation"] = a.get("human_ai_relation")
            row["result_type"] = a.get("result_type")
            row["proof_style"] = a.get("proof_style")
            row["math_subfields"] = a.get("math_subfields")
            row["open_problem"] = a.get("open_problem")
            row["open_problem_name"] = a.get("open_problem_name")
            row["formal_system"] = a.get("formal_system")
            row["models_mentioned"] = a.get("models_mentioned")
            row["trend_tags"] = a.get("trend_tags")
            row["one_line_summary"] = a.get("one_line_summary")
            row["confirm_keep"] = True
            row["confirm_reason"] = a.get("confirm_reason")
            confirmed.append(row)
        else:
            row["confirm_keep"] = False
            demoted.append(row)

        comparisons.append(
            {
                "arxiv_id": p["arxiv_id"],
                "title": p.get("title"),
                "abs_role": p.get("primary_ai_role"),
                "ft_role": a.get("primary_ai_role"),
                "abs_result": p.get("result_type"),
                "ft_result": a.get("result_type"),
                "abs_subfields": p.get("math_subfields"),
                "ft_subfields": a.get("math_subfields"),
                "abs_keep": True,  # input was deep_confirmed
                "ft_keep": a.get("confirm_keep"),
                "changed": a.get("changed_from_abstract"),
                "change_note": a.get("change_note"),
                "ft_writing_only": a.get("writing_only"),
                "ft_confidence": a.get("confidence"),
            }
        )
        merged.append(row)

    with out_path.open("w", encoding="utf-8") as f:
        for row in merged:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with confirmed_path.open("w", encoding="utf-8") as f:
        for row in confirmed:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with demoted_path.open("w", encoding="utf-8") as f:
        for row in demoted:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with compare_path.open("w", encoding="utf-8") as f:
        json.dump(comparisons, f, indent=2, ensure_ascii=False)

    summary = build_summary(confirmed, demoted, comparisons, model=model, ok_dl=ok_dl, n=len(papers))
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    export_stats(confirmed, stats)
    write_report(summary, confirmed, demoted, comparisons, report_path)

    # dashboard canonical set
    with (curated / "curated.jsonl").open("w", encoding="utf-8") as f:
        for row in confirmed:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (curated / "curated_summary.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "count": len(confirmed),
                "source": "fulltext_audit",
                "demoted_from_deep": len(demoted),
                "by_primary_ai_role": summary["by_primary_ai_role"],
                "by_subfield": summary["by_subfield"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(json.dumps({
        "input": len(papers),
        "download_ok": ok_dl,
        "confirmed": len(confirmed),
        "demoted": len(demoted),
        "role_flip": summary.get("role_changed_count"),
        "keep_flip_to_drop": summary.get("keep_to_drop"),
        "by_primary_ai_role": summary.get("by_primary_ai_role"),
        "by_subfield_top": dict(list((summary.get("by_subfield") or {}).items())[:10]),
        "open_problem_count": summary.get("open_problem_count"),
    }, indent=2, ensure_ascii=False))
    print(f"Report -> {report_path}")
    return summary


def build_summary(
    confirmed: list[dict[str, Any]],
    demoted: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    *,
    model: str,
    ok_dl: int,
    n: int,
) -> dict[str, Any]:
    def count_field(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        return dict(Counter(str(r.get(key) or "unknown") for r in rows))

    def count_list(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        c: Counter[str] = Counter()
        for r in rows:
            vals = r.get(key) or []
            if isinstance(vals, list):
                for v in vals:
                    c[str(v)] += 1
        return dict(c.most_common())

    yearly: Counter[str] = Counter()
    yearly_role: dict[str, Counter[str]] = defaultdict(Counter)
    yearly_sub: dict[str, Counter[str]] = defaultdict(Counter)
    for r in confirmed:
        y = (r.get("published") or "")[:4] or "unknown"
        yearly[y] += 1
        yearly_role[y][str(r.get("primary_ai_role") or "unknown")] += 1
        subs = r.get("math_subfields") or r.get("ft_math_subfields") or []
        if isinstance(subs, list) and subs:
            yearly_sub[y][str(subs[0])] += 1

    role_changed = sum(
        1
        for c in comparisons
        if c.get("ft_keep") and c.get("abs_role") and c.get("ft_role") and c.get("abs_role") != c.get("ft_role")
    )
    keep_to_drop = sum(1 for c in comparisons if c.get("abs_keep") and not c.get("ft_keep"))
    writing_only_drop = sum(1 for d in demoted if d.get("ft_writing_only"))

    open_problems = [
        {
            "arxiv_id": r.get("arxiv_id"),
            "title": r.get("title"),
            "name": r.get("open_problem_name") or r.get("ft_open_problem_name"),
            "primary_ai_role": r.get("primary_ai_role"),
            "subfields": r.get("math_subfields"),
            "evidence": r.get("ft_ai_usage_evidence") or r.get("ai_usage_evidence"),
            "url": r.get("url") or f"https://arxiv.org/abs/{r.get('arxiv_id')}",
        }
        for r in confirmed
        if r.get("open_problem") or r.get("ft_open_problem")
    ]

    # situation matrix: role x subfield
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for r in confirmed:
        role = str(r.get("primary_ai_role") or "unknown")
        subs = r.get("math_subfields") or []
        if isinstance(subs, list) and subs:
            for s in subs[:2]:
                matrix[str(s)][role] += 1
        else:
            matrix["unknown"][role] += 1

    return {
        "generated_at": utc_now(),
        "model": model,
        "input": n,
        "download_ok": ok_dl,
        "confirmed": len(confirmed),
        "demoted": len(demoted),
        "role_changed_count": role_changed,
        "keep_to_drop": keep_to_drop,
        "writing_only_demoted": writing_only_drop,
        "by_primary_ai_role": count_field(confirmed, "primary_ai_role"),
        "by_ai_roles_multi": count_list(confirmed, "ai_roles"),
        "by_centrality": count_field(confirmed, "ai_centrality"),
        "by_human_ai_relation": count_field(confirmed, "human_ai_relation"),
        "by_result_type": count_field(confirmed, "result_type"),
        "by_proof_style_multi": count_list(confirmed, "proof_style"),
        "by_subfield": count_list(confirmed, "math_subfields"),
        "by_formal_system": count_list(confirmed, "formal_system"),
        "by_models": count_list(confirmed, "models_mentioned"),
        "by_usage_locations": count_list(confirmed, "ft_ai_usage_locations"),
        "yearly_counts": dict(sorted(yearly.items())),
        "yearly_primary_role": {y: dict(c) for y, c in sorted(yearly_role.items())},
        "yearly_top_subfield": {y: dict(c) for y, c in sorted(yearly_sub.items())},
        "role_by_subfield": {s: dict(c) for s, c in matrix.items()},
        "open_problem_count": len(open_problems),
        "open_problems": open_problems[:60],
        "mean_confidence": (
            sum(float(r.get("ft_confidence") or r.get("confidence") or 0) for r in confirmed)
            / len(confirmed)
            if confirmed
            else 0
        ),
        "demote_samples": [
            {
                "arxiv_id": d.get("arxiv_id"),
                "title": d.get("title"),
                "reason": d.get("ft_confirm_reason") or d.get("confirm_reason"),
                "writing_only": d.get("ft_writing_only"),
            }
            for d in demoted[:30]
        ],
    }


def export_stats(confirmed: list[dict[str, Any]], stats_dir: Path) -> None:
    if not confirmed:
        return
    rows = []
    for r in confirmed:
        pub = r.get("published") or ""
        subs = r.get("math_subfields") or []
        primary_sub = subs[0] if isinstance(subs, list) and subs else "unknown"
        rows.append(
            {
                "arxiv_id": r.get("arxiv_id"),
                "title": r.get("title"),
                "published": pub,
                "year": pub[:4] if len(pub) >= 4 else None,
                "year_month": pub[:7] if len(pub) >= 7 else None,
                "primary_ai_role": r.get("primary_ai_role"),
                "ai_centrality": r.get("ai_centrality"),
                "result_type": r.get("result_type"),
                "primary_subfield": primary_sub,
                "open_problem": bool(r.get("open_problem")),
                "url": r.get("url") or f"https://arxiv.org/abs/{r.get('arxiv_id')}",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(stats_dir / "fulltext_papers.csv", index=False)
    df.to_csv(stats_dir / "deep_papers.csv", index=False)

    if "year" in df.columns:
        df.groupby(["year", "primary_ai_role"]).size().reset_index(name="count").to_csv(
            stats_dir / "deep_yearly_role.csv", index=False
        )
        df.groupby(["year", "primary_subfield"]).size().reset_index(name="count").to_csv(
            stats_dir / "deep_yearly_subfield.csv", index=False
        )
        df.groupby(["year", "result_type"]).size().reset_index(name="count").to_csv(
            stats_dir / "deep_yearly_result.csv", index=False
        )
        df.groupby("year").size().reset_index(name="count").to_csv(
            stats_dir / "yearly_counts.csv", index=False
        )

    if "year_month" in df.columns:
        monthly = (
            df.dropna(subset=["year_month"])
            .groupby("year_month")
            .size()
            .reset_index(name="count")
            .sort_values("year_month")
        )
        level_map = {
            "core": "L3",
            "substantial": "L2",
            "peripheral": "L1",
            "none": "L0",
            "unknown": "L1",
        }
        df["level"] = df["ai_centrality"].map(lambda x: level_map.get(str(x), "L1"))
        pivot = df.pivot_table(
            index="year_month", columns="level", values="arxiv_id", aggfunc="count", fill_value=0
        ).reset_index()
        base = monthly.merge(pivot, on="year_month", how="left")
        for col in ("L0", "L1", "L2", "L3"):
            if col not in base.columns:
                base[col] = 0
        base.to_csv(stats_dir / "monthly_counts.csv", index=False)

    cats = (
        df["primary_subfield"].fillna("unknown").value_counts().rename_axis("primary_category")
        .reset_index(name="count")
    )
    cats.to_csv(stats_dir / "category_counts.csv", index=False)
    df.sort_values(["open_problem", "year"], ascending=[False, False]).head(100).to_csv(
        stats_dir / "top_papers.csv", index=False
    )

    summary = {
        "total_candidates": int(len(df)),
        "by_level": df["level"].value_counts().to_dict() if "level" in df else {},
        "writing_only": 0,
        "date_min": str(df["published"].min()) if len(df) else None,
        "date_max": str(df["published"].max()) if len(df) else None,
        "source": "fulltext_audit",
    }
    with (stats_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # also dump role-by-subfield matrix
    with (stats_dir / "fulltext_summary.json").open("w", encoding="utf-8") as f:
        json.dump({"count": len(df), "source": "fulltext"}, f)


def write_report(
    summary: dict[str, Any],
    confirmed: list[dict[str, Any]],
    demoted: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Full-Text DeepSeek Audit Report",
        "",
        f"- Generated: `{summary.get('generated_at')}`",
        f"- Model: `{summary.get('model')}`",
        f"- Input: **{summary.get('input')}** | download OK: **{summary.get('download_ok')}**",
        f"- Confirmed after full text: **{summary.get('confirmed')}** | demoted: **{summary.get('demoted')}**",
        f"- Keep→drop flips: **{summary.get('keep_to_drop')}** | role changes: **{summary.get('role_changed_count')}**",
        f"- Writing-only demotions: **{summary.get('writing_only_demoted')}**",
        f"- Open-problem linked: **{summary.get('open_problem_count')}**",
        "",
        "## Stance / method",
        "",
        "Full text (PDF/HTML extract, head+tail) is more reliable than abstract-only for:",
        "- distinguishing **writing help** vs **proof contribution**",
        "- finding AI mentions in **acknowledgements / methods / appendices**",
        "- refining **subfield** from actual mathematical content",
        "",
        "Remaining limits: OCR/extraction errors; truncated middles; undisclosed AI use still invisible.",
        "",
        "## 1. AI usage (primary role)",
        "",
    ]
    for k, v in sorted((summary.get("by_primary_ai_role") or {}).items(), key=lambda x: -x[1]):
        lines.append(f"- **{k}**: {v}")
    lines += ["", "### Multi-label roles", ""]
    for k, v in list((summary.get("by_ai_roles_multi") or {}).items())[:15]:
        lines.append(f"- {k}: {v}")
    lines += ["", "## 2. Where AI is mentioned in the paper", ""]
    for k, v in list((summary.get("by_usage_locations") or {}).items())[:15]:
        lines.append(f"- {k}: {v}")
    lines += ["", "## 3. Subfields", ""]
    for k, v in list((summary.get("by_subfield") or {}).items())[:20]:
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## 4. Role × subfield (situation matrix)", ""]
    for sub, roles in sorted(
        (summary.get("role_by_subfield") or {}).items(),
        key=lambda x: -sum(x[1].values()),
    )[:15]:
        top = ", ".join(f"{r}:{c}" for r, c in sorted(roles.items(), key=lambda x: -x[1])[:4])
        lines.append(f"- **{sub}**: {top}")
    lines += ["", "## 5. Result / proof morphology", ""]
    for k, v in (summary.get("by_result_type") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "### Proof style", ""]
    for k, v in list((summary.get("by_proof_style_multi") or {}).items())[:12]:
        lines.append(f"- {k}: {v}")
    lines += ["", "## 6. Yearly volume", ""]
    for y, n in (summary.get("yearly_counts") or {}).items():
        lines.append(f"- **{y}**: {n}")
    lines += ["", "### Year × primary role", ""]
    for y, d in (summary.get("yearly_primary_role") or {}).items():
        lines.append(f"- **{y}**: {d}")
    lines += ["", "## 7. Models & formal systems", ""]
    for k, v in list((summary.get("by_models") or {}).items())[:20]:
        lines.append(f"- {k}: {v}")
    lines += ["", "### Formal", ""]
    for k, v in list((summary.get("by_formal_system") or {}).items())[:10]:
        lines.append(f"- {k}: {v}")
    lines += ["", "## 8. Open problems (sample)", ""]
    for op in (summary.get("open_problems") or [])[:25]:
        lines.append(
            f"- [{op.get('arxiv_id')}]({op.get('url')}) — {op.get('name') or 'open problem'}  \n"
            f"  _{op.get('title')}_  \n"
            f"  role=`{op.get('primary_ai_role')}` sub=`{op.get('subfields')}`"
        )
    lines += ["", "## 9. Demoted after full text (sample)", ""]
    for d in (summary.get("demote_samples") or [])[:20]:
        lines.append(
            f"- `{d.get('arxiv_id')}` writing_only={d.get('writing_only')}: {d.get('reason')}  \n"
            f"  _{str(d.get('title') or '')[:100]}_"
        )
    lines += ["", "## 10. Abstract vs full-text flips (sample)", ""]
    flips = [c for c in comparisons if (not c.get("ft_keep")) or c.get("abs_role") != c.get("ft_role")]
    for c in flips[:25]:
        lines.append(
            f"- `{c.get('arxiv_id')}` keep {c.get('abs_keep')}→{c.get('ft_keep')}; "
            f"role {c.get('abs_role')}→{c.get('ft_role')}  \n"
            f"  {c.get('change_note') or ''} | _{str(c.get('title') or '')[:90]}_"
        )
    lines += [
        "",
        "## 11. Bottom-line trend reading",
        "",
        _narrative(summary),
        "",
        "---",
        "PDFs cached under `data/downloads/` (local only). Labels via DeepSeek V4 Flash full-text excerpts.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _narrative(summary: dict[str, Any]) -> str:
    yearly = summary.get("yearly_counts") or {}
    roles = summary.get("by_primary_ai_role") or {}
    subs = summary.get("by_subfield") or {}
    ys = sorted(yearly)
    growth = ""
    if len(ys) >= 2:
        growth = f"Volume {ys[0]}:{yearly[ys[0]]} → {ys[-1]}:{yearly[ys[-1]]}. "
    top_role = max(roles, key=roles.get) if roles else "n/a"
    top_sub = max(subs, key=subs.get) if subs else "n/a"
    return (
        f"{growth}"
        f"After full-text review, dominant primary role is **{top_role}**; "
        f"densest subfield is **{top_sub}**. "
        f"Keep→drop flips: {summary.get('keep_to_drop')} "
        f"(incl. writing-only {summary.get('writing_only_demoted')}). "
        f"Open-problem-linked: {summary.get('open_problem_count')}. "
        f"Use role×subfield matrix for situation-specific conclusions."
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Full-text download + DeepSeek audit")
    p.add_argument("--model", default="deepseek-v4-flash")
    p.add_argument("--workers", type=int, default=4, help="LLM concurrency")
    p.add_argument("--download-workers", type=int, default=3)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--force-download", action="store_true")
    p.add_argument("--force-audit", action="store_true")
    p.add_argument("--max-chars", type=int, default=90000)
    p.add_argument("--download-delay", type=float, default=1.0)
    p.add_argument("--source", default="deep_confirmed", choices=["deep_confirmed", "refined"])
    args = p.parse_args(argv)
    run_fulltext_pipeline(
        model=args.model,
        workers=args.workers,
        download_workers=args.download_workers,
        limit=args.limit,
        force_download=args.force_download,
        force_audit=args.force_audit,
        max_chars=args.max_chars,
        download_delay=args.download_delay,
        source=args.source,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
