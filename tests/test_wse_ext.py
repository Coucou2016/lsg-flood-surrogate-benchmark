"""Tiny-fixture tests for Fraehr-style EXT + WSE dual path."""

from pathlib import Path

import numpy as np

from lsg.data import generate_synthetic_floodplain
from lsg.lsg_max import LSGMaxModel
from lsg.lsg_ts import LSGTSModel
from lsg.wse_ext import (
    classify_extent_cells,
    depth_to_extent,
    depth_to_wse,
    field_mode,
    normalize_field,
    wse_to_depth,
)


def _cfg(field: str = "wse_ext") -> dict:
    return {
        "hydrodynamic": {
            "depth_threshold_m": 0.03,
            "hf_cell_size_m": 25,
            "extent_binary_threshold": 0.5,
        },
        "lsg": {
            "field": field,
            "weight_by_cell_area": False,
            "max_eof_modes": 12,
            "inducing_point_fraction": 0.25,
            "train_test_split": 0.75,
            "random_seed": 0,
            "zoning": "none",
        },
    }


def test_normalize_field():
    assert normalize_field(None) == "depth"
    assert normalize_field("depth") == "depth"
    assert normalize_field("wse_ext") == "wse_ext"
    assert normalize_field("fraehr") == "wse_ext"
    assert field_mode({"lsg": {}}) == "depth"
    assert field_mode({"lsg": {"field": "wse_ext"}}) == "wse_ext"


def test_depth_wse_roundtrip():
    z = np.array([10.0, 11.0, 12.0])
    depth = np.array([[0.0, 0.5, 0.0], [1.0, 0.0, 2.0]])
    wse = depth_to_wse(depth, z)
    back = wse_to_depth(wse, z, 0.03)
    np.testing.assert_allclose(back, depth)
    ext = depth_to_extent(depth, 0.03)
    assert ext[0, 1] == 1.0
    assert ext[0, 0] == 0.0


def test_dual_lsg_ts_smoke_and_persist(tmp_path: Path):
    cfg = _cfg("wse_ext")
    data = generate_synthetic_floodplain(
        n_events=8, n_timesteps=10, shape_hf=(12, 16), lf_factor=4, seed=3
    )
    hf, lf = data["hf_depth"], data["lf_depth"]
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]
    n_train = 6

    model = LSGTSModel(cfg)
    model.fit(hf[:n_train], lf[:n_train], terrain, shape_hf, shape_lf)
    assert model.state is not None
    assert model.state.field == "wse_ext"
    pred = model.predict(lf[n_train:], terrain, shape_hf, shape_lf)
    assert pred.shape == hf[n_train:].shape
    assert np.nanmin(pred) >= 0.0
    metrics = model.evaluate(pred, hf[n_train:])
    assert metrics["max_csi"] > 0.4

    path = tmp_path / "lsg_ts_dual.npz"
    model.save(path)
    assert path.is_file()
    assert Path(str(path.with_suffix("")) + "_ext.npz").is_file()
    assert Path(str(path.with_suffix("")) + "_wse.npz").is_file()

    loaded = LSGTSModel.load_from(path, cfg)
    pred2 = loaded.predict(lf[n_train:], terrain, shape_hf, shape_lf)
    np.testing.assert_allclose(pred, pred2, atol=1e-5, equal_nan=True)


def test_dual_vs_depth_both_run():
    data = generate_synthetic_floodplain(
        n_events=6, n_timesteps=8, shape_hf=(10, 12), lf_factor=2, seed=5
    )
    hf, lf = data["hf_depth"], data["lf_depth"]
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]

    depth_m = LSGMaxModel(_cfg("depth"))
    depth_m.fit(hf[:4], lf[:4], terrain, shape_hf, shape_lf)
    pred_d = depth_m.predict(lf[4:], terrain, shape_hf, shape_lf)

    dual_m = LSGMaxModel(_cfg("wse_ext"))
    dual_m.fit(hf[:4], lf[:4], terrain, shape_hf, shape_lf)
    pred_x = dual_m.predict(lf[4:], terrain, shape_hf, shape_lf)

    assert pred_d.shape == pred_x.shape
    # Dual is a different model; predictions need not match, but must be finite.
    assert np.isfinite(pred_x).all()
    wet, af, tf = classify_extent_cells(
        np.nanmax(hf[:4], axis=1), 0.03
    )
    assert wet.size >= tf.size
    assert af.size + tf.size >= wet.size or tf.size == wet.size
