"""Hierarchical residual zonal EOF: residual-only zones and continuity."""

import numpy as np

from lsg import eof, zoning
from lsg.base import load_state, save_state
from lsg.lsg_max import LSGMaxModel


def _global_plus_left_bump(n=18, ny=8, nx=10, seed=0):
    rng = np.random.default_rng(seed)
    n_cells = ny * nx
    phi_g = np.linspace(0.2, 1.0, n_cells)
    c = rng.normal(size=(n, 1)) + 1.8
    h = c @ phi_g.reshape(1, -1) + 0.4
    left = np.zeros(n_cells)
    left[: n_cells // 2] = 1.0
    r = rng.normal(size=(n, 1)) * 0.35
    h = h + r @ left.reshape(1, -1)
    labels = np.zeros(n_cells, dtype=np.int32)
    labels[n_cells // 2 :] = 1
    return h, labels, ny, nx


def test_hierarchical_residual_only_roundtrip():
    h, labels, _, _ = _global_plus_left_bump()
    pca, mean = eof.fit_eof(h, n_components=2)
    global_modes = pca.components_[:1]
    recon_g = eof.reconstruct_from_ecs(
        eof.project_pseudo_ecs(h, global_modes, None, mean),
        global_modes,
        mean,
        None,
    )
    resid = h - recon_g
    hier = zoning.fit_residual_eofs(resid, labels, weights=None, n_modes=2)
    ecs_g, ecs_z = zoning.project_hierarchical(
        h, global_modes, mean, None, hier
    )
    recon = zoning.reconstruct_hierarchical(
        ecs_g, global_modes, mean, None, ecs_z, hier
    )
    np.testing.assert_allclose(recon, h, atol=1e-6)

    zeros = [np.zeros_like(z) for z in ecs_z]
    recon0 = zoning.reconstruct_hierarchical(
        ecs_g, global_modes, mean, None, zeros, hier
    )
    np.testing.assert_allclose(recon0, recon_g, atol=1e-10)


def test_hierarchical_jump_smaller_than_hard_partition():
    h, labels, ny, nx = _global_plus_left_bump()
    pca, mean = eof.fit_eof(h, n_components=2)
    global_modes = pca.components_[:1]
    recon_g = eof.reconstruct_from_ecs(
        eof.project_pseudo_ecs(h, global_modes, None, mean),
        global_modes,
        mean,
        None,
    )
    resid = h - recon_g
    hier = zoning.fit_residual_eofs(resid, labels, None, 2)
    ecs_g, ecs_z = zoning.project_hierarchical(h, global_modes, mean, None, hier)
    h_res = zoning.reconstruct_hierarchical(
        ecs_g, global_modes, mean, None, ecs_z, hier
    )

    # Hard partition: independent 2-mode EOF on raw depth in each half
    hard = np.empty_like(h)
    for z in (0, 1):
        mask = labels == z
        pca_z, mean_z = eof.fit_eof(h[:, mask], n_components=2)
        ecs = eof.project_pseudo_ecs(h[:, mask], pca_z.components_, None, mean_z)
        hard[:, mask] = eof.reconstruct_from_ecs(
            ecs, pca_z.components_, mean_z, None
        )

    cut = nx // 2
    h2 = h_res.reshape(-1, ny, nx)
    hard2 = hard.reshape(-1, ny, nx)
    jump_h = np.mean(np.abs(h2[:, :, cut] - h2[:, :, cut - 1]))
    jump_hard = np.mean(np.abs(hard2[:, :, cut] - hard2[:, :, cut - 1]))
    assert jump_h <= jump_hard + 1e-9


def test_zone_builders_return_requested_k():
    rng = np.random.default_rng(3)
    resid = rng.normal(size=(12, 40))
    xy = np.column_stack([np.repeat(np.arange(8), 5), np.tile(np.arange(5), 8)])
    a = zoning.build_zones(resid, "residual_kmeans", 3, xy=xy, seed=3)
    b = zoning.build_zones(resid, "wet_correlation", 3, seed=3)
    assert a.shape == (40,)
    assert b.shape == (40,)
    assert len(np.unique(a)) == 3
    assert len(np.unique(b)) == 3
    assert zoning.normalize_zoning("deferred") == "none"


def test_hlsg_state_roundtrip(tmp_path):
    cfg = {
        "hydrodynamic": {"depth_threshold_m": 0.03, "hf_cell_size_m": 25},
        "lsg": {
            "weight_by_cell_area": False,
            "max_eof_modes": 6,
            "inducing_point_fraction": 0.25,
            "train_test_split": 0.75,
            "random_seed": 0,
            "zoning": "residual_kmeans",
            "n_zones": 2,
            "residual_eof_modes": 1,
        },
    }
    from lsg.data import generate_synthetic_floodplain

    data = generate_synthetic_floodplain(
        n_events=6, n_timesteps=8, shape_hf=(12, 16), lf_factor=4, seed=4
    )
    hf, lf = data["hf_depth"], data["lf_depth"]
    model = LSGMaxModel(cfg)
    model.fit(hf[:4], lf[:4], data["terrain_hf"], data["shape_hf"], data["shape_lf"])
    assert model.state is not None
    assert model.state.zone_method == "residual_kmeans"
    assert model.state.zone_ids is not None
    assert model.state.residual_var is not None
    pred = model.predict(lf[4:], data["terrain_hf"], data["shape_hf"], data["shape_lf"])
    fmap = model.predict_uq(
        lf[4:], data["terrain_hf"], data["shape_hf"], data["shape_lf"]
    )
    assert fmap["inundation_prob"].shape == pred.shape
    assert np.all(fmap["inundation_prob"] >= 0.0)
    assert np.all(fmap["inundation_prob"] <= 1.0)
    path = tmp_path / "hlsg.npz"
    model.save(path)
    loaded = LSGMaxModel.load_from(path, cfg)
    pred2 = loaded.predict(
        lf[4:], data["terrain_hf"], data["shape_hf"], data["shape_lf"]
    )
    np.testing.assert_allclose(pred, pred2, atol=1e-6)
    state = load_state(path)
    save_state(tmp_path / "copy.npz", state, "lsg_max", cfg)
    assert loaded.state is not None
    assert loaded.state.zone_ids is not None
    assert loaded.state.residual_var is not None
