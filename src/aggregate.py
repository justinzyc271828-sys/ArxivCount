from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from .config import load_milestones, load_settings
from .db import db_session, init_db
from .paths import ensure_data_dirs, resolve


def load_joined_frame(
    settings: dict[str, Any],
    *,
    prefer_refined: bool = True,
) -> pd.DataFrame:
    """Load analysis frame.

    If prefer_refined and data/curated/refined.jsonl exists, use the LLM/rule
    refined keep-set. Otherwise fall back to keyword classifications in SQLite.
    """
    refined_path = resolve(settings["paths"]["curated_dir"]) / "refined.jsonl"
    if prefer_refined and refined_path.exists():
        records: list[dict[str, Any]] = []
        with refined_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if not obj.get("keep", True):
                    continue
                records.append(
                    {
                        "arxiv_id": obj.get("arxiv_id"),
                        "title": obj.get("title"),
                        "abstract": obj.get("abstract"),
                        "authors_json": json.dumps(obj.get("authors") or [], ensure_ascii=False),
                        "categories": obj.get("categories"),
                        "primary_category": obj.get("primary_category"),
                        "published": obj.get("published"),
                        "updated": obj.get("updated"),
                        "pdf_url": obj.get("pdf_url"),
                        "score": obj.get("keyword_score", obj.get("score", 0)),
                        "level": obj.get("level") or obj.get("refined_level") or "L1",
                        "matched_terms_json": json.dumps(
                            obj.get("matched_terms") or [], ensure_ascii=False
                        ),
                        "writing_only": 0,
                        "category": obj.get("category"),
                        "confidence": obj.get("confidence"),
                    }
                )
        if records:
            df = pd.DataFrame(records)
            return _enrich_dates(df)

    db_path = resolve(settings["paths"]["db_path"])
    init_db(db_path)
    with db_session(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                p.arxiv_id,
                p.title,
                p.abstract,
                p.authors_json,
                p.categories,
                p.primary_category,
                p.published,
                p.updated,
                p.pdf_url,
                c.score,
                c.level,
                c.matched_terms_json,
                c.writing_only
            FROM classifications c
            JOIN papers p ON p.arxiv_id = c.arxiv_id
            """
        ).fetchall()

    if not rows:
        return pd.DataFrame(
            columns=[
                "arxiv_id",
                "title",
                "published",
                "year",
                "year_month",
                "primary_category",
                "score",
                "level",
                "writing_only",
            ]
        )

    records = [dict(r) for r in rows]
    df = pd.DataFrame(records)
    return _enrich_dates(df)


def _enrich_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["published_dt"] = pd.to_datetime(df["published"], utc=True, errors="coerce")
    df["year"] = df["published_dt"].dt.year
    # drop timezone before Period conversion (pandas warning otherwise)
    pub_naive = df["published_dt"].dt.tz_localize(None)
    df["year_month"] = pub_naive.dt.to_period("M").astype(str)
    if "writing_only" in df.columns:
        df["writing_only"] = df["writing_only"].fillna(0).astype(int)
    else:
        df["writing_only"] = 0
    return df


def monthly_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["year_month", "count", "L0", "L1", "L2", "L3"])

    base = (
        df.groupby("year_month", dropna=True)
        .size()
        .rename("count")
        .reset_index()
        .sort_values("year_month")
    )
    level_pivot = (
        df.pivot_table(
            index="year_month",
            columns="level",
            values="arxiv_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )
    out = base.merge(level_pivot, on="year_month", how="left")
    for col in ("L0", "L1", "L2", "L3"):
        if col not in out.columns:
            out[col] = 0
    return out


def yearly_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["year", "count", "L0", "L1", "L2", "L3"])
    base = (
        df.dropna(subset=["year"])
        .groupby("year")
        .size()
        .rename("count")
        .reset_index()
        .sort_values("year")
    )
    level_pivot = (
        df.pivot_table(
            index="year",
            columns="level",
            values="arxiv_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )
    out = base.merge(level_pivot, on="year", how="left")
    for col in ("L0", "L1", "L2", "L3"):
        if col not in out.columns:
            out[col] = 0
    return out


def category_counts(df: pd.DataFrame, top_n: int = 30) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["primary_category", "count"])
    return (
        df["primary_category"]
        .fillna("unknown")
        .value_counts()
        .head(top_n)
        .rename_axis("primary_category")
        .reset_index(name="count")
    )


def growth_rates(monthly: pd.DataFrame) -> pd.DataFrame:
    if monthly.empty:
        return monthly
    out = monthly.copy()
    out["mom_pct"] = out["count"].pct_change() * 100.0
    # year-over-year if enough history
    out["yoy_pct"] = out["count"].pct_change(12) * 100.0
    return out


def summarize(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "total_candidates": 0,
            "by_level": {},
            "writing_only": 0,
            "date_min": None,
            "date_max": None,
        }
    return {
        "total_candidates": int(len(df)),
        "by_level": {k: int(v) for k, v in df["level"].value_counts().to_dict().items()},
        "writing_only": int((df["writing_only"] == 1).sum()),
        "date_min": str(df["published_dt"].min()) if df["published_dt"].notna().any() else None,
        "date_max": str(df["published_dt"].max()) if df["published_dt"].notna().any() else None,
        "mean_score": float(df["score"].mean()) if "score" in df else None,
    }


def run_aggregate(settings: dict[str, Any] | None = None) -> dict[str, Path]:
    settings = settings or load_settings()
    ensure_data_dirs(settings)
    stats_dir = resolve(settings["paths"]["stats_dir"])
    stats_dir.mkdir(parents=True, exist_ok=True)

    df = load_joined_frame(settings)
    monthly = monthly_counts(df)
    yearly = yearly_counts(df)
    cats = category_counts(df)
    monthly_growth = growth_rates(monthly)
    summary = summarize(df)
    milestones = load_milestones(settings)

    paths = {
        "monthly": stats_dir / "monthly_counts.csv",
        "yearly": stats_dir / "yearly_counts.csv",
        "categories": stats_dir / "category_counts.csv",
        "monthly_growth": stats_dir / "monthly_growth.csv",
        "summary": stats_dir / "summary.json",
        "milestones": stats_dir / "milestones.json",
        "top_papers": stats_dir / "top_papers.csv",
    }

    monthly.to_csv(paths["monthly"], index=False)
    yearly.to_csv(paths["yearly"], index=False)
    cats.to_csv(paths["categories"], index=False)
    monthly_growth.to_csv(paths["monthly_growth"], index=False)

    with paths["summary"].open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with paths["milestones"].open("w", encoding="utf-8") as f:
        json.dump(milestones, f, indent=2, ensure_ascii=False)

    if not df.empty:
        top = df.sort_values(["score", "published"], ascending=[False, False]).head(100)
        export_cols = [
            c
            for c in [
                "arxiv_id",
                "title",
                "published",
                "primary_category",
                "score",
                "level",
                "writing_only",
                "pdf_url",
            ]
            if c in top.columns
        ]
        top[export_cols].to_csv(paths["top_papers"], index=False)
    else:
        pd.DataFrame().to_csv(paths["top_papers"], index=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Stats written under {stats_dir}")
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate candidate time series")
    parser.parse_args(argv)
    run_aggregate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
