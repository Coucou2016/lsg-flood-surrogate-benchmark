"""O1–O4 oracle error-budget identity and monotonicity checks."""

import numpy as np

from lsg import diagnostics, eof, gp


def _rank_field(rng, n, n_cells, n_rank, scale):
    q, _ = np.linalg.qr(rng.normal(size=(n_cells, n_rank)))
    coef = rng.normal(size=(n, n_rank)) * scale.reshape(1, -1)
    return coef @ q.T + 0.35, q.T


def test_oracle_identity_when_lf_equals_hf_full_rank():
    rng = np.random.default_rng(0)
    n, n_cells, rank = 10, 24, 4
    hf, _ = _rank_field(rng, n, n_cells, rank, np.linspace(1.2, 0.4, rank))
    pca, mean = eof.fit_eof(hf, n_components=rank)
    full = pca.components_
    row = diagnostics.oracle_error_budget(
        hf,
        hf,
        eof_modes_full=full,
        n_modes=full.shape[0],
        hf_mean=mean,
        weights=None,
        gp_modes=None,
        threshold_m=0.03,
        split="train",
    )
    assert row["o1_rmse"] < 1e-6
    np.testing.assert_allclose(row["o1_rmse"], row["o2_rmse"], atol=1e-8)
    np.testing.assert_allclose(row["o2_rmse"], row["o3_rmse"], atol=1e-8)
    assert row["o4_rmse"] is None
    assert row["o2_minus_o1"] == 0.0 or abs(row["o2_minus_o1"]) < 1e-8


def test_oracle_o1_le_o2_le_o3_on_truncated_distorted_lf():
    rng = np.random.default_rng(2)
    n_train, n_test, n_cells = 16, 8, 30
    scale = np.linspace(1.6, 0.15, 8)
    hf_train, _ = _rank_field(rng, n_train, n_cells, 8, scale)
    hf_test, _ = _rank_field(rng, n_test, n_cells, 8, scale)
    lf_train = 0.65 * hf_train + 0.08 * rng.normal(size=hf_train.shape)
    lf_test = 0.65 * hf_test + 0.08 * rng.normal(size=hf_test.shape)
    pca, mean = eof.fit_eof(hf_train, n_components=12)
    full = pca.components_
    k = 3
    hf_ecs = eof.project_pseudo_ecs(hf_train, full[:k], None, mean)
    lf_ecs = eof.project_pseudo_ecs(lf_train, full[:k], None, mean)
    gp_modes = gp.train_ec_emulator(lf_ecs, hf_ecs, inducing_fraction=0.5)
    row = diagnostics.oracle_error_budget(
        hf_test,
        lf_test,
        eof_modes_full=full,
        n_modes=k,
        hf_mean=mean,
        weights=None,
        gp_modes=gp_modes,
        threshold_m=0.03,
        split="test",
    )
    assert row["o1_rmse"] <= row["o2_rmse"] + 1e-9
    assert row["o2_rmse"] < row["o3_rmse"]
    assert row["o4_rmse"] is not None
    # GP should not be worse than raw LF expressibility on this constructed case
    assert row["o4_rmse"] <= row["o3_rmse"] + 0.05
    assert row["n_modes"] == k
    assert row["n_modes_full"] >= k
    # Full-rank in-sample truncation vanishes
    train_row = diagnostics.oracle_error_budget(
        hf_train,
        lf_train,
        eof_modes_full=full,
        n_modes=full.shape[0],
        hf_mean=mean,
        weights=None,
        gp_modes=None,
        threshold_m=0.03,
        split="train",
    )
    assert train_row["o2_minus_o1"] < 1e-8


def test_dual_error_budget_finite_and_o4_matches_predict():
    """wse_ext DualLSGState must emit real O1–O4; O4 == predict_dual_depth."""
    from lsg.data import generate_synthetic_floodplain
    from lsg.lsg_max import LSGMaxModel
    from lsg.wse_ext import DualLSGState, predict_dual_depth

    cfg = {
        "hydrodynamic": {
            "depth_threshold_m": 0.03,
            "hf_cell_size_m": 25,
            "extent_binary_threshold": 0.5,
        },
        "lsg": {
            "field": "wse_ext",
            "weight_by_cell_area": False,
            "max_eof_modes": 12,
            "inducing_point_fraction": 0.25,
            "train_test_split": 0.75,
            "random_seed": 0,
            "zoning": "none",
        },
    }
    data = generate_synthetic_floodplain(
        n_events=8, n_timesteps=6, shape_hf=(10, 12), lf_factor=2, seed=11
    )
    hf, lf = data["hf_depth"], data["lf_depth"]
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]
    n_train = 6

    model = LSGMaxModel(cfg)
    model.fit(hf[:n_train], lf[:n_train], terrain, shape_hf, shape_lf)
    assert isinstance(model.state, DualLSGState)

    row = diagnostics.error_budget_from_state(
        model.state,
        hf[n_train:],
        lf[n_train:],
        terrain,
        shape_hf,
        shape_lf,
        time_series=False,
        split="test",
    )
    for key in ("o1_rmse", "o2_rmse", "o3_rmse", "o4_rmse"):
        assert row[key] is not None
        assert np.isfinite(row[key])
    assert row["n_samples"] > 0
    assert "dual-path" in str(row["notes"])

    # O4 full-mesh depth must match production dual predict.
    lf_test = np.nanmax(lf[n_train:], axis=1)
    hf_test = np.nanmax(hf[n_train:], axis=1)
    pred = predict_dual_depth(
        lf_test, terrain, shape_hf, shape_lf, model.state
    )
    hf_ext, lf_ext, hf_wse, lf_wse, _ = diagnostics._dual_branch_fields(
        model.state,
        hf_test,
        lf_test,
        terrain,
        shape_hf,
        shape_lf,
        None,
        None,
        None,
        0.03,
    )
    # Rebuild O4 depth via public combine helper using branch O4 fields.
    wse_stages = diagnostics._branch_oracle_stages(
        model.state.wse, hf_wse, lf_wse
    )
    ext_stages = diagnostics._branch_oracle_stages(
        model.state.ext, hf_ext, lf_ext
    )
    assert wse_stages["o4"] is not None and ext_stages["o4"] is not None
    o4_depth = diagnostics.combine_dual_stage_depth(
        ext_stages["o4"], wse_stages["o4"], model.state, terrain, 0.03
    )
    np.testing.assert_allclose(o4_depth, pred, atol=1e-5, equal_nan=True)


def test_dual_extent_threshold_inclusive_and_tf_can_miss():
    """Production uses >= thr; dry EXT must zero gated depth on TF cells."""
    from lsg.wse_ext import DualLSGState
    from lsg.base import LSGState

    terrain = np.array([10.0, 11.0, 12.0], dtype=np.float64)
    # wet=[0,1], tf=[1], af=[0]
    ext = LSGState(
        wet_idx=np.array([1], dtype=np.int64),
        hf_mean=np.zeros(1),
        eof_modes=np.ones((1, 1)),
        weights=None,
        n_modes=1,
        field="extent",
    )
    wse = LSGState(
        wet_idx=np.array([0, 1], dtype=np.int64),
        hf_mean=np.zeros(2),
        eof_modes=np.ones((1, 2)),
        weights=None,
        n_modes=1,
        field="wse",
        depth_threshold_m=0.03,
    )
    dual = DualLSGState(
        ext=ext,
        wse=wse,
        af_idx=np.array([0], dtype=np.int64),
        wet_idx=np.array([0, 1], dtype=np.int64),
        extent_binary_threshold=0.5,
    )
    # Exact threshold → wet on TF; WSE above terrain on both wet cells.
    ext_eq = np.array([[0.5]])
    wse_vals = np.array([[10.5, 11.4]])
    depth = diagnostics.combine_dual_stage_depth(
        ext_eq, wse_vals, dual, terrain, 0.03
    )
    assert depth[0, 1] > 0.0
    assert depth[0, 0] > 0.0  # AF forced wet regardless of EXT

    ext_dry = np.array([[0.49]])
    depth_miss = diagnostics.combine_dual_stage_depth(
        ext_dry, wse_vals, dual, terrain, 0.03
    )
    assert depth_miss[0, 1] == 0.0
    assert depth_miss[0, 0] > 0.0


def test_dual_error_budget_with_residual_kmeans_finite():
    from lsg.data import generate_synthetic_floodplain
    from lsg.lsg_max import LSGMaxModel
    from lsg.wse_ext import DualLSGState

    cfg = {
        "hydrodynamic": {
            "depth_threshold_m": 0.03,
            "hf_cell_size_m": 25,
            "extent_binary_threshold": 0.5,
        },
        "lsg": {
            "field": "wse_ext",
            "weight_by_cell_area": False,
            "max_eof_modes": 10,
            "inducing_point_fraction": 0.3,
            "random_seed": 1,
            "zoning": "residual_kmeans",
            "n_zones": 2,
            "residual_eof_modes": 2,
        },
    }
    data = generate_synthetic_floodplain(
        n_events=8, n_timesteps=5, shape_hf=(10, 12), lf_factor=2, seed=7
    )
    hf, lf = data["hf_depth"], data["lf_depth"]
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]
    model = LSGMaxModel(cfg)
    model.fit(hf[:5], lf[:5], terrain, shape_hf, shape_lf)
    assert isinstance(model.state, DualLSGState)
    # Residual zones attach to WSE only; binary EXT stays global.
    assert model.state.ext.zone_method == "none"
    assert model.state.wse.zone_method == "residual_kmeans"
    assert model.state.wse.zone_ids is not None
    assert len(model.state.wse.residual_eof_modes) >= 1
    row = diagnostics.error_budget_from_state(
        model.state,
        hf[5:],
        lf[5:],
        terrain,
        shape_hf,
        shape_lf,
        time_series=False,
        split="test",
    )
    assert row["o4_rmse"] is not None and np.isfinite(row["o4_rmse"])
