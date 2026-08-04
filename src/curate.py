from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .config import load_settings
from .db import db_session, init_db
from .paths import ensure_data_dirs, resolve


def curate(
    settings: dict[str, Any] | None = None,
    *,
    min_level: str = "L1",
    drop_writing_only: bool = True,
) -> Path:
    """Stage-B: export a stricter curated subset from local classifications."""
    settings = settings or load_settings()
    ensure_data_dirs(settings)
    db_path = resolve(settings["paths"]["db_path"])
    init_db(db_path)

    order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
    min_rank = order.get(min_level, 1)

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

    curated: list[dict[str, Any]] = []
    for r in rows:
        level = r["level"]
        if order.get(level, -1) < min_rank:
            continue
        if drop_writing_only and int(r["writing_only"] or 0) == 1 and level == "L0":
            continue
        if drop_writing_only and int(r["writing_only"] or 0) == 1 and level == "L1":
            # keep L1 writing_only only if score still high
            if float(r["score"] or 0) < 6:
                continue

        item = {
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
            "score": r["score"],
            "level": r["level"],
            "matched_terms": json.loads(r["matched_terms_json"] or "[]"),
            "writing_only": bool(r["writing_only"]),
            "url": f"https://arxiv.org/abs/{r['arxiv_id']}",
        }
        curated.append(item)

    out_dir = resolve(settings["paths"]["curated_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "curated.jsonl"
    json_path = out_dir / "curated.json"
    summary_path = out_dir / "curated_summary.json"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for item in curated:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(curated, f, indent=2, ensure_ascii=False)

    by_level: dict[str, int] = {}
    for item in curated:
        by_level[item["level"]] = by_level.get(item["level"], 0) + 1

    summary = {
        "count": len(curated),
        "min_level": min_level,
        "drop_writing_only": drop_writing_only,
        "by_level": by_level,
    }
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Curated set -> {jsonl_path}")
    return jsonl_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage-B curation export")
    parser.add_argument("--min-level", default="L1", choices=["L0", "L1", "L2", "L3"])
    parser.add_argument(
        "--keep-writing-only",
        action="store_true",
        help="Do not drop writing-only demoted papers",
    )
    args = parser.parse_args(argv)
    curate(
        min_level=args.min_level,
        drop_writing_only=not args.keep_writing_only,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
