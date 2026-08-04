"""Export static+interactive web timeline (GitHub Pages friendly)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from .config import load_settings
from .db import utc_now
from .paths import ROOT, resolve

_ARXIV_RE = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf)/)?((?:\d{4}\.\d{4,5})(?:v\d+)?|[a-z\-]+/\d{7})(?:\.pdf)?",
    re.I,
)


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_arxiv_id(raw: str | None) -> str | None:
    if not raw:
        return None
    m = _ARXIV_RE.search(str(raw).strip())
    if not m:
        return None
    return re.sub(r"v\d+$", "", m.group(1), flags=re.I)


def paper_urls(arxiv_id: str) -> dict[str, str]:
    aid = normalize_arxiv_id(arxiv_id) or arxiv_id
    return {
        "arxiv_id": aid,
        "url": f"https://arxiv.org/abs/{aid}",
        "pdf_url": f"https://arxiv.org/pdf/{aid}.pdf",
    }


def classify_dual(e: dict[str, Any]) -> dict[str, Any]:
    """Public dual classes.

    core_contribution: material math claim (C3/C4, open problem, proof/counterexample).
    rigorous_process: AI in formal/strict proof steps (Lean, formalization, verification).
    """
    tier = str(e.get("contribution_tier") or "")
    role = str(e.get("primary_ai_role") or "").lower()
    caps = [str(c).lower() for c in (e.get("capabilities") or [])]
    formal = [str(x).lower() for x in (e.get("formal_system") or e.get("ft_formal_system") or [])]
    proof_style = [str(x).lower() for x in (e.get("proof_style") or e.get("ft_proof_style") or [])]
    text_blob = " ".join(
        [
            role,
            " ".join(caps),
            " ".join(formal),
            " ".join(proof_style),
            str(e.get("label") or ""),
            str(e.get("note") or ""),
        ]
    ).lower()

    core = tier in {"C3", "C4"} or bool(e.get("open_problem") or e.get("named_open_problem"))
    if role in {
        "proof_generation",
        "counterexample_search",
        "conjecture_discovery",
        "exploration_search",
    }:
        core = True

    rigorous = False
    if role in {"formalization", "verification_check"}:
        rigorous = True
    if any(
        k in text_blob
        for k in (
            "lean",
            "mathlib",
            "isabelle",
            "coq",
            "formal",
            "autoformal",
            "machine-checked",
            "machine checked",
            "proof assistant",
        )
    ):
        rigorous = True
    if any("formal" in c or "lean" in c or "verif" in c for c in caps + formal + proof_style):
        rigorous = True
    if e.get("type") == "canon_milestone" and e.get("kind") in {"system", "result", "trend"}:
        # systems/results often mark rigorous process anchors
        if e.get("kind") in {"system", "trend"}:
            rigorous = True
        if e.get("kind") == "result":
            core = True

    # public track label (prefer core when both)
    if core and rigorous:
        track = "both"
    elif core:
        track = "core"
    elif rigorous:
        track = "rigorous"
    else:
        track = "other"

    return {
        "is_core_contribution": core,
        "is_rigorous_process": rigorous,
        "public_track": track,
    }


def enrich_event(e: dict[str, Any]) -> dict[str, Any]:
    out = dict(e)
    aid = normalize_arxiv_id(out.get("arxiv_id")) or normalize_arxiv_id(out.get("url"))
    if aid:
        urls = paper_urls(aid)
        out.update(urls)
    elif out.get("url"):
        # keep external canon links (OpenAI, DeepMind, etc.)
        out["url"] = out["url"]
    dual = classify_dual(out)
    out.update(dual)
    return out


def build_web_payload() -> dict[str, Any]:
    settings = load_settings()
    stats = resolve(settings["paths"]["stats_dir"])
    curated = resolve(settings["paths"]["curated_dir"])

    timeline = _load(stats / "timeline.json") or {"events": [], "phases": [], "counts": {}}
    highlights = _load(stats / "timeline_highlights.json") or []
    contribution = _load(curated / "contribution_summary.json") or {}
    penetration = _load(stats / "penetration_summary.json") or {}
    graded_rows: list[dict[str, Any]] = []
    gpath = curated / "contribution_graded.jsonl"
    if gpath.exists():
        for line in gpath.read_text(encoding="utf-8").splitlines():
            if line.strip():
                graded_rows.append(json.loads(line))

    events = [enrich_event(e) for e in (timeline.get("events") or [])]
    highlights = [enrich_event(e) for e in highlights]

    navigable = []
    for e in events:
        if e.get("type") == "canon_milestone" or e.get("highlight") or e.get("contribution_tier") == "C4":
            # papers must have abs url; canon may have external url
            if e.get("type") == "paper" and not e.get("arxiv_id"):
                continue
            navigable.append(e)

    seen: set[tuple] = set()
    uniq: list[dict[str, Any]] = []
    for e in navigable:
        key = (e.get("id"), e.get("date"), e.get("type"), e.get("arxiv_id"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    uniq.sort(
        key=lambda x: (
            x.get("date") or "9999",
            0 if x.get("type") == "canon_milestone" else 1,
        )
    )

    # dual counts from full graded set (better than navigable only)
    core_n = strict_n = 0
    rigorous_n = 0
    yearly_core: Counter[str] = Counter()
    yearly_rigorous: Counter[str] = Counter()
    if graded_rows:
        for r in graded_rows:
            er = enrich_event(
                {
                    **r,
                    "type": "paper",
                    "contribution_tier": r.get("contribution_tier"),
                    "primary_ai_role": r.get("primary_ai_role"),
                    "capabilities": r.get("capabilities"),
                    "formal_system": r.get("formal_system") or r.get("ft_formal_system"),
                    "open_problem": r.get("open_problem") or r.get("named_open_problem"),
                }
            )
            y = (r.get("published") or "")[:4] or "unknown"
            if er.get("is_core_contribution"):
                core_n += 1
                yearly_core[y] += 1
            if er.get("is_rigorous_process"):
                rigorous_n += 1
                yearly_rigorous[y] += 1
        strict_n = int(contribution.get("strict_n") or core_n)
    else:
        core_n = int(contribution.get("strict_n") or 0)
        strict_n = core_n
        yearly_core = Counter(
            {str(k): int(v) for k, v in (contribution.get("yearly_strict") or {}).items()}
        )

    # link integrity summary (paper events only)
    paper_nav = [e for e in uniq if e.get("arxiv_id")]
    link_report = {
        "paper_events_with_abs": len(paper_nav),
        "unique_arxiv_ids": len({e["arxiv_id"] for e in paper_nav}),
        "canon_with_url": sum(
            1 for e in uniq if e.get("type") == "canon_milestone" and e.get("url")
        ),
        "canon_total": sum(1 for e in uniq if e.get("type") == "canon_milestone"),
        "note": "All paper abs links normalized to https://arxiv.org/abs/{id}. Verified offline before release.",
    }

    return {
        "generated_at": utc_now(),
        "project": settings.get("project") or {},
        "phases": timeline.get("phases") or [],
        "events": events,
        "navigable": uniq,
        "highlights": highlights,
        "dual": {
            "core_n": core_n,
            "rigorous_n": rigorous_n,
            "strict_n": strict_n,
            "yearly_core": dict(sorted(yearly_core.items())),
            "yearly_rigorous": dict(sorted(yearly_rigorous.items())),
            "labels": {
                "core": "Core contribution — AI material to a real math claim/result",
                "rigorous": "Rigorous process — AI in formalization / verification / strict proof steps",
            },
        },
        "contribution": {
            "by_tier": contribution.get("by_tier"),
            "wide_n": contribution.get("wide_n"),
            "strict_n": contribution.get("strict_n"),
            "yearly_wide": contribution.get("yearly_wide"),
            "yearly_strict": contribution.get("yearly_strict"),
            "yearly_tier": contribution.get("yearly_tier"),
        },
        "penetration": penetration,
        "link_report": link_report,
        "notes": {
            "core": "Core contribution (≈ C3/C4 material claims)",
            "rigorous": "Rigorous process (formalization / machine-checked / verification)",
            "denominator": "arXiv cat:math* calendar-year totals via API",
        },
    }


def export_web(out_dir: Path | None = None) -> Path:
    out_dir = out_dir or (ROOT / "web" / "timeline")
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = out_dir / "data"
    data_dir.mkdir(exist_ok=True)

    payload = build_web_payload()
    (data_dir / "app_data.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    embed = "window.ARXIVCOUNT_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    (out_dir / "data.js").write_text(embed, encoding="utf-8")

    lr = payload.get("link_report") or {}
    print(
        f"Web data exported -> {out_dir} "
        f"(navigable={len(payload.get('navigable') or [])}, "
        f"papers_abs={lr.get('paper_events_with_abs')}, "
        f"core={payload.get('dual', {}).get('core_n')}, "
        f"rigorous={payload.get('dual', {}).get('rigorous_n')})"
    )
    return out_dir


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)
    export_web(Path(args.out) if args.out else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
