"""Tests for inundation_prob export into pred_examples and figure helpers."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from lsg import uq


def test_inundation_prob_panel_prefers_stored_field(tmp_path: Path):
    """Spatial figure path should detect inundation_prob_lsg_max when present."""
    n = 20
    pred = tmp_path / "pred_examples.npz"
    np.savez_compressed(
        pred,
        terrain_hf=np.zeros(n),
        shape_hf=np.array([n, 1]),
        shape_lf=np.array([n, 1]),
        test_ids=np.array(["E1"]),
        hf_max=np.linspace(0, 1, n)[None, :],
        pred_lsg_max=np.linspace(0, 0.8, n)[None, :],
        lf_upsampled_max=np.linspace(0, 0.5, n)[None, :],
        data_mode=np.array("real"),
        inundation_prob_lsg_max=np.clip(np.linspace(0.1, 0.9, n), 0, 1)[None, :],
    )
    raw = np.load(pred, allow_pickle=True)
    assert "inundation_prob_lsg_max" in raw.files
    p = np.asarray(raw["inundation_prob_lsg_max"][0])
    assert p.shape == (n,)
    assert np.all((p >= 0) & (p <= 1))


def test_probabilistic_flood_map_exports_inundation_prob():
    mu = np.array([0.1, 0.5, -0.2], dtype=np.float64)
    var = np.array([0.04, 0.01, 0.09], dtype=np.float64)
    fmap = uq.probabilistic_flood_map(mu, var, 0.03)
    assert "inundation_prob" in fmap
    assert fmap["inundation_prob"].shape == mu.shape
    assert np.all(fmap["inundation_prob"] >= 0.0)
    assert np.all(fmap["inundation_prob"] <= 1.0)


def test_make_figures_artifacts_registry_has_new_keys():
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "make_figures", root / "scripts" / "make_figures.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for key in ("burnett_global", "chowilla_uq", "burnett_uq", "chowilla_wet_corr"):
        assert key in mod.ARTIFACTS
