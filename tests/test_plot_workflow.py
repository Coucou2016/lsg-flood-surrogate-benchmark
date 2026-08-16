"""Smoke test for workflow plots (matplotlib)."""

import sys
from pathlib import Path

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from plot_workflow_results import plot_results  # noqa: E402


def test_plot_results_synthetic_demo(tmp_path):
    ny, nx = 8, 10
    examples = tmp_path / "pred_examples.npz"
    np.savez_compressed(
        examples,
        terrain_hf=np.zeros(ny * nx),
        shape_hf=np.array([ny, nx]),
        shape_lf=np.array([2, 2]),
        test_ids=np.array(["FE21", "FE26"]),
        hf_max=np.ones((2, ny * nx)),
        pred_lsg_max=np.ones((2, ny * nx)) * 0.8,
        pred_lsg_ts_max=np.ones((2, ny * nx)) * 0.9,
        lf_upsampled_max=np.ones((2, ny * nx)) * 0.5,
        data_mode=np.array("synthetic"),
    )
    summary = {
        "data_mode": "synthetic",
        "lsg_ts": {"eval_csi": 0.8, "eval_pod": 0.9, "eval_rmse": 0.1, "holdout": {}},
        "lsg_max": {
            "csi": 0.7,
            "pod": 0.85,
            "rmse": 0.12,
            "holdout": {
                "FE21": {"csi": 0.7, "ve_label": "VE1"},
                "FE26": {"csi": 0.6, "ve_label": "VE2"},
            },
        },
        "lf_only_max": {"csi": 0.5, "pod": 0.6, "rmse": 0.2},
        "resolution_comparison": {
            "lf120": {"max_csi": 0.75, "max_pod": 0.8, "max_rmse": 0.11},
            "lf300": {"max_csi": 0.65, "max_pod": 0.7, "max_rmse": 0.18},
            "_mode": "synthetic",
        },
    }
    out = tmp_path / "figures"
    paths = plot_results(summary, examples, out)
    names = {p.name for p in paths}
    assert "metrics_comparison.png" in names
    assert "resolution_comparison.png" in names
    assert "holdout_ve_csi.png" in names
    assert "example_inundation.png" in names
    assert all(p.is_file() for p in paths)
