from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    arxiv_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    categories TEXT NOT NULL,
    primary_category TEXT,
    published TEXT,
    updated TEXT,
    comment TEXT,
    journal_ref TEXT,
    doi TEXT,
    pdf_url TEXT,
    entry_json TEXT,
    collected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classifications (
    arxiv_id TEXT PRIMARY KEY,
    stage TEXT NOT NULL,
    score REAL NOT NULL,
    level TEXT NOT NULL,
    matched_terms_json TEXT NOT NULL,
    writing_only INTEGER NOT NULL DEFAULT 0,
    classified_at TEXT NOT NULL,
    FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
);

CREATE TABLE IF NOT EXISTS collect_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    query TEXT,
    fetched INTEGER DEFAULT 0,
    upserted INTEGER DEFAULT 0,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_papers_published ON papers(published);
CREATE INDEX IF NOT EXISTS idx_papers_primary_category ON papers(primary_category);
CREATE INDEX IF NOT EXISTS idx_class_level ON classifications(level);
CREATE INDEX IF NOT EXISTS idx_class_score ON classifications(score);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def db_session(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def upsert_paper(conn: sqlite3.Connection, paper: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO papers (
            arxiv_id, title, abstract, authors_json, categories,
            primary_category, published, updated, comment, journal_ref,
            doi, pdf_url, entry_json, collected_at
        ) VALUES (
            :arxiv_id, :title, :abstract, :authors_json, :categories,
            :primary_category, :published, :updated, :comment, :journal_ref,
            :doi, :pdf_url, :entry_json, :collected_at
        )
        ON CONFLICT(arxiv_id) DO UPDATE SET
            title=excluded.title,
            abstract=excluded.abstract,
            authors_json=excluded.authors_json,
            categories=excluded.categories,
            primary_category=excluded.primary_category,
            published=excluded.published,
            updated=excluded.updated,
            comment=excluded.comment,
            journal_ref=excluded.journal_ref,
            doi=excluded.doi,
            pdf_url=excluded.pdf_url,
            entry_json=excluded.entry_json,
            collected_at=excluded.collected_at
        """,
        paper,
    )


def upsert_classification(conn: sqlite3.Connection, row: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO classifications (
            arxiv_id, stage, score, level, matched_terms_json,
            writing_only, classified_at
        ) VALUES (
            :arxiv_id, :stage, :score, :level, :matched_terms_json,
            :writing_only, :classified_at
        )
        ON CONFLICT(arxiv_id) DO UPDATE SET
            stage=excluded.stage,
            score=excluded.score,
            level=excluded.level,
            matched_terms_json=excluded.matched_terms_json,
            writing_only=excluded.writing_only,
            classified_at=excluded.classified_at
        """,
        row,
    )


def paper_to_row(paper: dict[str, Any]) -> dict[str, Any]:
    return {
        "arxiv_id": paper["arxiv_id"],
        "title": paper.get("title") or "",
        "abstract": paper.get("abstract") or "",
        "authors_json": json.dumps(paper.get("authors") or [], ensure_ascii=False),
        "categories": paper.get("categories") or "",
        "primary_category": paper.get("primary_category"),
        "published": paper.get("published"),
        "updated": paper.get("updated"),
        "comment": paper.get("comment"),
        "journal_ref": paper.get("journal_ref"),
        "doi": paper.get("doi"),
        "pdf_url": paper.get("pdf_url"),
        "entry_json": json.dumps(paper, ensure_ascii=False),
        "collected_at": paper.get("collected_at") or utc_now(),
    }
