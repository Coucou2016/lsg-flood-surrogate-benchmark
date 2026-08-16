import numpy as np

from lsg import evaluation


def test_perfect_csi():
    d = np.array([0.0, 0.1, 0.0, 0.2])
    m = evaluation.extent_metrics(d, d, threshold_m=0.03)
    assert m["csi"] == 1.0
    assert m["pod"] == 1.0
    assert m["rfa"] == 0.0


def test_max_surface_metrics_uses_time_axis():
    pred = np.zeros((2, 3, 4))
    ref = np.zeros((2, 3, 4))
    pred[0, 2, 1] = 0.2
    ref[0, 1, 1] = 0.2
    pred[1, 0, 2] = 0.2
    ref[1, 2, 2] = 0.2
    m = evaluation.max_surface_metrics(pred, ref, threshold_m=0.03)
    assert m["csi"] == 1.0


def test_csi_invariant_to_extra_dry_cells():
    """Fraehr wet_idx vs full domain: CSI ignores correct negatives."""
    pred = np.array([0.2, 0.0, 0.15, 0.0, 0.0])
    ref = np.array([0.2, 0.1, 0.0, 0.0, 0.0])
    wet = np.array([0, 1, 2])
    full = evaluation.extent_metrics(pred, ref, threshold_m=0.03)
    masked = evaluation.extent_metrics(pred, ref, threshold_m=0.03, cell_mask=wet)
    assert full["csi"] == masked["csi"]
    assert full["pod"] == masked["pod"]
    assert full["rfa"] == masked["rfa"]
    assert full["ct_hits"] == masked["ct_hits"]
    assert full["rmse"] < masked["rmse"]  # dry zeros dilute domain RMSE


def test_gate_by_extent_removes_false_alarms():
    pred = np.array([0.2, 0.2, 0.0])
    ref = np.array([0.2, 0.0, 0.0])
    extent = np.array([0.2, 0.0, 0.0])  # second cell dry in LF extent
    raw = evaluation.extent_metrics(pred, ref, threshold_m=0.03)
    gated = evaluation.extent_metrics(
        evaluation.gate_by_extent(pred, extent, 0.03), ref, threshold_m=0.03
    )
    assert raw["ct_false_alarms"] == 1
    assert gated["ct_false_alarms"] == 0
    assert gated["csi"] == 1.0


def test_dual_score_includes_wet_and_gate():
    pred = np.array([[0.2, 0.2, 0.0, 0.0]])
    ref = np.array([[0.2, 0.0, 0.0, 0.0]])
    wet = np.array([0, 1, 2])
    gate = np.array([[0.2, 0.0, 0.0, 0.0]])
    scores = evaluation.dual_score_max_surface(
        pred, ref, wet_idx=wet, threshold_m=0.03, extent_gate=gate
    )
    assert "all_cells" in scores and "wet_train" in scores
    assert "lf_extent_gated" in scores
    assert scores["all_cells"]["csi"] < scores["lf_extent_gated"]["csi"]
