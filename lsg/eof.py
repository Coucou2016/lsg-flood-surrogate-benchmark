"""EOF (PCA) analysis following Fraehr et al. (2022, 2023) LSG methodology."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class EOFResult:
    components_: np.ndarray  # (n_modes, n_cells)
    explained_variance_: np.ndarray
    explained_variance_ratio_: np.ndarray
    n_components_: int
    singular_values_: np.ndarray


def temporal_mean(data: np.ndarray) -> np.ndarray:
    """Mean along time/event axis (axis 0)."""
    return np.mean(data, axis=0)


def center_data(data: np.ndarray, mean: np.ndarray | None = None) -> np.ndarray:
    mean = temporal_mean(data) if mean is None else mean
    return data - mean


def apply_weights(data: np.ndarray, weights: np.ndarray) -> np.ndarray:
    w = np.asarray(weights, dtype=np.float64).reshape(1, -1)
    return data * w


def fit_eof(
    data: np.ndarray,
    weights: np.ndarray | None = None,
    n_components: int = 100,
    hf_mean: np.ndarray | None = None,
) -> tuple[EOFResult, np.ndarray]:
    """
    Fit EOF spatial modes on detrended (and optionally weighted) data via SVD.

    data : (n_samples, n_cells)
    """
    mean = temporal_mean(data) if hf_mean is None else hf_mean
    centered = center_data(data, mean).astype(np.float64)
    if weights is not None:
        centered = apply_weights(centered, weights)

    n_samples, n_cells = centered.shape
    k = min(n_components, n_samples, n_cells)
    # Economy SVD: rows are time samples
    u, s, vt = np.linalg.svd(centered, full_matrices=False)
    k = min(k, len(s))
    components = vt[:k]
    var = (s[:k] ** 2) / max(n_samples - 1, 1)
    total = var.sum() if var.sum() > 0 else 1.0
    result = EOFResult(
        components_=components,
        explained_variance_=var,
        explained_variance_ratio_=var / total,
        n_components_=k,
        singular_values_=s[:k],
    )
    return result, mean


def project_pseudo_ecs(
    data: np.ndarray,
    eof_modes: np.ndarray,
    weights: np.ndarray | None = None,
    hf_mean: np.ndarray | None = None,
) -> np.ndarray:
    mean = temporal_mean(data) if hf_mean is None else hf_mean
    centered = center_data(data, mean)
    if weights is not None:
        centered = apply_weights(centered, weights)
    return centered @ eof_modes.T


def reconstruct_from_ecs(
    ecs: np.ndarray,
    eof_modes: np.ndarray,
    mean: np.ndarray,
    weights: np.ndarray | None = None,
) -> np.ndarray:
    recon = ecs @ eof_modes
    if weights is not None:
        w = np.asarray(weights, dtype=np.float64).reshape(1, -1)
        recon = recon / w
    return recon + mean


def reconstruct_variance(
    ecs_var: np.ndarray,
    eof_modes: np.ndarray,
    weights: np.ndarray | None = None,
    residual_var: np.ndarray | None = None,
) -> np.ndarray:
    """Cell-wise variance of a linear EOF reconstruction.

    Independent mode GPs give a closed form. With
    ``h_i = hbar_i + (1/w_i) * sum_k c_k * phi_ki``::

        Var(h_i) = sum_k sigma_k^2 * phi_ki^2 / w_i^2  [+ residual_var_i]

    ``residual_var`` is a per-cell truncation / leftover-EOF term. GP variance
    on the retained modes alone is overconfident because discarded modes and
    representation error are not in the emulator.
    """
    ecs_var = np.asarray(ecs_var, dtype=np.float64)
    phi2 = np.asarray(eof_modes, dtype=np.float64) ** 2
    var = ecs_var @ phi2
    if weights is not None:
        w = np.asarray(weights, dtype=np.float64).reshape(1, -1)
        var = var / (w * w)
    if residual_var is not None:
        var = var + np.asarray(residual_var, dtype=np.float64).reshape(1, -1)
    return np.maximum(var, 0.0)


def estimate_residual_variance(
    data: np.ndarray,
    eof_modes: np.ndarray,
    mean: np.ndarray,
    weights: np.ndarray | None = None,
) -> np.ndarray:
    """Per-cell mean squared leftover after a k-mode reconstruction."""
    ecs = project_pseudo_ecs(data, eof_modes, weights, mean)
    recon = reconstruct_from_ecs(ecs, eof_modes, mean, weights)
    resid = np.asarray(data, dtype=np.float64) - recon
    return np.mean(resid * resid, axis=0)


def norths_rule(pca: EOFResult, n_samples: int) -> int:
    eigenvalues = pca.explained_variance_
    d_eigen = np.abs(np.diff(eigenvalues))
    d_error = np.sqrt(2.0 / n_samples) * eigenvalues[:-1]
    boundary = np.where(d_eigen <= d_error)[0]
    if len(boundary) == 0:
        return len(eigenvalues)
    return int(boundary[0])


def kaiser_significant(pca: EOFResult) -> int:
    return int(np.sum(pca.explained_variance_ > 1.0))


def select_n_modes(pca: EOFResult, n_samples: int) -> int:
    n_north = norths_rule(pca, n_samples)
    n_kaiser = kaiser_significant(pca)
    return max(1, min(n_north, n_kaiser, pca.n_components_))
