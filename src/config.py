from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .paths import ROOT, resolve


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = resolve(str(path)) if not isinstance(path, Path) else path
    if not p.is_absolute():
        p = ROOT / p
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {p}")
    return data


def load_settings(path: str | Path = "config/settings.yaml") -> dict[str, Any]:
    return load_yaml(path)


def load_loose_keywords(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = settings or load_settings()
    return load_yaml(settings["paths"]["loose_keywords"])


def load_strict_keywords(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = settings or load_settings()
    return load_yaml(settings["paths"]["strict_keywords"])


def load_milestones(settings: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    settings = settings or load_settings()
    data = load_yaml(settings["paths"]["milestones"])
    return list(data.get("milestones") or [])
