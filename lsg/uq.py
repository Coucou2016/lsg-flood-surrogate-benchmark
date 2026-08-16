"""Probabilistic LSG scoring and flood-map utilities.

Depth is physically non-negative and treated as dry below a threshold τ
(default 0.03 m). Linear EOF reconstruction yields a *latent* Gaussian
Z ~ N(μ, σ²) that can put mass below τ.

Observation model (Tobit / Type-I left-censoring, not a renormalised
truncated Gaussian):

    h = 0  if Z < τ
    h = Z  if Z ≥ τ

Dry probability mass stays an atom at 0 rather than being folded back
onto the wet support. That is the right analogue of the operational
``depth = 0 if depth < τ`` map.

Consequences:

- Inundation probability is P(Z ≥ τ) = 1 - Φ((τ - μ) / σ).
- Expected mapped depth is the censored mean
  E[h] = E[Z * 1_{Z≥τ}] = μ (1-Φ(α)) + σ φ(α), α = (τ-μ)/σ.
- CRPS below is the closed-form Gaussian CRPS of the latent law against
  the observed depth (dry = 0). Brier score is the proper binary score
  for the inundation map.

GP EC variance is mapped through the linear reconstruction and then
inflated by a cell-wise residual/truncation variance (see ``eof.reconstruct_variance``)
so retained-mode GP variance is not used alone.

Variance calibration (paper innovation A)
----------------------------------------
Adding train truncation MSE often yields *over-coverage* (intervals too
wide): nominal 50/90% bands contain far more than 50/90% of observations.
We apply a single global multiplicative scale ``s`` to predictive variance,

    Var_cal = s * Var_raw ,

with ``s`` chosen on *training* predictions (same train events used for
fitting; subsampled for LSG-TS via ``uq_calibration_max_rows``) by
minimising mean Gaussian CRPS (a proper scoring rule). This is
in-sample train tuning of variance only — not an independent held-out
calibration split and not test-set leakage. The latent mean is untouched,
so operational point maps (CSI / RMSE) are unchanged. Prefer this over
isotonic PIT
warping: one scalar, closed-form CRPS, no binning artefacts.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import erf
from scipy.stats import norm

_SQRT2 = np.sqrt(2.0)
_SQRT_PI = np.sqrt(np.pi)
_INV_SQRT_2PI = 1.0 / np.sqrt(2.0 * np.pi)

VarianceCalibMethod = Literal["crps_scale", "coverage_90", "none"]


def _as_float_arrays(*arrays: np.ndarray) -> tuple[np.ndarray, ...]:
    return tuple(np.asarray(a, dtype=np.float64) for a in arrays)


def _std(var: np.ndarray, min_std: float = 1e-12) -> np.ndarray:
    return np.maximum(np.sqrt(np.maximum(np.asarray(var, dtype=np.float64), 0.0)), min_std)


def normal_pdf(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=np.float64)
    return _INV_SQRT_2PI * np.exp(-0.5 * z * z)


def normal_cdf(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=np.float64)
    return 0.5 * (1.0 + erf(z / _SQRT2))


def inundation_probability(
    latent_mean: np.ndarray,
    latent_var: np.ndarray,
    threshold_m: float = 0.03,
) -> np.ndarray:
    """P(Z ≥ τ) for latent Z ~ N(μ, σ²). Degenerate σ → hard threshold."""
    mu, var = _as_float_arrays(latent_mean, latent_var)
    std = np.sqrt(np.maximum(var, 0.0))
    out = np.empty_like(mu)
    tiny = std < 1e-15
    out[tiny] = (mu[tiny] >= threshold_m).astype(np.float64)
    ok = ~tiny
    alpha = (threshold_m - mu[ok]) / std[ok]
    out[ok] = 1.0 - normal_cdf(alpha)
    return np.clip(out, 0.0, 1.0)


def censored_depth_mean(
    latent_mean: np.ndarray,
    latent_var: np.ndarray,
    threshold_m: float = 0.03,
) -> np.ndarray:
    """Tobit expected depth E[h] with dry atom at 0 and wet values Z ≥ τ."""
    mu, var = _as_float_arrays(latent_mean, latent_var)
    std = np.sqrt(np.maximum(var, 0.0))
    out = np.empty_like(mu)
    tiny = std < 1e-15
    out[tiny] = np.where(mu[tiny] >= threshold_m, np.maximum(mu[tiny], 0.0), 0.0)
    ok = ~tiny
    alpha = (threshold_m - mu[ok]) / std[ok]
    surv = 1.0 - normal_cdf(alpha)
    out[ok] = mu[ok] * surv + std[ok] * normal_pdf(alpha)
    return np.maximum(out, 0.0)


def threshold_latent_mean(
    latent_mean: np.ndarray,
    threshold_m: float = 0.03,
) -> np.ndarray:
    """Operational point map: zero latent mean below τ (historical LSG)."""
    mu = np.asarray(latent_mean, dtype=np.float64)
    return np.where(mu < threshold_m, 0.0, mu)


def crps_gaussian(
    obs: np.ndarray,
    mean: np.ndarray,
    var: np.ndarray,
) -> np.ndarray:
    """Closed-form CRPS of N(μ, σ²) vs observation (Gneiting & Raftery)."""
    y, mu, var = _as_float_arrays(obs, mean, var)
    std = _std(var)
    z = (y - mu) / std
    phi = normal_pdf(z)
    cdf = normal_cdf(z)
    return std * (z * (2.0 * cdf - 1.0) + 2.0 * phi - 1.0 / _SQRT_PI)


def brier_inundation(
    obs_depth: np.ndarray,
    inundation_prob: np.ndarray,
    threshold_m: float = 0.03,
) -> float:
    y = (np.asarray(obs_depth, dtype=np.float64) >= threshold_m).astype(np.float64)
    p = np.clip(np.asarray(inundation_prob, dtype=np.float64), 0.0, 1.0)
    return float(np.mean((p - y) ** 2))


def pit_values(
    obs: np.ndarray,
    mean: np.ndarray,
    var: np.ndarray,
) -> np.ndarray:
    """Gaussian PIT Φ((y-μ)/σ). Prefer wet cells under the Tobit model."""
    y, mu, var = _as_float_arrays(obs, mean, var)
    std = _std(var)
    return normal_cdf((y - mu) / std)


def gaussian_coverage(
    obs: np.ndarray,
    mean: np.ndarray,
    var: np.ndarray,
    level: float = 0.9,
    mask: np.ndarray | None = None,
) -> float:
    y, mu, var = _as_float_arrays(obs, mean, var)
    z = float(norm.ppf(0.5 + 0.5 * level))
    std = _std(var)
    hit = np.abs(y - mu) <= z * std
    if mask is not None:
        m = np.asarray(mask, dtype=bool)
        if not np.any(m):
            return float("nan")
        return float(np.mean(hit[m]))
    return float(np.mean(hit))


def active_cell_mask(
    obs: np.ndarray,
    mean: np.ndarray,
    threshold_m: float = 0.03,
) -> np.ndarray:
    """Cells that are wet in truth or in the latent mean (Tobit-relevant)."""
    y, mu = _as_float_arrays(obs, mean)
    return (y >= threshold_m) | (mu >= threshold_m)


def apply_variance_scale(var: np.ndarray, scale: float) -> np.ndarray:
    """Non-negative global scale on predictive variance (mean unchanged)."""
    s = float(scale)
    if not np.isfinite(s) or s < 0.0:
        raise ValueError(f"variance scale must be finite and >= 0, got {scale!r}")
    return np.asarray(var, dtype=np.float64) * s


def fit_variance_scale_crps(
    obs: np.ndarray,
    mean: np.ndarray,
    var: np.ndarray,
    *,
    bounds: tuple[float, float] = (1e-4, 1e2),
    mask: np.ndarray | None = None,
) -> float:
    """CRPS-optimal multiplicative variance scale on a calibration set.

    Minimises mean closed-form Gaussian CRPS of ``N(μ, s·σ²)`` vs ``obs``.
    When ``mask`` is given, only those cells enter the mean (e.g. active cells).
    """
    y, mu, va = _as_float_arrays(obs, mean, var)
    y = y.ravel()
    mu = mu.ravel()
    va = np.maximum(va.ravel(), 0.0)
    if mask is not None:
        m = np.asarray(mask, dtype=bool).ravel()
        y, mu, va = y[m], mu[m], va[m]
    if y.size == 0:
        return 1.0
    # Degenerate / zero predictive variance cannot be rescaled usefully.
    if float(np.max(va)) <= 0.0:
        return 1.0

    lo, hi = float(bounds[0]), float(bounds[1])
    if not (0.0 < lo < hi):
        raise ValueError(f"invalid bounds {bounds!r}")

    def _obj(scale: float) -> float:
        return float(np.mean(crps_gaussian(y, mu, scale * va)))

    res = minimize_scalar(_obj, bounds=(lo, hi), method="bounded")
    scale = float(res.x)
    # Prefer identity when the optimum is numerically indistinct.
    if abs(_obj(scale) - _obj(1.0)) < 1e-15 and abs(scale - 1.0) < 1e-6:
        return 1.0
    return scale


def fit_variance_scale_coverage(
    obs: np.ndarray,
    mean: np.ndarray,
    var: np.ndarray,
    *,
    level: float = 0.9,
    target: float | None = None,
    bounds: tuple[float, float] = (1e-4, 1e2),
    mask: np.ndarray | None = None,
    n_grid: int = 48,
) -> float:
    """Variance scale that matches empirical Gaussian coverage to ``target``.

    Secondary to CRPS scaling: useful when the paper target is explicit
    nominal coverage. Uses a log-spaced grid plus local refinement.
    """
    y, mu, va = _as_float_arrays(obs, mean, var)
    tgt = float(level if target is None else target)
    lo, hi = float(bounds[0]), float(bounds[1])
    grid = np.geomspace(lo, hi, int(n_grid))

    def _cov(scale: float) -> float:
        return gaussian_coverage(y, mu, scale * va, level=level, mask=mask)

    best_s = 1.0
    best_err = abs(_cov(1.0) - tgt)
    for s in grid:
        err = abs(_cov(float(s)) - tgt)
        if err < best_err:
            best_err = err
            best_s = float(s)
    # Local geometric refine around the best grid point.
    refine = np.geomspace(max(lo, best_s / 1.5), min(hi, best_s * 1.5), 25)
    for s in refine:
        err = abs(_cov(float(s)) - tgt)
        if err < best_err:
            best_err = err
            best_s = float(s)
    return best_s


def fit_variance_scale(
    obs: np.ndarray,
    mean: np.ndarray,
    var: np.ndarray,
    method: VarianceCalibMethod = "crps_scale",
    *,
    threshold_m: float = 0.03,
    active_only: bool = True,
    max_cells: int = 2_000_000,
    seed: int = 0,
) -> dict[str, Any]:
    """Fit a global predictive-variance scale; default method is CRPS.

    ``active_only`` restricts the fit to Tobit-relevant cells (obs or mean
    above τ), so EXT-gated dry zeros do not dominate the objective.
    ``max_cells`` randomly subsamples the calibration pool for memory/CPU.
    """
    method_n = str(method or "none").strip().lower()
    if method_n in {"", "none", "off", "false", "0"}:
        return {
            "method": "none",
            "var_scale": 1.0,
            "active_only": bool(active_only),
        }
    y = np.asarray(obs, dtype=np.float64).ravel()
    mu = np.asarray(mean, dtype=np.float64).ravel()
    va = np.asarray(var, dtype=np.float64).ravel()
    if active_only:
        m = active_cell_mask(y, mu, threshold_m)
        y, mu, va = y[m], mu[m], va[m]
    n_pool = int(y.size)
    if max_cells > 0 and n_pool > int(max_cells):
        rng = np.random.default_rng(int(seed))
        pick = rng.choice(n_pool, size=int(max_cells), replace=False)
        y, mu, va = y[pick], mu[pick], va[pick]
    if method_n in {"crps_scale", "crps"}:
        scale = fit_variance_scale_crps(y, mu, va)
        method_out = "crps_scale"
    elif method_n in {"coverage_90", "coverage", "cov90"}:
        scale = fit_variance_scale_coverage(y, mu, va, level=0.9, target=0.9)
        method_out = "coverage_90"
    else:
        raise ValueError(
            f"unknown UQ calibration method {method!r}; "
            "use 'crps_scale', 'coverage_90', or 'none'"
        )
    return {
        "method": method_out,
        "var_scale": float(scale),
        "active_only": bool(active_only),
        "n_calib_cells": int(y.size),
        "n_calib_pool": n_pool,
    }


def set_state_uq_var_scale(state: Any, scale: float) -> None:
    """Attach a calibrated variance scale to ``LSGState`` or ``DualLSGState``."""
    s = float(scale)
    if not np.isfinite(s) or s < 0.0:
        raise ValueError(f"variance scale must be finite and >= 0, got {scale!r}")
    state.uq_var_scale = s
    wse = getattr(state, "wse", None)
    if wse is not None and hasattr(wse, "uq_var_scale"):
        wse.uq_var_scale = s


def reliability_table(
    inundation_prob: np.ndarray,
    obs_depth: np.ndarray,
    threshold_m: float = 0.03,
    n_bins: int = 10,
) -> dict[str, np.ndarray]:
    """Predicted-P bins vs observed wet frequency."""
    p = np.clip(np.asarray(inundation_prob, dtype=np.float64).ravel(), 0.0, 1.0)
    y = (np.asarray(obs_depth, dtype=np.float64).ravel() >= threshold_m).astype(
        np.float64
    )
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    pred = np.full(n_bins, np.nan)
    freq = np.full(n_bins, np.nan)
    count = np.zeros(n_bins, dtype=np.int64)
    for i in range(n_bins):
        if i < n_bins - 1:
            mask = (p >= edges[i]) & (p < edges[i + 1])
        else:
            mask = (p >= edges[i]) & (p <= edges[i + 1])
        count[i] = int(mask.sum())
        if count[i] == 0:
            continue
        pred[i] = float(p[mask].mean())
        freq[i] = float(y[mask].mean())
    return {"bin_edges": edges, "predicted": pred, "observed": freq, "count": count}


def probabilistic_flood_map(
    latent_mean: np.ndarray,
    latent_var: np.ndarray,
    threshold_m: float = 0.03,
) -> dict[str, np.ndarray]:
    """Cell-wise probabilistic products from latent Gaussian moments."""
    mu, var = _as_float_arrays(latent_mean, latent_var)
    return {
        "latent_mean": mu,
        "latent_var": var,
        "inundation_prob": inundation_probability(mu, var, threshold_m),
        "depth_mean": censored_depth_mean(mu, var, threshold_m),
        "depth_point": threshold_latent_mean(mu, threshold_m),
    }


def score_probabilistic(
    obs_depth: np.ndarray,
    latent_mean: np.ndarray,
    latent_var: np.ndarray,
    threshold_m: float = 0.03,
    *,
    var_scale: float = 1.0,
) -> dict[str, Any]:
    """CRPS, Brier, PIT, coverage, and Tobit-mean RMSE.

    ``var_scale`` multiplies ``latent_var`` before scoring (mean unchanged).
    All-cell coverage is retained for continuity; ``coverage_*_active`` uses
    cells that are wet in truth or in the latent mean (fairer under EXT gating).
    """
    y, mu, var = _as_float_arrays(obs_depth, latent_mean, latent_var)
    if float(var_scale) != 1.0:
        var = apply_variance_scale(var, var_scale)
    fmap = probabilistic_flood_map(mu, var, threshold_m)
    crps = crps_gaussian(y, mu, var)
    wet = y >= threshold_m
    active = active_cell_mask(y, mu, threshold_m)
    pit = pit_values(y, mu, var)
    rel = reliability_table(fmap["inundation_prob"], y, threshold_m)
    return {
        "crps": float(np.mean(crps)),
        "brier": brier_inundation(y, fmap["inundation_prob"], threshold_m),
        "coverage_90": gaussian_coverage(y, mu, var, 0.9),
        "coverage_50": gaussian_coverage(y, mu, var, 0.5),
        "coverage_90_active": gaussian_coverage(y, mu, var, 0.9, mask=active),
        "coverage_50_active": gaussian_coverage(y, mu, var, 0.5, mask=active),
        "pit_mean_wet": float(np.mean(pit[wet])) if np.any(wet) else float("nan"),
        "rmse_censored_mean": float(
            np.sqrt(np.mean((fmap["depth_mean"] - y) ** 2))
        ),
        "rmse_point": float(np.sqrt(np.mean((fmap["depth_point"] - y) ** 2))),
        "mean_inundation_prob": float(np.mean(fmap["inundation_prob"])),
        "var_scale": float(var_scale),
        "reliability": {
            "predicted": rel["predicted"].tolist(),
            "observed": rel["observed"].tolist(),
            "count": rel["count"].tolist(),
        },
    }
