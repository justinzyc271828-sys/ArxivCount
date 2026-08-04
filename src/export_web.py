"""Export static+interactive web timeline (GitHub Pages friendly)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from .config import load_settings
from .db import utc_now
from .paths import ROOT, resolve


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_web_payload() -> dict[str, Any]:
    settings = load_settings()
    stats = resolve(settings["paths"]["stats_dir"])
    curated = resolve(settings["paths"]["curated_dir"])

    timeline = _load(stats / "timeline.json") or {"events": [], "phases": [], "counts": {}}
    highlights = _load(stats / "timeline_highlights.json") or []
    contribution = _load(curated / "contribution_summary.json") or {}
    penetration = _load(stats / "penetration_summary.json") or {}

    # Ordered navigable milestones: canon first by date, then C4/highlight papers
    events = list(timeline.get("events") or [])
    navigable = []
    for e in events:
        if e.get("type") == "canon_milestone" or e.get("highlight") or e.get("contribution_tier") == "C4":
            navigable.append(e)
    # de-dup by id+date
    seen = set()
    uniq = []
    for e in navigable:
        key = (e.get("id"), e.get("date"), e.get("type"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    uniq.sort(key=lambda x: (x.get("date") or "9999", 0 if x.get("type") == "canon_milestone" else 1))

    return {
        "generated_at": utc_now(),
        "project": settings.get("project") or {},
        "phases": timeline.get("phases") or [],
        "events": events,
        "navigable": uniq,
        "highlights": highlights,
        "contribution": {
            "by_tier": contribution.get("by_tier"),
            "wide_n": contribution.get("wide_n"),
            "strict_n": contribution.get("strict_n"),
            "yearly_wide": contribution.get("yearly_wide"),
            "yearly_strict": contribution.get("yearly_strict"),
            "yearly_tier": contribution.get("yearly_tier"),
        },
        "penetration": penetration,
        "notes": {
            "wide": "C2+ ecosystem (assistive + material)",
            "strict": "C3+ material math impact claims",
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
    # also embed for file:// and simple hosting without CORS issues
    embed = "window.ARXIVCOUNT_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    (out_dir / "data.js").write_text(embed, encoding="utf-8")

    # copy template files if generators wrote them as package assets
    # templates live next to this exporter under web/timeline sources
    src_templates = ROOT / "web" / "timeline"
    # ensure index/css/js exist (written by this module's companion files)
    print(f"Web data exported -> {out_dir} ({len(payload.get('navigable') or [])} navigable events)")
    return out_dir


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)
    export_web(Path(args.out) if args.out else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
