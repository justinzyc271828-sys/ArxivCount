"""Verify arXiv abs/pdf links for timeline navigable papers."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .export_web import build_web_payload, normalize_arxiv_id
from .paths import ROOT


def _check(aid: str) -> dict[str, Any]:
    aid0 = normalize_arxiv_id(aid) or aid
    abs_url = f"https://arxiv.org/abs/{aid0}"
    pdf_url = f"https://arxiv.org/pdf/{aid0}.pdf"
    out = {"arxiv_id": aid0, "abs_url": abs_url, "pdf_url": pdf_url, "ok_abs": False, "ok_pdf": False}

    def head_or_get(url: str) -> tuple[bool, Any]:
        try:
            req = urllib.request.Request(
                url, method="HEAD", headers={"User-Agent": "ArxivCount-linkcheck/0.1"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                return 200 <= r.status < 400, r.status
        except Exception:
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "ArxivCount-linkcheck/0.1",
                        "Range": "bytes=0-200",
                    },
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    return r.status in {200, 206} or (200 <= r.status < 400), r.status
            except Exception as e:
                return False, str(e)

    out["ok_abs"], out["code_abs"] = head_or_get(abs_url)
    out["ok_pdf"], out["code_pdf"] = head_or_get(pdf_url)
    return out


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Verify timeline arXiv links").parse_args(argv)
    payload = build_web_payload()
    nav = payload.get("navigable") or []
    ids = sorted({e["arxiv_id"] for e in nav if e.get("arxiv_id")})
    print(f"Checking {len(ids)} unique arXiv ids from navigable events...")

    results = []
    bad = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_check, aid): aid for aid in ids}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            if not r["ok_abs"]:
                bad.append(r)
                print("FAIL abs", r["arxiv_id"], r.get("code_abs"))

    report = {
        "checked": len(results),
        "ok_abs": sum(1 for r in results if r["ok_abs"]),
        "ok_pdf": sum(1 for r in results if r["ok_pdf"]),
        "bad_abs": bad,
        "canon_links": [
            {"id": e.get("id"), "url": e.get("url")}
            for e in nav
            if e.get("type") == "canon_milestone"
        ],
    }
    out = ROOT / "data" / "stats" / "link_verify_report.json"
    # stats may be gitignored; also write under web
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        pass
    (ROOT / "web" / "timeline" / "data" / "link_verify_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "checked": report["checked"],
                "ok_abs": report["ok_abs"],
                "ok_pdf": report["ok_pdf"],
                "bad_abs_n": len(bad),
            },
            indent=2,
        )
    )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
