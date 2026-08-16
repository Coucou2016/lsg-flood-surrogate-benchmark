"""Tests for probabilistic LSG (inverse scaling, recon variance, Tobit maps)."""

import numpy as np

from lsg import eof, gp, uq
from lsg.gp import _NumpyStandardScaler, inverse_transform_gp_moments


def test_variance_inverse_scaling():
    scaler = _NumpyStandardScaler()
    scaler.mean_ = np.array([2.0])
    scaler.scale_ = np.array([4.0])
    mean, var = inverse_transform_gp_moments(
        scaler, np.array([0.0, 1.0]), np.array([1.0, 0.25])
    )
    np.testing.assert_allclose(mean, [2.0, 6.0])
    np.testing.assert_allclose(var, [16.0, 4.0])


def test_predict_ec_emulator_returns_positive_variance():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(24, 3))
    y = np.column_stack([x[:, 0] + 0.1 * rng.normal(size=24), x[:, 1]])
    modes = gp.train_ec_emulator(x, y, inducing_fraction=0.4)
    mu, va = gp.predict_ec_emulator(modes, x[:6], return_var=True)
    assert mu.shape == (6, 2)
    assert va.shape == (6, 2)
    assert np.all(va >= 0.0)
    mu_only = gp.predict_ec_emulator(modes, x[:6], return_var=False)
    np.testing.assert_allclose(mu_only, mu)


def test_reconstruction_variance_matches_monte_carlo():
    rng = np.random.default_rng(1)
    n, k, p = 5, 3, 16
    phi = rng.normal(size=(k, p))
    w = np.linspace(0.6, 1.4, p)
    mean_c = rng.normal(size=(n, k))
    var_c = rng.uniform(0.15, 0.6, size=(n, k))
    residual_var = rng.uniform(0.02, 0.08, size=p)
    closed = eof.reconstruct_variance(var_c, phi, w, residual_var)

    n_mc = 25000
    mc = np.empty((n, p), dtype=np.float64)
    hbar = np.zeros(p)
    for i in range(n):
        samples = rng.normal(mean_c[i], np.sqrt(var_c[i]), size=(n_mc, k))
        h = eof.reconstruct_from_ecs(samples, phi, hbar, w)
        h = h + rng.normal(0.0, np.sqrt(residual_var), size=(n_mc, p))
        mc[i] = h.var(axis=0)
    np.testing.assert_allclose(closed, mc, rtol=0.06, atol=0.02)


def test_inundation_probability_and_tobit_mean():
    tau = 0.03
    # Far wet, tiny variance → P≈1 and E[h]≈μ
    p_wet = uq.inundation_probability(np.array([1.0]), np.array([1e-8]), tau)
    np.testing.assert_allclose(p_wet, [1.0])
    # Far dry → P≈0 and censored mean ≈ 0
    p_dry = uq.inundation_probability(np.array([-1.0]), np.array([1e-8]), tau)
    np.testing.assert_allclose(p_dry, [0.0])
    e_dry = uq.censored_depth_mean(np.array([-1.0]), np.array([1e-8]), tau)
    np.testing.assert_allclose(e_dry, [0.0], atol=1e-10)
    # Mass straddling τ: 0 < P < 1 and E[h] > 0
    p_mid = float(uq.inundation_probability(np.array([tau]), np.array([0.04]), tau)[0])
    assert 0.4 < p_mid < 0.6
    e_mid = float(uq.censored_depth_mean(np.array([tau]), np.array([0.04]), tau)[0])
    assert e_mid > 0.0
    scores = uq.score_probabilistic(
        np.array([0.0, 0.2]),
        np.array([-0.1, 0.2]),
        np.array([0.05, 0.01]),
        tau,
    )
    assert 0.0 <= scores["brier"] <= 1.0
    assert scores["crps"] >= 0.0
    assert 0.0 <= scores["coverage_90"] <= 1.0
    assert "coverage_90_active" in scores


def test_apply_variance_scale():
    v = np.array([1.0, 4.0])
    np.testing.assert_allclose(uq.apply_variance_scale(v, 0.25), [0.25, 1.0])
    try:
        uq.apply_variance_scale(v, -1.0)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_fit_variance_scale_crps_recovers_overdispersion():
    rng = np.random.default_rng(2)
    n = 8000
    mu = rng.normal(0.25, 0.2, size=n)
    true_std = rng.uniform(0.05, 0.35, size=n)
    y = rng.normal(mu, true_std)
    # Reported variance is 4x too large (std 2x).
    var_rep = (2.0 * true_std) ** 2
    scale = uq.fit_variance_scale_crps(y, mu, var_rep)
    assert 0.2 < scale < 0.35  # ≈ 1/4 on variance
    before = uq.gaussian_coverage(y, mu, var_rep, 0.9)
    after = uq.gaussian_coverage(y, mu, scale * var_rep, 0.9)
    assert before > 0.97
    assert abs(after - 0.9) < abs(before - 0.9)
    assert abs(after - 0.9) < 0.03
    # Point RMSE path unchanged when only var_scale is applied in score_probabilistic.
    s0 = uq.score_probabilistic(y, mu, var_rep, 0.03, var_scale=1.0)
    s1 = uq.score_probabilistic(y, mu, var_rep, 0.03, var_scale=scale)
    assert s1["crps"] <= s0["crps"] + 1e-12
    np.testing.assert_allclose(s0["rmse_point"], s1["rmse_point"])


def test_fit_variance_scale_coverage_targets_nominal():
    rng = np.random.default_rng(3)
    n = 6000
    mu = rng.normal(0.0, 1.0, size=n)
    std = np.full(n, 1.5)
    y = rng.normal(mu, 1.0)
    var = std**2
    out = uq.fit_variance_scale(y, mu, var, method="coverage_90", active_only=False)
    assert out["method"] == "coverage_90"
    cov = uq.gaussian_coverage(y, mu, out["var_scale"] * var, 0.9)
    assert abs(cov - 0.9) < 0.04


def test_fit_variance_scale_none():
    out = uq.fit_variance_scale(
        np.array([0.1]), np.array([0.1]), np.array([0.01]), method="none"
    )
    assert out["var_scale"] == 1.0
    assert out["method"] == "none"
