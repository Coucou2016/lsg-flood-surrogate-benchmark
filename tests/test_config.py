"""Config path resolution must not depend on a previous drive letter."""

import os
from pathlib import Path

from lsg.config import load_config, resolve_path


def test_load_config_infers_repo_root(tmp_path, monkeypatch):
    monkeypatch.delenv("LSG_PROJECT_ROOT", raising=False)
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    cfg_path = cfg_dir / "brisbane.yaml"
    cfg_path.write_text(
        "paths:\n  project_root: null\n  evaluation: outputs/evaluation\n",
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    assert cfg["_project_root"] == tmp_path.resolve()
    assert resolve_path(cfg, "evaluation") == (tmp_path / "outputs" / "evaluation").resolve()


def test_env_overrides_yaml(tmp_path, monkeypatch):
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("LSG_PROJECT_ROOT", str(other))
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    cfg_path = cfg_dir / "case.yaml"
    cfg_path.write_text(
        "paths:\n  project_root: D:/does-not-exist\n  models: outputs/models\n",
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    assert cfg["_project_root"] == other.resolve()


def test_repo_brisbane_yaml_points_here():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "config" / "brisbane.yaml")
    assert cfg["_project_root"] == root.resolve()
    assert "d:/Projects" not in str(cfg["_project_root"]).replace("\\", "/").lower()
    eval_dir = resolve_path(cfg, "evaluation")
    assert eval_dir == (root / "outputs" / "evaluation").resolve()


def test_repo_merced_yaml_points_here():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "config" / "merced.yaml")
    assert cfg["_project_root"] == root.resolve()
    eval_dir = resolve_path(cfg, "evaluation")
    assert eval_dir == (root / "outputs" / "evaluation" / "merced").resolve()


def test_repo_chowilla_yaml_points_here():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "config" / "chowilla.yaml")
    assert cfg["_project_root"] == root.resolve()
    eval_dir = resolve_path(cfg, "evaluation")
    assert eval_dir == (root / "outputs" / "evaluation" / "chowilla").resolve()
    assert cfg["lsg"]["field"] == "wse_ext"
    assert cfg["lsg"]["min_inducing_points"] == 16
