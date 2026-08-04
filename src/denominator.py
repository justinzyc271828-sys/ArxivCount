"""Fetch arXiv math.* yearly totals and compute penetration rates."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import pandas as pd

from .config import load_settings
from .db import utc_now
from .paths import ensure_data_dirs, resolve

NS = {"opensearch": "http://a9.com/-/spec/opensearch/1.1/"}


def arxiv_total(query: str, *, timeout: int = 90) -> int:
    params = urllib.parse.urlencode(
        {"search_query": query, "start": 0, "max_results": 1}
    )
    url = "https://export.arxiv.org/api/query?" + params
    req = urllib.request.Request(
        url, headers={"User-Agent": "ArxivCount/0.1 (research; penetration)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    node = root.find("opensearch:totalResults", NS)
    if node is None or node.text is None:
        raise RuntimeError(f"No totalResults for query={query!r}")
    return int(node.text)


def fetch_math_yearly(
    years: list[int],
    *,
    delay: float = 3.0,
    category_query: str = "cat:math*",
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for y in years:
        # arXiv submittedDate format YYYYMMDDHHHH
        q = (
            f"{category_query} AND "
            f"submittedDate:[{y}01010000 TO {y}12312359]"
        )
        print(f"Query math total {y} ...", flush=True)
        total = arxiv_total(q)
        rows.append(
            {
                "year": y,
                "math_total": total,
                "category_query": category_query,
                "query": q,
                "fetched_at": utc_now(),
            }
        )
        print(f"  {y}: {total}", flush=True)
        time.sleep(delay)
    return rows


def load_wide_strict(stats_dir: Path, curated_dir: Path) -> pd.DataFrame:
    dual = stats_dir / "contribution_wide_vs_strict_yearly.csv"
    if dual.exists():
        df = pd.read_csv(dual)
        # ensure columns
        if "wide" not in df.columns:
            df["wide"] = 0
        if "strict" not in df.columns:
            df["strict"] = 0
        return df

    # fallback from summary json
    summary = curated_dir / "contribution_summary.json"
    if summary.exists():
        s = json.loads(summary.read_text(encoding="utf-8"))
        wide = s.get("yearly_wide") or {}
        strict = s.get("yearly_strict") or {}
        years = sorted(set(map(str, wide)) | set(map(str, strict)))
        return pd.DataFrame(
            {
                "year": [int(y) for y in years],
                "wide": [int(wide.get(y, wide.get(int(y), 0))) for y in years],
                "strict": [int(strict.get(y, strict.get(int(y), 0))) for y in years],
            }
        )
    return pd.DataFrame(columns=["year", "wide", "strict"])


def compute_penetration(
    math_rows: list[dict[str, Any]],
    wide_strict: pd.DataFrame,
) -> pd.DataFrame:
    m = pd.DataFrame(math_rows)
    ws = wide_strict.copy()
    ws["year"] = ws["year"].astype(int)
    m["year"] = m["year"].astype(int)
    df = m.merge(ws, on="year", how="left")
    df["wide"] = df["wide"].fillna(0).astype(int)
    df["strict"] = df["strict"].fillna(0).astype(int)
    df["wide_per_10k"] = (df["wide"] / df["math_total"] * 10000).round(4)
    df["strict_per_10k"] = (df["strict"] / df["math_total"] * 10000).round(4)
    df["wide_pct"] = (df["wide"] / df["math_total"] * 100).round(6)
    df["strict_pct"] = (df["strict"] / df["math_total"] * 100).round(6)
    # YoY growth of rates
    df = df.sort_values("year")
    df["wide_per_10k_yoy"] = df["wide_per_10k"].pct_change() * 100
    df["strict_per_10k_yoy"] = df["strict_per_10k"].pct_change() * 100
    return df


def run(
    *,
    start_year: int = 2015,
    end_year: int = 2026,
    delay: float = 3.0,
    skip_fetch: bool = False,
) -> Path:
    settings = load_settings()
    ensure_data_dirs(settings)
    stats = resolve(settings["paths"]["stats_dir"])
    curated = resolve(settings["paths"]["curated_dir"])
    raw = resolve(settings["paths"]["raw_dir"])

    years = list(range(start_year, end_year + 1))
    cache_path = raw / "math_yearly_totals.json"

    if skip_fetch and cache_path.exists():
        math_rows = json.loads(cache_path.read_text(encoding="utf-8"))
        print(f"Loaded cached math totals from {cache_path}")
    else:
        math_rows = fetch_math_yearly(years, delay=delay)
        cache_path.write_text(json.dumps(math_rows, indent=2), encoding="utf-8")

    ws = load_wide_strict(stats, curated)
    pen = compute_penetration(math_rows, ws)

    out_csv = stats / "penetration_yearly.csv"
    pen.to_csv(out_csv, index=False)

    summary = {
        "generated_at": utc_now(),
        "category_query": "cat:math*",
        "note": (
            "math_total = arXiv API opensearch:totalResults for cat:math* in calendar year. "
            "wide/strict from contribution grading of seed-collected AI-for-math proxy set. "
            "Rates are lower bounds on disclosed AI-related work, not true population penetration."
        ),
        "years": pen.to_dict(orient="records"),
        "latest": pen.iloc[-1].to_dict() if len(pen) else None,
    }
    out_json = stats / "penetration_summary.json"
    # convert numpy types
    def _clean(o: Any) -> Any:
        if isinstance(o, dict):
            return {k: _clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_clean(x) for x in o]
        if hasattr(o, "item"):
            try:
                return o.item()
            except Exception:
                return str(o)
        if pd.isna(o):
            return None
        return o

    out_json.write_text(
        json.dumps(_clean(summary), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(pen.to_string(index=False))
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_json}")
    return out_csv


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Math denominator + penetration rates")
    p.add_argument("--start-year", type=int, default=2015)
    p.add_argument("--end-year", type=int, default=2026)
    p.add_argument("--delay", type=float, default=3.0)
    p.add_argument("--skip-fetch", action="store_true", help="Use cached math totals")
    args = p.parse_args(argv)
    run(
        start_year=args.start_year,
        end_year=args.end_year,
        delay=args.delay,
        skip_fetch=args.skip_fetch,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
