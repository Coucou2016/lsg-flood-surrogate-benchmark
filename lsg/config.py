"""Load YAML configuration for case studies."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_ENV_ROOT = "LSG_PROJECT_ROOT"


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path).resolve()
    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg.setdefault("paths", {})
    cfg["_config_path"] = path
    cfg["_project_root"] = _resolve_project_root(path, cfg)
    return cfg


def _resolve_project_root(config_path: Path, cfg: dict[str, Any]) -> Path:
    """
    Resolve the project root without baking in a drive letter.

    Order: $LSG_PROJECT_ROOT, then YAML ``paths.project_root`` if set to an
    absolute path, then the directory that contains ``config/`` (parent of the
    YAML file's parent). Relative YAML values are interpreted from that inferred
    root so moving the repo does not break paths.
    """
    env = os.environ.get(_ENV_ROOT, "").strip()
    if env:
        return Path(env).expanduser().resolve()

    inferred = config_path.parent.parent
    raw = cfg.get("paths", {}).get("project_root")
    if raw is None or str(raw).strip() in ("", ".", "null", "None"):
        return inferred.resolve()

    p = Path(str(raw).strip()).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (inferred / p).resolve()


def resolve_path(cfg: dict[str, Any], key: str) -> Path:
    rel = cfg["paths"][key]
    return resolve_path_value(cfg, rel)


def resolve_path_value(cfg: dict[str, Any], rel: str | Path) -> Path:
    p = Path(rel)
    if p.is_absolute():
        return p
    return (cfg["_project_root"] / p).resolve()
