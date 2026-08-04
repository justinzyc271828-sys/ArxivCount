"""Retry failed fulltext downloads and re-merge into confirmed set."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .config import load_settings
from .fulltext import download_fulltext
from .fulltext_audit import (
    audit_fulltext,
    build_summary,
    export_stats,
    write_report,
    _load_jsonl,
    _append_jsonl,
)
from .llm_client import get_deepseek_client
from .paths import resolve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--ids", nargs="*", default=None, help="Specific arxiv ids")
    args = parser.parse_args(argv)

    settings = load_settings()
    curated = resolve(settings["paths"]["curated_dir"])
    downloads = resolve(settings["paths"]["downloads_dir"])
    stats = resolve(settings["paths"]["stats_dir"])
    docs = resolve("docs")

    demoted = _load_jsonl(curated / "fulltext_demoted.jsonl")
    confirmed = _load_jsonl(curated / "fulltext_confirmed.jsonl")
    # also load deep_confirmed originals for metadata
    deep = {r["arxiv_id"]: r for r in _load_jsonl(curated / "deep_confirmed.jsonl")}

    if args.ids:
        targets = args.ids
    else:
        targets = [
            d["arxiv_id"]
            for d in demoted
            if "unavailable" in str(d.get("ft_confirm_reason") or d.get("confirm_reason") or "")
            or d.get("ft_audit_mode") in {"fulltext_failed", "fulltext_short"}
        ]

    if not targets:
        print("No targets to repair")
        return 0

    print("Repair targets:", targets)
    client = get_deepseek_client()
    recovered: list[dict[str, Any]] = []
    still_bad: list[dict[str, Any]] = []

    for aid in targets:
        base = deep.get(aid) or next((d for d in demoted if d.get("arxiv_id") == aid), {"arxiv_id": aid})
        meta = download_fulltext(aid, downloads, delay=1.0, force=True)
        print(aid, "download", meta.get("ok"), meta.get("chars"), meta.get("error"))
        if not meta.get("ok"):
            row = {**base, "confirm_keep": False, "ft_confirm_keep": False,
                   "ft_confirm_reason": f"fulltext unavailable: {meta.get('error')}",
                   "ft_audit_mode": "fulltext_failed"}
            still_bad.append(row)
            continue
        text = Path(meta["txt_path"]).read_text(encoding="utf-8", errors="ignore")
        try:
            audit = audit_fulltext(client, base, text, model=args.model, max_chars=90000)
            audit["model"] = args.model
            audit["fulltext_chars"] = len(text)
            audit["fulltext_source"] = meta.get("source")
            _append_jsonl(curated / "fulltext_audit_cache.jsonl", audit)
        except Exception as e:  # noqa: BLE001
            print("audit failed", aid, e)
            still_bad.append({**base, "confirm_keep": False, "ft_confirm_reason": f"audit error: {e}"})
            continue

        row = {
            **base,
            "ft_confirm_keep": audit.get("confirm_keep"),
            "ft_confirm_reason": audit.get("confirm_reason"),
            "ft_primary_ai_role": audit.get("primary_ai_role"),
            "ft_ai_roles": audit.get("ai_roles"),
            "ft_ai_centrality": audit.get("ai_centrality"),
            "ft_human_ai_relation": audit.get("human_ai_relation"),
            "ft_result_type": audit.get("result_type"),
            "ft_proof_style": audit.get("proof_style"),
            "ft_math_subfields": audit.get("math_subfields"),
            "ft_open_problem": audit.get("open_problem"),
            "ft_open_problem_name": audit.get("open_problem_name"),
            "ft_formal_system": audit.get("formal_system"),
            "ft_models_mentioned": audit.get("models_mentioned"),
            "ft_trend_tags": audit.get("trend_tags"),
            "ft_ai_usage_evidence": audit.get("ai_usage_evidence"),
            "ft_ai_usage_locations": audit.get("ai_usage_locations"),
            "ft_writing_only": audit.get("writing_only"),
            "ft_confidence": audit.get("confidence"),
            "ft_one_line_summary": audit.get("one_line_summary"),
            "ft_changed_from_abstract": audit.get("changed_from_abstract"),
            "ft_change_note": audit.get("change_note"),
            "ft_audit_mode": audit.get("audit_mode"),
            "ft_model": audit.get("model"),
            "fulltext_chars": audit.get("fulltext_chars"),
            "fulltext_source": audit.get("fulltext_source"),
        }
        if audit.get("confirm_keep"):
            row["primary_ai_role"] = audit.get("primary_ai_role")
            row["ai_roles"] = audit.get("ai_roles")
            row["ai_centrality"] = audit.get("ai_centrality")
            row["human_ai_relation"] = audit.get("human_ai_relation")
            row["result_type"] = audit.get("result_type")
            row["proof_style"] = audit.get("proof_style")
            row["math_subfields"] = audit.get("math_subfields")
            row["open_problem"] = audit.get("open_problem")
            row["open_problem_name"] = audit.get("open_problem_name")
            row["formal_system"] = audit.get("formal_system")
            row["models_mentioned"] = audit.get("models_mentioned")
            row["trend_tags"] = audit.get("trend_tags")
            row["one_line_summary"] = audit.get("one_line_summary")
            row["confirm_keep"] = True
            row["confirm_reason"] = audit.get("confirm_reason")
            recovered.append(row)
            print("  RECOVERED keep", audit.get("primary_ai_role"), audit.get("one_line_summary"))
        else:
            row["confirm_keep"] = False
            still_bad.append(row)
            print("  audited but demoted:", audit.get("confirm_reason"))

    # merge: drop repaired ids from old confirmed/demoted, re-add
    repaired_ids = set(targets)
    confirmed = [r for r in confirmed if r.get("arxiv_id") not in repaired_ids] + recovered
    demoted_kept = [d for d in demoted if d.get("arxiv_id") not in repaired_ids] + still_bad

    with (curated / "fulltext_confirmed.jsonl").open("w", encoding="utf-8") as f:
        for r in confirmed:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (curated / "fulltext_demoted.jsonl").open("w", encoding="utf-8") as f:
        for r in demoted_kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (curated / "curated.jsonl").open("w", encoding="utf-8") as f:
        for r in confirmed:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # rebuild comparisons lightly
    comparisons = []
    for r in confirmed + demoted_kept:
        comparisons.append(
            {
                "arxiv_id": r.get("arxiv_id"),
                "title": r.get("title"),
                "abs_role": deep.get(r.get("arxiv_id"), {}).get("primary_ai_role"),
                "ft_role": r.get("primary_ai_role") or r.get("ft_primary_ai_role"),
                "abs_keep": True,
                "ft_keep": bool(r.get("confirm_keep")),
                "changed": r.get("ft_changed_from_abstract"),
                "change_note": r.get("ft_change_note"),
            }
        )

    summary = build_summary(
        confirmed,
        demoted_kept,
        comparisons,
        model=args.model,
        ok_dl=len(confirmed) + sum(1 for d in demoted_kept if (d.get("fulltext_chars") or 0) > 0),
        n=len(confirmed) + len(demoted_kept),
    )
    with (curated / "fulltext_audit_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    export_stats(confirmed, stats)
    write_report(summary, confirmed, demoted_kept, comparisons, docs / "fulltext_audit_report.md")

    print(json.dumps({
        "recovered": len(recovered),
        "still_bad": len(still_bad),
        "confirmed_total": len(confirmed),
        "demoted_total": len(demoted_kept),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
