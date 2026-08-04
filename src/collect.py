from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import arxiv
from tqdm import tqdm

from .classify import KeywordClassifier
from .config import load_loose_keywords, load_settings, load_strict_keywords
from .db import (
    db_session,
    init_db,
    paper_to_row,
    upsert_classification,
    upsert_paper,
    utc_now,
)
from .paths import ensure_data_dirs, resolve

# arXiv IDs like 2301.12345 or 2301.12345v2 or math/0212345
_ID_RE = re.compile(
    r"(?:arXiv:)?((?:\d{4}\.\d{4,5})(?:v\d+)?|(?:[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?)",
    re.IGNORECASE,
)


def normalize_arxiv_id(raw: str) -> str:
    raw = (raw or "").strip()
    m = _ID_RE.search(raw)
    if not m:
        return raw.replace("arXiv:", "").strip()
    aid = m.group(1)
    # store without version for stable PK; keep latest metadata on upsert
    aid = re.sub(r"v\d+$", "", aid)
    return aid


def result_to_paper(r: arxiv.Result) -> dict[str, Any]:
    cats = list(r.categories or [])
    authors = [a.name for a in (r.authors or [])]
    arxiv_id = normalize_arxiv_id(r.get_short_id())
    return {
        "arxiv_id": arxiv_id,
        "title": (r.title or "").replace("\n", " ").strip(),
        "abstract": (r.summary or "").replace("\n", " ").strip(),
        "authors": authors,
        "categories": " ".join(cats),
        "primary_category": r.primary_category,
        "published": r.published.isoformat() if r.published else None,
        "updated": r.updated.isoformat() if r.updated else None,
        "comment": r.comment,
        "journal_ref": r.journal_ref,
        "doi": r.doi,
        "pdf_url": r.pdf_url,
        "collected_at": utc_now(),
    }


def build_category_clause(categories: list[str]) -> str:
    """Build arXiv API category clause. math.* is expanded to cat:math* style."""
    parts: list[str] = []
    for c in categories:
        c = c.strip()
        if not c:
            continue
        if c.endswith(".*"):
            # arXiv supports cat:math.* in some clients; use prefix form
            prefix = c[:-2]
            parts.append(f"cat:{prefix}*")
        elif c.endswith("*"):
            parts.append(f"cat:{c}")
        else:
            parts.append(f"cat:{c}")
    if not parts:
        return "cat:math*"
    if len(parts) == 1:
        return parts[0]
    return "(" + " OR ".join(parts) + ")"


def iter_search(
    query: str,
    *,
    max_results: int,
    page_size: int,
    delay: float,
    sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
    sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending,
) -> Iterable[arxiv.Result]:
    client = arxiv.Client(
        page_size=page_size,
        delay_seconds=delay,
        num_retries=3,
    )
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    yield from client.results(search)


def collect_seed_queries(
    settings: dict[str, Any],
    *,
    dry_run: bool = False,
    max_per_query: int | None = None,
) -> dict[str, int]:
    ensure_data_dirs(settings)
    db_path = resolve(settings["paths"]["db_path"])
    init_db(db_path)

    arxiv_cfg = settings["arxiv"]
    collect_cfg = settings["collect"]
    categories = arxiv_cfg.get("categories") or ["math.*"]
    cat_clause = build_category_clause(categories)
    page_size = int(arxiv_cfg.get("page_size") or 100)
    delay = float(arxiv_cfg.get("request_delay_seconds") or 3.0)
    default_max = int(arxiv_cfg.get("max_results_per_query") or 30000)
    max_results = max_per_query if max_per_query is not None else default_max

    loose = load_loose_keywords(settings)
    strict = load_strict_keywords(settings)
    thresholds = (settings.get("classify") or {}).get("levels")
    classifier = KeywordClassifier(loose, strict, thresholds)

    seed_queries: list[str] = list(collect_cfg.get("seed_queries") or [])
    stats = {"fetched": 0, "upserted": 0, "candidates": 0, "queries": len(seed_queries)}

    if dry_run:
        for q in seed_queries:
            full = f"({cat_clause}) AND ({q})"
            print(f"[dry-run] {full}")
        return stats

    start_date = arxiv_cfg.get("start_date") or "2015-01-01"

    with db_session(db_path) as conn:
        for q in seed_queries:
            full_query = f"({cat_clause}) AND ({q})"
            print(f"\n==> Query: {full_query}")
            run_started = utc_now()
            fetched = 0
            upserted = 0
            cand = 0

            cur = conn.execute(
                "INSERT INTO collect_runs (started_at, query, fetched, upserted, notes) VALUES (?, ?, 0, 0, ?)",
                (run_started, full_query, "seed"),
            )
            run_id = cur.lastrowid

            try:
                for result in tqdm(
                    iter_search(
                        full_query,
                        max_results=max_results,
                        page_size=page_size,
                        delay=delay,
                    ),
                    desc="fetch",
                    unit="paper",
                ):
                    paper = result_to_paper(result)
                    # date filter (client-side safety net)
                    pub = paper.get("published") or ""
                    if start_date and pub and pub[:10] < start_date:
                        # results are newest-first; can stop this query early
                        break

                    fetched += 1
                    upsert_paper(conn, paper_to_row(paper))
                    upserted += 1

                    m = classifier.classify_text(paper["title"], paper["abstract"])
                    if m.level != "none":
                        cand += 1
                        upsert_classification(
                            conn,
                            {
                                "arxiv_id": paper["arxiv_id"],
                                "stage": "loose",
                                "score": m.score,
                                "level": m.level,
                                "matched_terms_json": json.dumps(
                                    m.matched_terms, ensure_ascii=False
                                ),
                                "writing_only": 1 if m.writing_only else 0,
                                "classified_at": utc_now(),
                            },
                        )

                    if fetched % 50 == 0:
                        conn.commit()

            except Exception as e:
                conn.execute(
                    "UPDATE collect_runs SET finished_at=?, fetched=?, upserted=?, notes=? WHERE id=?",
                    (utc_now(), fetched, upserted, f"error: {e}", run_id),
                )
                conn.commit()
                raise

            conn.execute(
                "UPDATE collect_runs SET finished_at=?, fetched=?, upserted=?, notes=? WHERE id=?",
                (utc_now(), fetched, upserted, f"candidates={cand}", run_id),
            )
            conn.commit()
            stats["fetched"] += fetched
            stats["upserted"] += upserted
            stats["candidates"] += cand
            print(f"    fetched={fetched} upserted={upserted} candidates={cand}")

    # also dump a jsonl snapshot of candidates
    export_candidates_jsonl(settings)
    return stats


def export_candidates_jsonl(settings: dict[str, Any]) -> Path:
    db_path = resolve(settings["paths"]["db_path"])
    out_dir = resolve(settings["paths"]["candidates_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "candidates.jsonl"

    with db_session(db_path) as conn:
        rows = conn.execute(
            """
            SELECT p.*, c.score, c.level, c.matched_terms_json, c.writing_only
            FROM classifications c
            JOIN papers p ON p.arxiv_id = c.arxiv_id
            ORDER BY p.published DESC
            """
        ).fetchall()

    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            item = dict(r)
            # authors as list
            try:
                item["authors"] = json.loads(item.pop("authors_json") or "[]")
            except json.JSONDecodeError:
                item["authors"] = []
            try:
                item["matched_terms"] = json.loads(item.pop("matched_terms_json") or "[]")
            except json.JSONDecodeError:
                item["matched_terms"] = []
            item.pop("entry_json", None)
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} candidates -> {out_path}")
    return out_path


def reclassify_local(settings: dict[str, Any]) -> int:
    """Re-run classifier on all papers already in SQLite."""
    ensure_data_dirs(settings)
    db_path = resolve(settings["paths"]["db_path"])
    init_db(db_path)
    loose = load_loose_keywords(settings)
    strict = load_strict_keywords(settings)
    thresholds = (settings.get("classify") or {}).get("levels")
    classifier = KeywordClassifier(loose, strict, thresholds)

    n = 0
    with db_session(db_path) as conn:
        rows = conn.execute("SELECT arxiv_id, title, abstract FROM papers").fetchall()
        for r in tqdm(rows, desc="reclassify"):
            m = classifier.classify_text(r["title"], r["abstract"])
            if m.level == "none":
                conn.execute(
                    "DELETE FROM classifications WHERE arxiv_id=?", (r["arxiv_id"],)
                )
                continue
            upsert_classification(
                conn,
                {
                    "arxiv_id": r["arxiv_id"],
                    "stage": "loose",
                    "score": m.score,
                    "level": m.level,
                    "matched_terms_json": json.dumps(m.matched_terms, ensure_ascii=False),
                    "writing_only": 1 if m.writing_only else 0,
                    "classified_at": utc_now(),
                },
            )
            n += 1
            if n % 100 == 0:
                conn.commit()
    export_candidates_jsonl(settings)
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect arXiv math papers (loose AI keywords)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print queries only",
    )
    parser.add_argument(
        "--max-per-query",
        type=int,
        default=None,
        help="Cap results per seed query (useful for smoke tests)",
    )
    parser.add_argument(
        "--reclassify-only",
        action="store_true",
        help="Only re-run classifier on local DB",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    if args.reclassify_only:
        n = reclassify_local(settings)
        print(f"Reclassified candidates: {n}")
        return 0

    stats = collect_seed_queries(
        settings,
        dry_run=args.dry_run,
        max_per_query=args.max_per_query,
    )
    print("Done:", stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
