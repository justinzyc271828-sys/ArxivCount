"""Stage-B/C curation: rule hard-filter + optional DeepSeek V4 Flash review."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .config import load_settings
from .db import db_session, init_db, utc_now
from .llm_client import chat_json, get_deepseek_client
from .paths import ensure_data_dirs, resolve

SYSTEM_PROMPT = """You are a careful research librarian labeling arXiv math papers.

Goal: decide whether a paper is relevant to the TREND of AI-assisted mathematical
proof / discovery / formalization (LLMs, neural theorem provers, AI+Lean, etc.).

Return ONLY a JSON object with these fields:
{
  "keep": boolean,                 // true if relevant to AI-for-math trend (not mere writing help)
  "category": string,              // one of the categories below
  "refined_level": string,         // L3 | L2 | L1 | L0 | drop
  "confidence": number,            // 0.0-1.0
  "reason": string                 // <= 30 English words
}

Categories:
- ai_proof_generation: AI/LLM produced or co-produced a proof, lemma, or counterexample of math interest
- ai_formalization: AI used with Lean/Isabelle/Coq/etc. to formalize or search formal proofs
- ai_discovery_assist: AI meaningfully used in math exploration/conjecture search (not just prose)
- ai_method_survey: paper ABOUT methods/systems/benchmarks for AI mathematical reasoning
- writing_only: AI only for writing/editing/translation of an otherwise ordinary math paper
- classical_formal_only: proof assistants / computer algebra WITHOUT AI/LLM involvement
- false_positive: keyword accident; not about AI-for-math
- unrelated: other

Level guide (only if keep=true; else refined_level=drop):
- L3: open problem / major conjecture / notable new math result with clear AI role
- L2: substantial AI+formal or serious AI-assisted proving
- L1: clear AI-for-math relevance (including solid method/system papers)
- L0: weak/borderline AI mention still worth soft tracking

Be strict on writing_only and classical_formal_only. Lean-only human formalization without AI -> classical_formal_only.
Mention of ChatGPT only in acknowledgements for English polishing -> writing_only / keep=false.
"""

# Keywords that suggest real AI involvement (for rule stage)
_AI_RE = re.compile(
    r"\b("
    r"llm|llms|chatgpt|gpt-?\d|claude|gemini|grok|deepseek|"
    r"large language model|language model|foundation model|"
    r"alphaproof|alphageometry|funsearch|minerva|"
    r"autoformalization|auto-formalization|neural theorem|"
    r"ai[- ]assisted|ai[- ]generated|ai[- ]aided|machine[- ]generated proof|"
    r"reinforcement learning"
    r")\b",
    re.I,
)

_FORMAL_RE = re.compile(
    r"\b(lean\s*4|lean4|mathlib|isabelle|coq|hol light|proof assistant|formal verification|formal proof)\b",
    re.I,
)

_WRITING_RE = re.compile(
    r"(writing assistance|helped (with )?writ|proofread|language edit|polishing the manuscript|"
    r"improved the (english|writing)|grammar check|for helpful comments on (the )?writing)",
    re.I,
)


def load_candidates(settings: dict[str, Any]) -> list[dict[str, Any]]:
    db_path = resolve(settings["paths"]["db_path"])
    init_db(db_path)
    with db_session(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                p.arxiv_id, p.title, p.abstract, p.authors_json, p.categories,
                p.primary_category, p.published, p.updated, p.pdf_url, p.doi,
                c.score, c.level, c.matched_terms_json, c.writing_only
            FROM classifications c
            JOIN papers p ON p.arxiv_id = c.arxiv_id
            ORDER BY c.score DESC, p.published DESC
            """
        ).fetchall()

    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "arxiv_id": r["arxiv_id"],
                "title": r["title"],
                "abstract": r["abstract"],
                "authors": json.loads(r["authors_json"] or "[]"),
                "categories": r["categories"],
                "primary_category": r["primary_category"],
                "published": r["published"],
                "updated": r["updated"],
                "pdf_url": r["pdf_url"],
                "doi": r["doi"],
                "score": float(r["score"] or 0),
                "level": r["level"],
                "matched_terms": json.loads(r["matched_terms_json"] or "[]"),
                "writing_only": bool(r["writing_only"]),
                "url": f"https://arxiv.org/abs/{r['arxiv_id']}",
            }
        )
    return out


def rule_screen(item: dict[str, Any]) -> dict[str, Any]:
    """Deterministic pre-filter. Does not call the LLM."""
    text = f"{item.get('title','')}\n{item.get('abstract','')}"
    has_ai = bool(_AI_RE.search(text))
    has_formal = bool(_FORMAL_RE.search(text))
    writingish = bool(_WRITING_RE.search(text)) or bool(item.get("writing_only"))

    # also look at matched terms for AI tokens
    terms = " ".join(item.get("matched_terms") or [])
    if not has_ai and _AI_RE.search(terms):
        has_ai = True

    decision = {
        "rule_keep": True,
        "rule_category": "unknown",
        "rule_reason": "",
        "needs_llm": True,
    }

    if writingish and not has_formal and item.get("score", 0) < 8:
        # still send borderline to LLM if AI words exist
        if has_ai and item.get("score", 0) >= 4:
            decision.update(
                rule_keep=True,
                rule_category="maybe_writing",
                rule_reason="writing hints present; LLM will decide",
                needs_llm=True,
            )
        else:
            decision.update(
                rule_keep=False,
                rule_category="writing_only",
                rule_reason="writing-assistance language without strong proof/AI signal",
                needs_llm=False,
            )
        return decision

    if has_formal and not has_ai:
        decision.update(
            rule_keep=False,
            rule_category="classical_formal_only",
            rule_reason="formal methods without AI/LLM signal in title/abstract",
            needs_llm=False,
        )
        return decision

    if not has_ai and not has_formal:
        decision.update(
            rule_keep=False,
            rule_category="false_positive",
            rule_reason="no AI or formal signal after re-check",
            needs_llm=False,
        )
        return decision

    if has_ai and has_formal:
        decision.update(
            rule_keep=True,
            rule_category="ai_formal_candidate",
            rule_reason="AI + formal keywords",
            needs_llm=True,
        )
        return decision

    if has_ai:
        decision.update(
            rule_keep=True,
            rule_category="ai_candidate",
            rule_reason="AI/LLM keywords present",
            needs_llm=True,
        )
        return decision

    decision.update(
        rule_keep=True,
        rule_category="unknown",
        rule_reason="fallback to LLM",
        needs_llm=True,
    )
    return decision


def _build_user_prompt(item: dict[str, Any]) -> str:
    abstract = (item.get("abstract") or "")[:1800]
    terms = ", ".join((item.get("matched_terms") or [])[:12])
    return (
        f"arxiv_id: {item['arxiv_id']}\n"
        f"title: {item.get('title','')}\n"
        f"primary_category: {item.get('primary_category','')}\n"
        f"keyword_level: {item.get('level')} score={item.get('score')}\n"
        f"matched_terms: {terms}\n"
        f"abstract:\n{abstract}\n"
    )


def llm_label(client: Any, item: dict[str, Any], model: str) -> dict[str, Any]:
    data = chat_json(
        client,
        system=SYSTEM_PROMPT,
        user=_build_user_prompt(item),
        model=model,
        temperature=0.05,
        max_tokens=400,
    )
    keep = bool(data.get("keep"))
    category = str(data.get("category") or "unrelated")
    level = str(data.get("refined_level") or ("L1" if keep else "drop"))
    if not keep:
        level = "drop"
    if level not in {"L0", "L1", "L2", "L3", "drop"}:
        level = "L1" if keep else "drop"
    try:
        conf = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    conf = max(0.0, min(1.0, conf))
    reason = str(data.get("reason") or "")[:240]
    return {
        "keep": keep,
        "category": category,
        "refined_level": level,
        "confidence": conf,
        "reason": reason,
        "llm_raw": data,
    }


def _load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    cache: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            aid = obj.get("arxiv_id")
            if aid:
                cache[aid] = obj
    return cache


def _append_cache(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def refine(
    settings: dict[str, Any] | None = None,
    *,
    use_llm: bool = True,
    model: str = "deepseek-v4-flash",
    workers: int = 6,
    limit: int | None = None,
    min_keyword_level: str = "L0",
    force: bool = False,
) -> dict[str, Any]:
    settings = settings or load_settings()
    ensure_data_dirs(settings)
    out_dir = resolve(settings["paths"]["curated_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    cache_path = out_dir / "llm_labels_cache.jsonl"
    refined_path = out_dir / "refined.jsonl"
    refined_json = out_dir / "refined.json"
    dropped_path = out_dir / "dropped.jsonl"
    summary_path = out_dir / "refined_summary.json"

    items = load_candidates(settings)
    order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
    min_rank = order.get(min_keyword_level, 0)
    items = [x for x in items if order.get(x.get("level", "L0"), 0) >= min_rank]
    if limit is not None:
        items = items[:limit]

    # Stage 1: rules
    for it in items:
        it.update(rule_screen(it))

    rule_drop = [x for x in items if not x["rule_keep"] and not x["needs_llm"]]
    llm_pool = [x for x in items if x["needs_llm"]]
    rule_keep_no_llm = [x for x in items if x["rule_keep"] and not x["needs_llm"]]

    print(
        f"Candidates={len(items)} | rule_hard_drop={len(rule_drop)} | "
        f"llm_pool={len(llm_pool)} | rule_keep_no_llm={len(rule_keep_no_llm)}"
    )

    cache = {} if force else _load_cache(cache_path)
    if force and cache_path.exists():
        cache_path.unlink()
        cache = {}

    labels: dict[str, dict[str, Any]] = {}

    # Apply rule-only decisions
    for it in rule_drop:
        labels[it["arxiv_id"]] = {
            "arxiv_id": it["arxiv_id"],
            "keep": False,
            "category": it["rule_category"],
            "refined_level": "drop",
            "confidence": 0.9,
            "reason": it["rule_reason"],
            "source": "rule",
            "labeled_at": utc_now(),
        }
    for it in rule_keep_no_llm:
        labels[it["arxiv_id"]] = {
            "arxiv_id": it["arxiv_id"],
            "keep": True,
            "category": it["rule_category"],
            "refined_level": it.get("level") or "L1",
            "confidence": 0.7,
            "reason": it["rule_reason"],
            "source": "rule",
            "labeled_at": utc_now(),
        }

    # Stage 2: LLM
    if use_llm and llm_pool:
        client = get_deepseek_client()
        todo = []
        for it in llm_pool:
            aid = it["arxiv_id"]
            if aid in cache and cache[aid].get("source") == "llm":
                labels[aid] = cache[aid]
            else:
                todo.append(it)

        print(f"LLM to label: {len(todo)} (cached {len(llm_pool) - len(todo)})")

        def work(it: dict[str, Any]) -> dict[str, Any]:
            lab = llm_label(client, it, model=model)
            row = {
                "arxiv_id": it["arxiv_id"],
                **lab,
                "source": "llm",
                "model": model,
                "labeled_at": utc_now(),
            }
            # strip bulky raw for cache readability optional keep
            return row

        errors = 0
        with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            futs = {ex.submit(work, it): it for it in todo}
            for fut in tqdm(as_completed(futs), total=len(futs), desc="deepseek"):
                it = futs[fut]
                try:
                    row = fut.result()
                    labels[it["arxiv_id"]] = row
                    _append_cache(cache_path, row)
                except Exception as e:  # noqa: BLE001
                    errors += 1
                    # fail-open conservatively: keep keyword level if score high
                    fallback_keep = float(it.get("score") or 0) >= 7
                    row = {
                        "arxiv_id": it["arxiv_id"],
                        "keep": fallback_keep,
                        "category": "llm_error",
                        "refined_level": (it.get("level") or "L1") if fallback_keep else "drop",
                        "confidence": 0.2,
                        "reason": f"llm error: {type(e).__name__}",
                        "source": "llm_error",
                        "labeled_at": utc_now(),
                    }
                    labels[it["arxiv_id"]] = row
                    _append_cache(cache_path, row)
        print(f"LLM errors: {errors}")

    elif not use_llm:
        # without LLM, promote rule-kept needs_llm using keyword level
        for it in llm_pool:
            labels[it["arxiv_id"]] = {
                "arxiv_id": it["arxiv_id"],
                "keep": True,
                "category": it["rule_category"],
                "refined_level": it.get("level") or "L1",
                "confidence": 0.5,
                "reason": "rules-only mode",
                "source": "rule",
                "labeled_at": utc_now(),
            }

    # Merge + export
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for it in items:
        lab = labels.get(it["arxiv_id"]) or {
            "keep": False,
            "category": "missing",
            "refined_level": "drop",
            "confidence": 0.0,
            "reason": "no label",
            "source": "missing",
        }
        merged = {
            **{k: it[k] for k in it if not k.startswith("rule_") and k != "needs_llm"},
            "keyword_level": it.get("level"),
            "keyword_score": it.get("score"),
            "keep": lab.get("keep"),
            "category": lab.get("category"),
            "refined_level": lab.get("refined_level"),
            "confidence": lab.get("confidence"),
            "refine_reason": lab.get("reason"),
            "refine_source": lab.get("source"),
            "refine_model": lab.get("model"),
        }
        # final level field for downstream charts
        if merged["keep"] and merged["refined_level"] != "drop":
            merged["level"] = merged["refined_level"]
            kept.append(merged)
        else:
            merged["level"] = "drop"
            dropped.append(merged)

    # sort kept by level then score
    level_rank = {"L3": 3, "L2": 2, "L1": 1, "L0": 0}
    kept.sort(
        key=lambda x: (
            -level_rank.get(x.get("level") or "L0", 0),
            -float(x.get("keyword_score") or 0),
            x.get("published") or "",
        )
    )

    with refined_path.open("w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with refined_json.open("w", encoding="utf-8") as f:
        json.dump(kept, f, indent=2, ensure_ascii=False)
    with dropped_path.open("w", encoding="utf-8") as f:
        for row in dropped:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_level = dict(Counter(x.get("level") for x in kept))
    by_cat = dict(Counter(x.get("category") for x in kept))
    drop_cat = dict(Counter(x.get("category") for x in dropped))
    summary = {
        "input_candidates": len(items),
        "kept": len(kept),
        "dropped": len(dropped),
        "by_refined_level": by_level,
        "by_category_kept": by_cat,
        "by_category_dropped": drop_cat,
        "use_llm": use_llm,
        "model": model if use_llm else None,
        "generated_at": utc_now(),
    }
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # also refresh curated.jsonl as the refined keep-set (main product)
    curated_path = out_dir / "curated.jsonl"
    curated_json = out_dir / "curated.json"
    curated_summary = out_dir / "curated_summary.json"
    with curated_path.open("w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with curated_json.open("w", encoding="utf-8") as f:
        json.dump(kept, f, indent=2, ensure_ascii=False)
    with curated_summary.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "count": len(kept),
                "source": "refine+llm" if use_llm else "refine-rules",
                "by_level": by_level,
                "by_category": by_cat,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Refined keep -> {refined_path}")
    print(f"Dropped     -> {dropped_path}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rule + DeepSeek refine for candidates")
    parser.add_argument("--no-llm", action="store_true", help="Rules only")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=None, help="Only first N candidates")
    parser.add_argument("--min-keyword-level", default="L0", choices=["L0", "L1", "L2", "L3"])
    parser.add_argument("--force", action="store_true", help="Ignore LLM cache")
    args = parser.parse_args(argv)

    refine(
        use_llm=not args.no_llm,
        model=args.model,
        workers=args.workers,
        limit=args.limit,
        min_keyword_level=args.min_keyword_level,
        force=args.force,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
