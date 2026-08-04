"""Build public timeline: canon milestones + graded papers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from .config import load_settings
from .db import utc_now
from .paths import ROOT, resolve


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_timeline() -> dict[str, Any]:
    settings = load_settings()
    curated = resolve(settings["paths"]["curated_dir"])
    stats = resolve(settings["paths"]["stats_dir"])
    docs = resolve("docs")

    with (ROOT / "config" / "milestones.yaml").open(encoding="utf-8") as f:
        mile_cfg = yaml.safe_load(f) or {}

    graded = _load_jsonl(curated / "contribution_graded.jsonl")
    if not graded:
        graded = _load_jsonl(curated / "fulltext_confirmed.jsonl")

    events: list[dict[str, Any]] = []

    # canon milestones
    for m in mile_cfg.get("milestones") or []:
        events.append(
            {
                "date": m.get("date"),
                "type": "canon_milestone",
                "kind": m.get("kind"),
                "phase": m.get("phase"),
                "id": m.get("id"),
                "label": m.get("label"),
                "note": m.get("note"),
                "arxiv_id": m.get("arxiv"),
                "url": (m.get("links") or [None])[0]
                if m.get("links")
                else (f"https://arxiv.org/abs/{m['arxiv']}" if m.get("arxiv") else None),
                "contribution_tier": m.get("contribution_hint"),
                "highlight": True,
            }
        )

    # paper events: C3/C4 + milestone candidates + open problems
    for r in graded:
        tier = r.get("contribution_tier") or ""
        if tier not in {"C3", "C4"} and not r.get("milestone_candidate"):
            # still include strong open-problem C2? skip for clean timeline
            if not (r.get("open_problem") and r.get("primary_ai_role") in {
                "proof_generation", "counterexample_search", "formalization"
            }):
                continue
            if tier not in {"C2", "C3", "C4"}:
                continue

        pub = (r.get("published") or "")[:10]
        if not pub:
            continue
        label = r.get("milestone_label") or r.get("title")
        if label and len(str(label)) > 90:
            label = str(label)[:87] + "..."
        events.append(
            {
                "date": pub,
                "type": "paper",
                "kind": "result" if tier in {"C3", "C4"} else "paper",
                "phase": None,
                "id": r.get("arxiv_id"),
                "label": label,
                "note": r.get("ai_role_summary") or r.get("tier_reason") or r.get("one_line_summary"),
                "arxiv_id": r.get("arxiv_id"),
                "url": r.get("url") or f"https://arxiv.org/abs/{r.get('arxiv_id')}",
                "contribution_tier": tier,
                "primary_ai_role": r.get("primary_ai_role"),
                "subfields": r.get("math_subfields"),
                "open_problem": bool(r.get("named_open_problem") or r.get("open_problem")),
                "open_problem_name": r.get("open_problem_name") or r.get("contrib_open_problem_name"),
                "milestone_candidate": bool(r.get("milestone_candidate")),
                "highlight": bool(r.get("milestone_candidate") or tier == "C4"),
            }
        )

    events.sort(key=lambda e: (e.get("date") or "9999", 0 if e.get("type") == "canon_milestone" else 1))

    # phases with counts
    phases = []
    for ph in mile_cfg.get("phases") or []:
        start, end = ph.get("start"), ph.get("end")
        papers = [
            e
            for e in events
            if e.get("type") == "paper"
            and e.get("date")
            and start <= e["date"] <= (end or "9999-12-31")
        ]
        strict_n = sum(1 for p in papers if p.get("contribution_tier") in {"C3", "C4"})
        phases.append(
            {
                **ph,
                "paper_events": len(papers),
                "strict_like": strict_n,
                "highlights": [p for p in papers if p.get("highlight")][:8],
            }
        )

    payload = {
        "generated_at": utc_now(),
        "phases": phases,
        "events": events,
        "counts": {
            "canon_milestones": sum(1 for e in events if e["type"] == "canon_milestone"),
            "paper_events": sum(1 for e in events if e["type"] == "paper"),
            "highlights": sum(1 for e in events if e.get("highlight")),
        },
    }

    out_json = stats / "timeline.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # markdown timeline for article/X
    lines = [
        "# AI × Mathematics Timeline (ArxivCount)",
        "",
        f"Generated: `{payload['generated_at']}`",
        "",
        "Canon milestones + graded papers (C3/C4 and milestone candidates).",
        "",
    ]
    for ph in phases:
        lines.append(f"## {ph.get('label')} ({ph.get('start')} → {ph.get('end')})")
        lines.append("")
        lines.append(
            f"Paper events in window: **{ph.get('paper_events')}** "
            f"(strict-like C3/C4: **{ph.get('strict_like')}**)"
        )
        lines.append("")
        # events in phase
        for e in events:
            d = e.get("date") or ""
            if not d or not (ph.get("start") <= d <= (ph.get("end") or "9999")):
                continue
            mark = "★" if e.get("highlight") else "•"
            if e["type"] == "canon_milestone":
                lines.append(f"- {mark} **{d}** · _canon_ · **{e.get('label')}**  ")
                lines.append(f"  {e.get('note')}")
            else:
                tier = e.get("contribution_tier") or "?"
                lines.append(
                    f"- {mark} **{d}** · `{tier}` · [{e.get('arxiv_id')}]({e.get('url')}) — {e.get('label')}  "
                )
                if e.get("open_problem_name"):
                    lines.append(f"  Open problem: {e.get('open_problem_name')}")
                if e.get("note"):
                    lines.append(f"  {e.get('note')}")
        lines.append("")

    md_path = docs / "timeline.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # top milestone shortlist for dashboard/X cards
    highlights = [e for e in events if e.get("highlight")]
    with (stats / "timeline_highlights.json").open("w", encoding="utf-8") as f:
        json.dump(highlights, f, indent=2, ensure_ascii=False)

    print(
        json.dumps(
            {
                "events": len(events),
                "highlights": len(highlights),
                "phases": len(phases),
                "md": str(md_path),
                "json": str(out_json),
            },
            indent=2,
        )
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Build timeline").parse_args(argv)
    build_timeline()
    return 0


if __name__ == "__main__":
    sys.exit(main())
