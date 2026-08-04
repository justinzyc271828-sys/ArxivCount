from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resolve(path_str: str) -> Path:
    """Resolve a project-relative path string against the repo root."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    return ROOT / p


def ensure_data_dirs(settings: dict) -> None:
    paths = settings.get("paths", {})
    for key in (
        "raw_dir",
        "downloads_dir",
        "candidates_dir",
        "curated_dir",
        "stats_dir",
    ):
        resolve(paths[key]).mkdir(parents=True, exist_ok=True)
    db = resolve(paths["db_path"])
    db.parent.mkdir(parents=True, exist_ok=True)
