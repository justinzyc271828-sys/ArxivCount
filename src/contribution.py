"""Strict contribution-tier labeling (C0–C4) on fulltext-confirmed papers."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from tqdm import tqdm

from .config import load_settings
from .db import utc_now
from .fulltext import load_text, sample_for_llm
from .llm_client import chat_json, get_deepseek_client
from .paths import ROOT, ensure_data_dirs, resolve

SYSTEM = """You grade AI's MATHEMATICAL contribution in an arXiv paper.
Use FULL TEXT excerpt when provided; otherwise title+abstract+prior labels.

Return ONLY JSON:
{
  "tier": "C0"|"C1"|"C2"|"C3"|"C4",
  "tier_reason": string,                 // <= 35 words, evidence-based
  "capabilities": [string],              // from list below
  "decisive_for_main_result": boolean,
  "named_open_problem": boolean,
  "open_problem_name": string|null,
  "human_role": "essential"|"primary"|"joint"|"secondary"|"unclear",
  "ai_role_summary": string,             // <= 30 words: what AI actually did
  "milestone_candidate": boolean,        // community-visible breakthrough writeup?
  "milestone_label": string|null,        // short label if yes
  "dirty_data_risk": "low"|"medium"|"high",  // extraction/label uncertainty
  "confidence": number,
  "quote_evidence": [string]             // <=3 short evidence snippets
}

Tiers (strict):
- C0 noise/false positive (not really AI-for-math contribution)
- C1 writing/peripheral only
- C2 assistive, not decisive for main math claim
- C3 material contribution to a real math result (lemma/counterexample/construction/formal proof)
- C4 decisive role in named open problem / major breakthrough writeup

Capabilities:
prose_editing, code_generation, example_search, lemma_suggestion, full_proof_draft,
counterexample_construction, conjecture_proposal, large_scale_search_evolution,
autoformalization, formal_proof_search, verification_bugfinding, method_or_benchmark_only

Rules:
1) Method/benchmark-only papers that do not claim a new math theorem: usually C2 if they advance AI-for-math tools; C1/C0 if peripheral. Rarely C3/C4.
2) "We used ChatGPT for writing" alone => C1.
3) AI found a counterexample/proof of a named conjecture the authors adopt => C3 or C4.
4) Prefer lower tier when uncertain between two levels.
5) milestone_candidate=true only for unusually visible breakthroughs or primary writeups of them.
"""


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _append(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _cache(path: Path) -> dict[str, dict[str, Any]]:
    return {r["arxiv_id"]: r for r in _load_jsonl(path) if r.get("arxiv_id")}


def _load_taxonomy() -> dict[str, Any]:
    p = ROOT / "config" / "contribution_taxonomy.yaml"
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def grade_one(
    client: Any,
    paper: dict[str, Any],
    *,
    model: str,
    downloads: Path,
    max_chars: int = 45000,
) -> dict[str, Any]:
    aid = paper["arxiv_id"]
    safe = aid.replace("/", "_")
    txt = downloads / f"{safe}.txt"
    body = ""
    if txt.exists():
        # prefer smaller window for speed/reliability; head+tail still covers ack/methods
        body = sample_for_llm(load_text(txt), max_chars=max_chars)
    user = (
        f"arxiv_id: {aid}\n"
        f"title: {paper.get('title')}\n"
        f"published: {paper.get('published')}\n"
        f"prior_primary_ai_role: {paper.get('primary_ai_role')}\n"
        f"prior_result_type: {paper.get('result_type')}\n"
        f"prior_subfields: {paper.get('math_subfields')}\n"
        f"prior_open_problem: {paper.get('open_problem')} {paper.get('open_problem_name')}\n"
        f"prior_summary: {paper.get('one_line_summary') or paper.get('ft_one_line_summary')}\n"
        f"prior_evidence: {paper.get('ft_ai_usage_evidence')}\n"
    )
    if body:
        user += f"FULL TEXT EXCERPT:\n-----\n{body}\n-----\n"
    else:
        user += f"abstract: {(paper.get('abstract') or '')[:2000]}\n"
    user += "Grade contribution tier. JSON only."

    raw = chat_json(
        client,
        system=SYSTEM,
        user=user,
        model=model,
        temperature=0.05,
        max_tokens=900,
    )
    tier = str(raw.get("tier") or "C2").upper()
    if tier not in {"C0", "C1", "C2", "C3", "C4"}:
        tier = "C2"
    try:
        conf = float(raw.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    caps = raw.get("capabilities") or []
    if not isinstance(caps, list):
        caps = [str(caps)]
    quotes = raw.get("quote_evidence") or []
    if not isinstance(quotes, list):
        quotes = [str(quotes)]

    return {
        "arxiv_id": aid,
        "tier": tier,
        "tier_reason": str(raw.get("tier_reason") or "")[:400],
        "capabilities": [str(c) for c in caps][:8],
        "decisive_for_main_result": bool(raw.get("decisive_for_main_result")),
        "named_open_problem": bool(raw.get("named_open_problem")),
        "open_problem_name": raw.get("open_problem_name"),
        "human_role": str(raw.get("human_role") or "unclear"),
        "ai_role_summary": str(raw.get("ai_role_summary") or "")[:400],
        "milestone_candidate": bool(raw.get("milestone_candidate")),
        "milestone_label": raw.get("milestone_label"),
        "dirty_data_risk": str(raw.get("dirty_data_risk") or "medium"),
        "confidence": max(0.0, min(1.0, conf)),
        "quote_evidence": [str(q)[:240] for q in quotes][:3],
        "model": model,
        "graded_at": utc_now(),
    }


def run_contribution(
    *,
    model: str = "deepseek-v4-flash",
    workers: int = 5,
    limit: int | None = None,
    force: bool = False,
) -> dict[str, Any]:
    settings = load_settings()
    ensure_data_dirs(settings)
    curated = resolve(settings["paths"]["curated_dir"])
    downloads = resolve(settings["paths"]["downloads_dir"])
    stats = resolve(settings["paths"]["stats_dir"])
    docs = resolve("docs")
    taxonomy = _load_taxonomy()

    src = curated / "fulltext_confirmed.jsonl"
    papers = _load_jsonl(src)
    if not papers:
        raise FileNotFoundError(src)
    if limit:
        papers = papers[:limit]

    cache_path = curated / "contribution_cache.jsonl"
    cache = {} if force else _cache(cache_path)
    if force and cache_path.exists():
        cache_path.unlink()
        cache = {}

    client = get_deepseek_client()
    results: dict[str, dict[str, Any]] = {}
    todo = []
    for p in papers:
        aid = p["arxiv_id"]
        if aid in cache:
            results[aid] = cache[aid]
        else:
            todo.append(p)

    print(f"Contribution grading: total={len(papers)} cached={len(results)} todo={len(todo)}")

    def work(p: dict[str, Any]) -> dict[str, Any]:
        return grade_one(client, p, model=model, downloads=downloads)

    errors = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {ex.submit(work, p): p for p in todo}
        for fut in tqdm(as_completed(futs), total=len(futs), desc="contrib"):
            p = futs[fut]
            try:
                row = fut.result()
            except Exception as e:  # noqa: BLE001
                errors += 1
                row = {
                    "arxiv_id": p["arxiv_id"],
                    "tier": "C2",
                    "tier_reason": f"grade error: {type(e).__name__}",
                    "capabilities": [],
                    "decisive_for_main_result": False,
                    "named_open_problem": bool(p.get("open_problem")),
                    "open_problem_name": p.get("open_problem_name"),
                    "human_role": "unclear",
                    "ai_role_summary": "",
                    "milestone_candidate": False,
                    "milestone_label": None,
                    "dirty_data_risk": "high",
                    "confidence": 0.2,
                    "quote_evidence": [],
                    "model": model,
                    "graded_at": utc_now(),
                }
            results[p["arxiv_id"]] = row
            _append(cache_path, row)
    print("errors", errors)

    # merge
    merged = []
    for p in papers:
        g = results[p["arxiv_id"]]
        tier = g["tier"]
        wide = tier in {"C2", "C3", "C4"}
        strict = tier in {"C3", "C4"}
        row = {
            **p,
            **{f"contrib_{k}": v for k, v in g.items() if k != "arxiv_id"},
            "contribution_tier": tier,
            "in_wide_set": wide,
            "in_strict_set": strict,
            "milestone_candidate": g.get("milestone_candidate"),
            "milestone_label": g.get("milestone_label"),
            "capabilities": g.get("capabilities"),
            "ai_role_summary": g.get("ai_role_summary"),
            "tier_reason": g.get("tier_reason"),
            "dirty_data_risk": g.get("dirty_data_risk"),
            "contrib_confidence": g.get("confidence"),
        }
        merged.append(row)

    out_all = curated / "contribution_graded.jsonl"
    out_wide = curated / "set_wide.jsonl"
    out_strict = curated / "set_strict.jsonl"
    out_c4 = curated / "set_c4_milestones.jsonl"

    wide = [r for r in merged if r["in_wide_set"]]
    strict = [r for r in merged if r["in_strict_set"]]
    c4 = [r for r in merged if r["contribution_tier"] == "C4" or r.get("milestone_candidate")]

    for path, rows in [
        (out_all, merged),
        (out_wide, wide),
        (out_strict, strict),
        (out_c4, c4),
    ]:
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # summary
    by_tier = dict(Counter(r["contribution_tier"] for r in merged))
    yearly_tier: dict[str, Counter[str]] = defaultdict(Counter)
    yearly_strict: Counter[str] = Counter()
    yearly_wide: Counter[str] = Counter()
    cap_c: Counter[str] = Counter()
    for r in merged:
        y = (r.get("published") or "")[:4] or "unknown"
        yearly_tier[y][r["contribution_tier"]] += 1
        if r["in_wide_set"]:
            yearly_wide[y] += 1
        if r["in_strict_set"]:
            yearly_strict[y] += 1
        for c in r.get("capabilities") or []:
            cap_c[str(c)] += 1

    summary = {
        "generated_at": utc_now(),
        "model": model,
        "n": len(merged),
        "by_tier": by_tier,
        "wide_n": len(wide),
        "strict_n": len(strict),
        "c4_or_milestone_n": len(c4),
        "yearly_tier": {y: dict(c) for y, c in sorted(yearly_tier.items())},
        "yearly_wide": dict(sorted(yearly_wide.items())),
        "yearly_strict": dict(sorted(yearly_strict.items())),
        "capabilities": dict(cap_c.most_common()),
        "dirty_risk": dict(Counter(r.get("dirty_data_risk") for r in merged)),
        "mean_confidence": sum(float(r.get("contrib_confidence") or 0) for r in merged) / max(1, len(merged)),
        "taxonomy_version": taxonomy.get("version"),
    }
    with (curated / "contribution_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # stats tables for charts
    rows = []
    for r in merged:
        pub = r.get("published") or ""
        rows.append(
            {
                "arxiv_id": r.get("arxiv_id"),
                "title": r.get("title"),
                "published": pub,
                "year": pub[:4] if len(pub) >= 4 else None,
                "year_month": pub[:7] if len(pub) >= 7 else None,
                "contribution_tier": r.get("contribution_tier"),
                "in_wide_set": r.get("in_wide_set"),
                "in_strict_set": r.get("in_strict_set"),
                "milestone_candidate": r.get("milestone_candidate"),
                "primary_ai_role": r.get("primary_ai_role"),
                "primary_subfield": (r.get("math_subfields") or ["unknown"])[0]
                if isinstance(r.get("math_subfields"), list) and r.get("math_subfields")
                else "unknown",
                "open_problem": bool(r.get("named_open_problem") or r.get("open_problem")),
                "url": r.get("url") or f"https://arxiv.org/abs/{r.get('arxiv_id')}",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(stats / "contribution_papers.csv", index=False)
    if not df.empty:
        df.groupby(["year", "contribution_tier"]).size().reset_index(name="count").to_csv(
            stats / "contribution_yearly_tier.csv", index=False
        )
        # wide/strict yearly
        w = (
            df[df["in_wide_set"] == True]  # noqa: E712
            .groupby("year")
            .size()
            .reset_index(name="wide")
        )
        s = (
            df[df["in_strict_set"] == True]  # noqa: E712
            .groupby("year")
            .size()
            .reset_index(name="strict")
        )
        dual = w.merge(s, on="year", how="outer").fillna(0)
        dual.to_csv(stats / "contribution_wide_vs_strict_yearly.csv", index=False)

    # update curated canonical to strict for impact messaging? keep full graded; curated = wide
    with (curated / "curated.jsonl").open("w", encoding="utf-8") as f:
        for r in wide:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(json.dumps({
        "n": summary["n"],
        "by_tier": by_tier,
        "wide_n": len(wide),
        "strict_n": len(strict),
        "c4_or_milestone_n": len(c4),
        "yearly_strict": summary["yearly_strict"],
        "yearly_wide": summary["yearly_wide"],
    }, indent=2, ensure_ascii=False))
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="deepseek-v4-flash")
    p.add_argument("--workers", type=int, default=5)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    run_contribution(model=args.model, workers=args.workers, limit=args.limit, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
