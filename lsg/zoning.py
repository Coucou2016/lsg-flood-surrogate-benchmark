"""Hierarchical residual zonal EOF (H-LSG).

Hard partitions of the full water surface create jumps at zone boundaries.
H-LSG keeps a global EOF for basin-scale filling and lets zones model
*residuals only*::

    h = Φ_global c_global + Σ_z 1_z Φ_z^res c_z

Config ``lsg.zoning``:

- ``none`` / ``global`` / ``deferred`` — global-only baseline (A/B control)
- ``residual_kmeans`` — k-means on per-cell residual magnitude (+ optional XY)
- ``wet_correlation`` — k-means on standardised cell hydrographs (correlation proxy)

Residual ECs are stacked into the same LF→HF GP as the global ECs. That
widens the GP input dimension, so the SGPR inducing set must be drawn from
training rows (and floored via ``lsg.min_inducing_points``); a per-column
linspace diagonal collapses under H-LSG when ``n_train`` is small (LSG-Max).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from lsg import eof


def normalize_zoning(raw: Any) -> str:
    method = str(raw or "none").lower().strip()
    if method in {"", "none", "off", "global", "deferred", "false", "0"}:
        return "none"
    aliases = {
        "residual": "residual_kmeans",
        "error": "residual_kmeans",
        "error_kmeans": "residual_kmeans",
        "correlation": "wet_correlation",
        "wet_corr": "wet_correlation",
    }
    return aliases.get(method, method)


def _kmeans(
    x: np.ndarray,
    n_clusters: int,
    rng: np.random.Generator,
    n_iter: int = 40,
) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    k = max(1, min(int(n_clusters), n))
    if k == 1:
        return np.zeros(n, dtype=np.int32)
    idx = rng.choice(n, size=k, replace=False)
    centers = x[idx].copy()
    labels = np.zeros(n, dtype=np.int32)
    for _ in range(n_iter):
        dist = ((x[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        new_labels = np.argmin(dist, axis=1).astype(np.int32)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for j in range(k):
            mask = labels == j
            if np.any(mask):
                centers[j] = x[mask].mean(axis=0)
            else:
                centers[j] = x[int(rng.integers(n))]
    _, labels = np.unique(labels, return_inverse=True)
    return labels.astype(np.int32)


def _standardize_cols(feat: np.ndarray) -> np.ndarray:
    feat = np.asarray(feat, dtype=np.float64)
    mu = feat.mean(axis=0)
    sd = feat.std(axis=0)
    sd[sd < 1e-12] = 1.0
    return (feat - mu) / sd


def cluster_residual_kmeans(
    residual: np.ndarray,
    n_zones: int,
    xy: np.ndarray | None = None,
    seed: int = 0,
) -> np.ndarray:
    """Cluster wet cells by residual/error signature (optional coordinates)."""
    resid = np.asarray(residual, dtype=np.float64)
    rms = np.sqrt(np.mean(resid * resid, axis=0))
    feat = np.column_stack(
        [
            rms,
            resid.mean(axis=0),
            np.quantile(np.abs(resid), 0.9, axis=0),
        ]
    )
    if xy is not None:
        xy_n = _standardize_cols(np.asarray(xy, dtype=np.float64).reshape(-1, 2))
        feat = np.hstack([feat, xy_n])
    feat = _standardize_cols(feat)
    return _kmeans(feat, n_zones, np.random.default_rng(seed))


def cluster_wet_correlation(
    residual: np.ndarray,
    n_zones: int,
    seed: int = 0,
) -> np.ndarray:
    """Cluster cells with similar (standardised) residual hydrographs.

    Euclidean k-means on per-cell z-scored series is a cheap proxy for
    correlation clustering and stays numpy-only.
    """
    series = np.asarray(residual, dtype=np.float64).T
    mu = series.mean(axis=1, keepdims=True)
    sd = series.std(axis=1, keepdims=True)
    sd[sd < 1e-12] = 1.0
    feat = (series - mu) / sd
    return _kmeans(feat, n_zones, np.random.default_rng(seed))


def build_zones(
    residual: np.ndarray,
    method: str,
    n_zones: int,
    xy: np.ndarray | None = None,
    seed: int = 0,
) -> np.ndarray:
    method = normalize_zoning(method)
    if method == "none":
        return np.zeros(np.asarray(residual).shape[1], dtype=np.int32)
    if method == "residual_kmeans":
        return cluster_residual_kmeans(residual, n_zones, xy=xy, seed=seed)
    if method == "wet_correlation":
        return cluster_wet_correlation(residual, n_zones, seed=seed)
    raise ValueError(
        f"Unknown zoning method {method!r}. Use none, residual_kmeans, or wet_correlation."
    )


@dataclass
class HierarchicalEOF:
    zone_ids: np.ndarray
    residual_modes: list[np.ndarray]
    residual_mean: list[np.ndarray]

    @property
    def n_zones(self) -> int:
        return len(self.residual_modes)

    @property
    def residual_n_modes(self) -> list[int]:
        return [int(m.shape[0]) for m in self.residual_modes]


def fit_residual_eofs(
    residual: np.ndarray,
    zone_ids: np.ndarray,
    weights: np.ndarray | None,
    n_modes: int,
) -> HierarchicalEOF:
    """Fit per-zone EOFs on the *global residual*, not the raw water surface."""
    labels = np.asarray(zone_ids, dtype=np.int32).reshape(-1)
    _, labels = np.unique(labels, return_inverse=True)
    labels = labels.astype(np.int32)
    resid = np.asarray(residual, dtype=np.float64)
    w_all = None if weights is None else np.asarray(weights, dtype=np.float64).reshape(-1)
    modes_list: list[np.ndarray] = []
    mean_list: list[np.ndarray] = []
    n_zones = int(labels.max()) + 1 if labels.size else 0
    for z in range(n_zones):
        mask = labels == z
        n_z = int(mask.sum())
        data_z = resid[:, mask]
        w_z = None if w_all is None else w_all[mask]
        k = min(int(n_modes), data_z.shape[0], n_z)
        if k < 1 or n_z < 1:
            modes_list.append(np.zeros((0, n_z), dtype=np.float64))
            mean_list.append(np.zeros(n_z, dtype=np.float64))
            continue
        pca, mean_z = eof.fit_eof(data_z, weights=w_z, n_components=k)
        k_use = min(k, pca.n_components_)
        modes_list.append(np.asarray(pca.components_[:k_use], dtype=np.float64))
        mean_list.append(np.asarray(mean_z, dtype=np.float64))
    return HierarchicalEOF(
        zone_ids=labels, residual_modes=modes_list, residual_mean=mean_list
    )


def project_hierarchical(
    data: np.ndarray,
    global_modes: np.ndarray,
    global_mean: np.ndarray,
    weights: np.ndarray | None,
    hier: HierarchicalEOF,
) -> tuple[np.ndarray, list[np.ndarray]]:
    ecs_g = eof.project_pseudo_ecs(data, global_modes, weights, global_mean)
    recon_g = eof.reconstruct_from_ecs(ecs_g, global_modes, global_mean, weights)
    resid = np.asarray(data, dtype=np.float64) - recon_g
    w_all = None if weights is None else np.asarray(weights, dtype=np.float64).reshape(-1)
    ecs_z: list[np.ndarray] = []
    for z in range(hier.n_zones):
        mask = hier.zone_ids == z
        w_z = None if w_all is None else w_all[mask]
        ecs_z.append(
            eof.project_pseudo_ecs(
                resid[:, mask],
                hier.residual_modes[z],
                w_z,
                hier.residual_mean[z],
            )
        )
    return ecs_g, ecs_z


def reconstruct_hierarchical(
    ecs_global: np.ndarray,
    global_modes: np.ndarray,
    global_mean: np.ndarray,
    weights: np.ndarray | None,
    ecs_residual: list[np.ndarray],
    hier: HierarchicalEOF,
) -> np.ndarray:
    h = eof.reconstruct_from_ecs(ecs_global, global_modes, global_mean, weights)
    w_all = None if weights is None else np.asarray(weights, dtype=np.float64).reshape(-1)
    for z, ecs_z in enumerate(ecs_residual):
        mask = hier.zone_ids == z
        if not np.any(mask):
            continue
        w_z = None if w_all is None else w_all[mask]
        add = eof.reconstruct_from_ecs(
            ecs_z, hier.residual_modes[z], hier.residual_mean[z], w_z
        )
        h[:, mask] = h[:, mask] + add
    return h


def reconstruct_hierarchical_variance(
    var_global: np.ndarray,
    global_modes: np.ndarray,
    var_residual: list[np.ndarray],
    weights: np.ndarray | None,
    hier: HierarchicalEOF,
    residual_var: np.ndarray | None = None,
) -> np.ndarray:
    v = eof.reconstruct_variance(var_global, global_modes, weights, residual_var=None)
    w_all = None if weights is None else np.asarray(weights, dtype=np.float64).reshape(-1)
    for z, var_z in enumerate(var_residual):
        mask = hier.zone_ids == z
        if not np.any(mask) or var_z.size == 0:
            continue
        w_z = None if w_all is None else w_all[mask]
        v[:, mask] = v[:, mask] + eof.reconstruct_variance(
            var_z, hier.residual_modes[z], w_z, residual_var=None
        )
    if residual_var is not None:
        v = v + np.asarray(residual_var, dtype=np.float64).reshape(1, -1)
    return np.maximum(v, 0.0)


def stack_ecs(ecs_global: np.ndarray, ecs_residual: list[np.ndarray]) -> np.ndarray:
    parts = [np.asarray(ecs_global, dtype=np.float64)]
    parts.extend(np.asarray(z, dtype=np.float64) for z in ecs_residual)
    return np.hstack(parts)


def unstack_ecs(
    ecs: np.ndarray,
    n_global: int,
    n_per_zone: list[int],
) -> tuple[np.ndarray, list[np.ndarray]]:
    ecs = np.asarray(ecs, dtype=np.float64)
    ecs_g = ecs[:, :n_global]
    ecs_z: list[np.ndarray] = []
    i = n_global
    for k in n_per_zone:
        ecs_z.append(ecs[:, i : i + k])
        i += k
    return ecs_g, ecs_z


def hier_from_state(state: Any) -> HierarchicalEOF | None:
    modes = getattr(state, "residual_eof_modes", None) or []
    if not modes:
        return None
    zone_ids = getattr(state, "zone_ids", None)
    means = getattr(state, "residual_eof_mean", None) or []
    if zone_ids is None:
        return None
    if len(means) != len(modes):
        means = [np.zeros(m.shape[1], dtype=np.float64) for m in modes]
    return HierarchicalEOF(
        zone_ids=np.asarray(zone_ids, dtype=np.int32),
        residual_modes=list(modes),
        residual_mean=list(means),
    )
