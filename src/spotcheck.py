"""Build a human spot-check checklist from fulltext-confirmed papers."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from .config import load_settings
from .paths import resolve


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


def score_priority(row: dict[str, Any]) -> float:
    s = 0.0
    if row.get("open_problem") or row.get("ft_open_problem"):
        s += 5.0
    role = str(row.get("primary_ai_role") or "")
    if role in {"proof_generation", "counterexample_search", "formalization", "conjecture_discovery"}:
        s += 3.0
    if role == "exploration_search":
        s += 2.0
    cent = str(row.get("ai_centrality") or "")
    if cent == "core":
        s += 1.5
    if cent == "ai_led" or str(row.get("human_ai_relation")) == "ai_led":
        s += 2.0
    conf = float(row.get("ft_confidence") or row.get("audit_confidence") or 0.5)
    # lower confidence = more need for human check
    s += max(0.0, 1.0 - conf) * 2.0
    if row.get("ft_changed_from_abstract") or row.get("changed_from_abstract"):
        s += 1.5
    # prefer recent
    pub = str(row.get("published") or "")
    if pub.startswith("2026"):
        s += 1.0
    elif pub.startswith("2025"):
        s += 0.5
    return s


def build_spotcheck(
    *,
    limit: int = 40,
    open_problem_only: bool = False,
    name: str | None = None,
) -> dict[str, Any]:
    settings = load_settings()
    curated = resolve(settings["paths"]["curated_dir"])
    docs = resolve("docs")
    stats = resolve(settings["paths"]["stats_dir"])

    src = curated / "fulltext_confirmed.jsonl"
    if not src.exists():
        src = curated / "deep_confirmed.jsonl"
    rows = _load_jsonl(src)
    if open_problem_only:
        rows = [r for r in rows if r.get("open_problem") or r.get("ft_open_problem")]

    ranked = sorted(rows, key=score_priority, reverse=True)
    top = ranked[:limit]

    checklist = []
    for i, r in enumerate(top, 1):
        evidence = r.get("ft_ai_usage_evidence") or r.get("ai_usage_evidence") or []
        checklist.append(
            {
                "rank": i,
                "priority_score": round(score_priority(r), 2),
                "arxiv_id": r.get("arxiv_id"),
                "url": r.get("url") or f"https://arxiv.org/abs/{r.get('arxiv_id')}",
                "pdf": f"https://arxiv.org/pdf/{r.get('arxiv_id')}.pdf",
                "title": r.get("title"),
                "published": (r.get("published") or "")[:10],
                "primary_ai_role": r.get("primary_ai_role"),
                "ai_centrality": r.get("ai_centrality"),
                "human_ai_relation": r.get("human_ai_relation"),
                "result_type": r.get("result_type"),
                "math_subfields": r.get("math_subfields") or r.get("ft_math_subfields"),
                "open_problem": bool(r.get("open_problem") or r.get("ft_open_problem")),
                "open_problem_name": r.get("open_problem_name") or r.get("ft_open_problem_name"),
                "models_mentioned": r.get("models_mentioned") or r.get("ft_models_mentioned"),
                "formal_system": r.get("formal_system") or r.get("ft_formal_system"),
                "one_line_summary": r.get("one_line_summary") or r.get("ft_one_line_summary"),
                "ai_usage_evidence": evidence,
                "ft_confidence": r.get("ft_confidence") or r.get("audit_confidence"),
                # human fields to fill
                "human_verdict": "",  # confirm / demote / unsure
                "human_notes": "",
                "human_role_override": "",
            }
        )

    stem = name or ("spotcheck_open_problems" if open_problem_only else "spotcheck_queue")
    out_json = curated / f"{stem}.json"
    out_csv = stats / f"{stem}.csv"
    out_md = docs / f"{stem}.md"

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(checklist, f, indent=2, ensure_ascii=False)

    if checklist:
        fields = list(checklist[0].keys())
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for row in checklist:
                flat = dict(row)
                for k, v in list(flat.items()):
                    if isinstance(v, (list, dict)):
                        flat[k] = json.dumps(v, ensure_ascii=False)
                w.writerow(flat)

    lines = [
        "# Human Spot-Check Queue",
        "",
        f"Source: `{src.name}` · top **{len(checklist)}** by priority",
        "",
        "Priority favors: open problems, proof/counterexample/formalization, ai_led, low model confidence, abstract↔fulltext flips, recent years.",
        "",
        "Fill `human_verdict` with: `confirm` / `demote` / `unsure`.",
        "",
        "| # | arXiv | Role | Open problem | Subfields | Action |",
        "|---|-------|------|--------------|-----------|--------|",
    ]
    for c in checklist:
        subs = c.get("math_subfields") or []
        if isinstance(subs, list):
            subs_s = ", ".join(str(x) for x in subs[:3])
        else:
            subs_s = str(subs)
        op = c.get("open_problem_name") or ("yes" if c.get("open_problem") else "")
        lines.append(
            f"| {c['rank']} | [{c['arxiv_id']}]({c['url']}) | `{c.get('primary_ai_role')}` | {op} | {subs_s} |  |"
        )
        lines.append("")
        lines.append(f"**{c['title']}**")
        lines.append("")
        lines.append(f"- Summary: {c.get('one_line_summary')}")
        lines.append(f"- Relation: `{c.get('human_ai_relation')}` · centrality: `{c.get('ai_centrality')}` · conf: {c.get('ft_confidence')}")
        if c.get("ai_usage_evidence"):
            lines.append(f"- Evidence: {c.get('ai_usage_evidence')}")
        lines.append(f"- PDF: {c.get('pdf')}")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(checklist)} items -> {out_md}")
    print(f"CSV -> {out_csv}")
    return {"count": len(checklist), "md": str(out_md), "csv": str(out_csv)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build human spot-check queue")
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--open-problem-only", action="store_true")
    p.add_argument("--name", default=None, help="output stem name")
    args = p.parse_args(argv)
    build_spotcheck(
        limit=args.limit,
        open_problem_only=args.open_problem_only,
        name=args.name,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
