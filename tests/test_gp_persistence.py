"""GP save/load round-trip and paper-style synthetic splits."""

from pathlib import Path

import numpy as np

from lsg import gp
from lsg.base import load_state, save_state
from lsg.config import load_config
from lsg.data import (
    PAPER_VALIDATION_IDS,
    default_synthetic_event_ids,
    generate_synthetic_floodplain,
    resolve_train_test_indices,
)
from lsg.lsg_max import LSGMaxModel
from lsg.lsg_ts import LSGTSModel


def _tiny_cfg() -> dict:
    return {
        "hydrodynamic": {"depth_threshold_m": 0.03, "hf_cell_size_m": 25},
        "lsg": {
            "weight_by_cell_area": False,
            "max_eof_modes": 8,
            "inducing_point_fraction": 0.2,
            "train_test_split": 0.75,
            "random_seed": 0,
        },
    }


def test_inducing_budget_floors_small_n_and_caps_at_n():
    # LSG-Max Grp1: 8 events × 0.02 → 2 under the bare fraction rule.
    assert gp.inducing_budget(8, 0.02, min_inducing=16) == 8
    assert gp.inducing_budget(8, 0.02, min_inducing=4) == 4
    # LSG-TS: thousands of timesteps; fraction dominates the floor.
    assert gp.inducing_budget(2100, 0.02, min_inducing=16) == 42
    assert gp.inducing_budget(1, 0.02, min_inducing=16) == 1


def test_inducing_points_are_training_rows_not_diagonal():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 5))
    z = gp._inducing_points(x, 6)
    assert z.shape == (6, 5)
    # Every inducing row must exist in the training matrix.
    for row in z:
        assert np.any(np.all(np.isclose(x, row), axis=1))
    # Full budget → exact copy of X (SGPR degenerates to GPR).
    z_full = gp._inducing_points(x, 20)
    np.testing.assert_allclose(z_full, x)


def test_default_synthetic_ids_cover_paper_holdout():
    ids = default_synthetic_event_ids(12)
    assert set(PAPER_VALIDATION_IDS).issubset(set(ids))
    assert "FE20" in ids
    assert "synthetic_event_00" not in ids


def test_synthetic_bundle_uses_splits_yaml():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "config" / "brisbane.yaml")
    cfg.setdefault("events", {})["synthetic_only"] = True
    data = generate_synthetic_floodplain(
        n_events=12, n_timesteps=8, shape_hf=(12, 16), lf_factor=4, seed=0
    )
    ts_train, ts_test, ts_how = resolve_train_test_indices(
        data["event_ids"], cfg, "lsg_ts"
    )
    mx_train, mx_test, mx_how = resolve_train_test_indices(
        data["event_ids"], cfg, "lsg_max"
    )
    assert ts_how.startswith("paper:")
    assert mx_how.startswith("paper:")
    assert ts_train.size == 6
    assert mx_train.size > ts_train.size
    assert ts_test.size == 4
    assert set(data["event_ids"][i] for i in ts_test.tolist()) == set(PAPER_VALIDATION_IDS)
    assert set(data["event_ids"][i] for i in mx_test.tolist()) == set(PAPER_VALIDATION_IDS)


def test_gp_state_roundtrip_predict_without_retrain(tmp_path):
    cfg = _tiny_cfg()
    data = generate_synthetic_floodplain(
        n_events=8, n_timesteps=12, shape_hf=(12, 16), lf_factor=4, seed=1
    )
    hf, lf = data["hf_depth"], data["lf_depth"]
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]
    n_train = 6

    model = LSGTSModel(cfg)
    model.fit(hf[:n_train], lf[:n_train], terrain, shape_hf, shape_lf)
    pred_fit = model.predict(lf[n_train:], terrain, shape_hf, shape_lf)

    path = tmp_path / "lsg_ts_state.npz"
    model.save(path)
    raw = np.load(path)
    assert "gp_n_modes" in raw.files
    assert int(raw["gp_n_modes"]) >= 1
    assert str(raw["gp_0_kind"]) in {"rbf", "sgpr"}

    loaded = LSGTSModel.load_from(path, cfg)
    assert loaded.state is not None
    assert len(loaded.state.gp_modes) == len(model.state.gp_modes)
    pred_load = loaded.predict(lf[n_train:], terrain, shape_hf, shape_lf)
    np.testing.assert_allclose(pred_fit, pred_load, atol=1e-6)

    # Direct base helpers
    state = load_state(path)
    save_state(tmp_path / "copy.npz", state, "lsg_ts", cfg)
    pred_again = LSGTSModel.load_from(tmp_path / "copy.npz", cfg).predict(
        lf[n_train:], terrain, shape_hf, shape_lf
    )
    np.testing.assert_allclose(pred_fit, pred_again, atol=1e-6)


def test_lsg_max_state_roundtrip(tmp_path):
    cfg = _tiny_cfg()
    data = generate_synthetic_floodplain(
        n_events=6, n_timesteps=10, shape_hf=(12, 16), lf_factor=4, seed=2
    )
    hf, lf = data["hf_depth"], data["lf_depth"]
    model = LSGMaxModel(cfg)
    model.fit(hf[:4], lf[:4], data["terrain_hf"], data["shape_hf"], data["shape_lf"])
    pred = model.predict(lf[4:], data["terrain_hf"], data["shape_hf"], data["shape_lf"])
    path = tmp_path / "lsg_max_state.npz"
    model.save(path)
    loaded = LSGMaxModel.load_from(path, cfg)
    pred2 = loaded.predict(lf[4:], data["terrain_hf"], data["shape_hf"], data["shape_lf"])
    np.testing.assert_allclose(pred, pred2, atol=1e-6)
    expected = "gpflow" if gp.gpflow_available() else "numpy"
    assert loaded.state.gp_backend == expected
