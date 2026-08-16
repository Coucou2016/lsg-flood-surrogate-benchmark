"""Gaussian Process emulators for EC conversion (GPflow SGPR or NumPy RBF)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
import os

import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

try:
    import gpflow

    _HAS_GPFLOW = True
except ImportError:
    gpflow = None
    _HAS_GPFLOW = False


def gpflow_available() -> bool:
    return _HAS_GPFLOW


@dataclass
class SparseGPMode:
    model: object
    scaler_x: object
    scaler_y: object
    kind: str = "rbf"


class _NumpyStandardScaler:
    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.scale_: np.ndarray | None = None

    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x.reshape(-1, 1)
        self.mean_ = x.mean(axis=0)
        self.scale_ = x.std(axis=0)
        self.scale_[self.scale_ < 1e-12] = 1.0
        return (x - self.mean_) / self.scale_

    def transform(self, x: np.ndarray) -> np.ndarray:
        assert self.mean_ is not None and self.scale_ is not None
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x.reshape(-1, 1)
        return (x - self.mean_) / self.scale_

    def inverse_transform(self, y: np.ndarray) -> np.ndarray:
        assert self.scale_ is not None and self.mean_ is not None
        y = np.asarray(y, dtype=np.float64)
        if y.ndim == 1:
            return y * self.scale_[0] + self.mean_[0]
        return y * self.scale_ + self.mean_


def _make_scaler() -> _NumpyStandardScaler:
    return _NumpyStandardScaler()


def _as_1d(arr: np.ndarray) -> np.ndarray:
    return np.atleast_1d(np.asarray(arr, dtype=np.float64)).reshape(-1)


def _scaler_from_arrays(mean: np.ndarray, scale: np.ndarray) -> _NumpyStandardScaler:
    scaler = _NumpyStandardScaler()
    scaler.mean_ = _as_1d(mean)
    scaler.scale_ = _as_1d(scale)
    scaler.scale_[scaler.scale_ < 1e-12] = 1.0
    return scaler


def _tf_to_numpy(value: Any) -> np.ndarray:
    if hasattr(value, "numpy"):
        value = value.numpy()
    return np.asarray(value)


MIN_INDUCING_POINTS = 16


def inducing_budget(
    n_samples: int,
    inducing_fraction: float = 0.02,
    min_inducing: int = MIN_INDUCING_POINTS,
) -> int:
    """How many inducing points an SGPR should use for ``n_samples`` rows.

    Fraehr's fraction rule is tuned for the LSG-TS regime (thousands of
    timestep rows). LSG-Max trains on one row per event, so a bare fraction
    collapses to 2 points and the sparse approximation becomes the dominant
    error. Sparsity is only needed when ``n_samples`` is large, so the budget
    is floored and then capped at ``n_samples`` — at the cap SGPR with
    ``Z = X`` is an exact GP.
    """
    n = max(1, int(n_samples))
    m = max(2, round(n * float(inducing_fraction)))
    m = max(m, min(n, int(min_inducing)))
    return int(min(m, n))


def min_inducing_from_cfg(cfg: dict[str, Any]) -> int:
    """``lsg.min_inducing_points`` (floor on the SGPR inducing budget)."""
    return int(
        (cfg.get("lsg") or {}).get("min_inducing_points", MIN_INDUCING_POINTS)
    )


def _inducing_points(x_sc: np.ndarray, n_inducing: int) -> np.ndarray:
    """Inducing locations drawn from the (standardised) training inputs.

    One point per EC dimension placed on a ``linspace`` *per column* traces a
    single diagonal line through the input box: with d > 1 EC inputs that line
    holds almost no training rows, so the SGPR posterior cannot represent even
    a near-linear LF→HF mapping (H-LSG stacks global + residual ECs, so d grows
    from 1 to 13 for an 8-event LSG-Max fit). Subsampling the training rows
    themselves is the standard SGPR initialisation and stays deterministic.
    """
    x_sc = np.asarray(x_sc, dtype=np.float64)
    n = x_sc.shape[0]
    m = max(1, min(int(n_inducing), n))
    if m >= n:
        return x_sc.copy()
    idx = np.unique(np.linspace(0, n - 1, m).round().astype(int))
    return x_sc[idx].copy()


def train_sparse_gp_mode_gpflow(
    x_train: np.ndarray,
    y_train: np.ndarray,
    inducing_fraction: float = 0.02,
    min_inducing: int = MIN_INDUCING_POINTS,
) -> SparseGPMode:
    if not _HAS_GPFLOW:
        raise ImportError("gpflow is not installed")
    n_inducing = inducing_budget(
        len(x_train), inducing_fraction, min_inducing=min_inducing
    )
    scaler_x = _make_scaler()
    scaler_y = _make_scaler()
    x_sc = scaler_x.fit_transform(x_train)
    y_sc = scaler_y.fit_transform(y_train.reshape(-1, 1))

    z = _inducing_points(x_sc, n_inducing)
    ini_length = float(np.mean(np.abs(x_sc)))
    kernel = gpflow.kernels.Exponential(variance=1.0, lengthscales=ini_length)
    model = gpflow.models.SGPR(
        data=(x_sc, y_sc),
        kernel=kernel,
        inducing_variable=z,
    )
    opt = gpflow.optimizers.Scipy()
    for trainable in (
        model.kernel.variance,
        model.kernel.lengthscales,
        model.likelihood.variance,
    ):
        gpflow.set_trainable(trainable, False)
    opt.minimize(
        model.training_loss,
        model.trainable_variables,
        method="L-BFGS-B",
        options=dict(maxiter=100),
    )
    for trainable in (
        model.kernel.variance,
        model.kernel.lengthscales,
        model.likelihood.variance,
    ):
        gpflow.set_trainable(trainable, True)
    gpflow.set_trainable(model.inducing_variable.Z, False)
    opt.minimize(
        model.training_loss,
        model.trainable_variables,
        method="L-BFGS-B",
        options=dict(maxiter=100),
    )
    return SparseGPMode(
        model=model, scaler_x=scaler_x, scaler_y=scaler_y, kind="sgpr"
    )


class _RBFKernelGP:
    """Lightweight RBF GP fallback (no GPflow)."""

    def __init__(self, length_scale: float = 1.0, noise: float = 0.05) -> None:
        self.length_scale = length_scale
        self.noise = noise
        self.x_train: np.ndarray | None = None
        self.y_train: np.ndarray | None = None
        self._alpha: np.ndarray | None = None
        self._L: np.ndarray | None = None

    def _kernel(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        dist = np.sum((a[:, None, :] - b[None, :, :]) ** 2, axis=2)
        return np.exp(-0.5 * dist / (self.length_scale**2))

    def _refresh_cholesky(self) -> None:
        assert self.x_train is not None
        n = len(self.x_train)
        k = self._kernel(self.x_train, self.x_train)
        jitter = float(self.noise)
        eye = np.eye(n)
        for _ in range(8):
            try:
                self._L = np.linalg.cholesky(k + jitter * eye)
                return
            except np.linalg.LinAlgError:
                jitter = jitter * 10.0 if jitter > 0 else 1e-8
        self._L = np.linalg.cholesky(k + (jitter + 1e-6) * eye)

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        self.x_train = np.asarray(x, dtype=np.float64)
        self.y_train = np.asarray(y, dtype=np.float64).ravel()
        self._refresh_cholesky()
        assert self._L is not None
        self._alpha = np.linalg.solve(
            self._L.T, np.linalg.solve(self._L, self.y_train)
        )

    def predict(self, x: np.ndarray) -> np.ndarray:
        mean, _ = self.predict_f(x)
        return mean

    def predict_f(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Latent posterior mean and variance (GPflow ``predict_f`` analogue)."""
        assert self.x_train is not None and self._alpha is not None
        if self._L is None:
            self._refresh_cholesky()
        assert self._L is not None
        x = np.asarray(x, dtype=np.float64)
        k_star = self._kernel(x, self.x_train)
        mean = k_star @ self._alpha
        v = np.linalg.solve(self._L, k_star.T)
        var = np.ones(x.shape[0], dtype=np.float64) - np.sum(v * v, axis=0)
        return mean.ravel(), np.maximum(var, 0.0)


def train_sparse_gp_mode_numpy(
    x_train: np.ndarray,
    y_train: np.ndarray,
) -> _RBFKernelGP:
    model = _RBFKernelGP()
    model.fit(x_train, y_train.ravel())
    return model


def _restore_sgpr(
    x_data: np.ndarray,
    y_data: np.ndarray,
    inducing_z: np.ndarray,
    kernel_variance: float,
    kernel_lengthscales: np.ndarray,
    likelihood_variance: float,
) -> Any:
    if not _HAS_GPFLOW:
        raise ImportError(
            "Saved GPflow SGPR weights require gpflow. "
            "Install optional extras or retrain with the NumPy fallback."
        )
    x_data = np.asarray(x_data, dtype=np.float64)
    y_data = np.asarray(y_data, dtype=np.float64)
    if y_data.ndim == 1:
        y_data = y_data.reshape(-1, 1)
    inducing_z = np.asarray(inducing_z, dtype=np.float64)
    ls = np.asarray(kernel_lengthscales, dtype=np.float64)
    lengthscales = float(ls.reshape(-1)[0]) if ls.size <= 1 else ls
    kernel = gpflow.kernels.Exponential(
        variance=float(kernel_variance),
        lengthscales=lengthscales,
    )
    model = gpflow.models.SGPR(
        data=(x_data, y_data),
        kernel=kernel,
        inducing_variable=inducing_z,
    )
    model.likelihood.variance.assign(float(likelihood_variance))
    gpflow.set_trainable(model.inducing_variable.Z, False)
    return model


def inverse_transform_gp_moments(
    scaler_y: Any,
    mean_sc: np.ndarray,
    var_sc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Map scaled GP mean/variance back to EC units.

    StandardScaler is affine: ``y = y_sc * scale + mean``, so
    ``Var(y) = Var(y_sc) * scale**2`` (never add ``mean`` into the variance).
    """
    mean_sc = np.asarray(mean_sc, dtype=np.float64).reshape(-1, 1)
    var_sc = np.asarray(var_sc, dtype=np.float64).reshape(-1)
    mean = np.asarray(scaler_y.inverse_transform(mean_sc), dtype=np.float64).ravel()
    scale = np.asarray(scaler_y.scale_, dtype=np.float64).reshape(-1)
    var = var_sc * float(scale[0] ** 2)
    return mean, np.maximum(var, 0.0)


def predict_sparse_gp_mode(
    mode: SparseGPMode,
    x: np.ndarray,
    return_var: bool = False,
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    x_sc = mode.scaler_x.transform(x)
    if isinstance(mode.model, _RBFKernelGP) or mode.kind == "rbf":
        mean_sc, var_sc = mode.model.predict_f(x_sc)
    else:
        mean_t, var_t = mode.model.predict_f(x_sc)
        mean_sc = _tf_to_numpy(mean_t)
        var_sc = _tf_to_numpy(var_t)
    mean, var = inverse_transform_gp_moments(mode.scaler_y, mean_sc, var_sc)
    if return_var:
        return mean, var
    return mean


def train_ec_emulator(
    lf_ecs: np.ndarray,
    hf_ecs: np.ndarray,
    inducing_fraction: float = 0.02,
    min_inducing: int = MIN_INDUCING_POINTS,
) -> list:
    modes = []
    x = lf_ecs
    for i in range(hf_ecs.shape[1]):
        y = hf_ecs[:, i]
        if _HAS_GPFLOW:
            sm = train_sparse_gp_mode_gpflow(
                x,
                y,
                inducing_fraction=inducing_fraction,
                min_inducing=min_inducing,
            )
        else:
            scaler_x = _make_scaler()
            scaler_y = _make_scaler()
            x_sc = scaler_x.fit_transform(x)
            y_sc = scaler_y.fit_transform(y.reshape(-1, 1))
            gpr = train_sparse_gp_mode_numpy(x_sc, y_sc)
            sm = SparseGPMode(
                model=gpr, scaler_x=scaler_x, scaler_y=scaler_y, kind="rbf"
            )
        modes.append(sm)
    return modes


def predict_ec_emulator(
    modes: Sequence,
    lf_ecs: np.ndarray,
    return_var: bool = False,
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """Predict HF ECs. ``return_var=True`` yields ``(mean, var)`` each ``(n, k)``.

    Default stays mean-only so existing callers keep working.
    """
    means: list[np.ndarray] = []
    vars_: list[np.ndarray] = []
    for mode in modes:
        mu, va = predict_sparse_gp_mode(mode, lf_ecs, return_var=True)
        means.append(np.asarray(mu, dtype=np.float64).ravel())
        vars_.append(np.asarray(va, dtype=np.float64).ravel())
    mean = np.column_stack(means) if means else np.zeros((len(lf_ecs), 0))
    var = np.column_stack(vars_) if vars_ else np.zeros((len(lf_ecs), 0))
    if return_var:
        return mean, var
    return mean


def sklearn_fallback_train(lf_ecs: np.ndarray, hf_ecs: np.ndarray) -> list:
    return train_ec_emulator(lf_ecs, hf_ecs, inducing_fraction=0.1)


def sklearn_fallback_predict(models: list, lf_ecs: np.ndarray) -> np.ndarray:
    return predict_ec_emulator(models, lf_ecs, return_var=False)


def dump_gp_modes(modes: Sequence[SparseGPMode]) -> dict[str, np.ndarray]:
    """Serialize GP weights/scalers as NPZ-friendly arrays (no pickle)."""
    payload: dict[str, np.ndarray] = {
        "gp_n_modes": np.array(len(modes), dtype=np.int32),
        "gp_backend": np.array("gpflow" if _HAS_GPFLOW else "numpy"),
    }
    for i, mode in enumerate(modes):
        p = f"gp_{i}_"
        kind = mode.kind
        if isinstance(mode.model, _RBFKernelGP):
            kind = "rbf"
        payload[p + "kind"] = np.array(kind)
        payload[p + "sx_mean"] = np.asarray(mode.scaler_x.mean_, dtype=np.float64)
        payload[p + "sx_scale"] = np.asarray(mode.scaler_x.scale_, dtype=np.float64)
        payload[p + "sy_mean"] = np.asarray(mode.scaler_y.mean_, dtype=np.float64)
        payload[p + "sy_scale"] = np.asarray(mode.scaler_y.scale_, dtype=np.float64)
        if kind == "rbf":
            model: _RBFKernelGP = mode.model
            if model.x_train is None or model._alpha is None:
                raise RuntimeError("Cannot serialize an unfitted NumPy GP.")
            payload[p + "x_train"] = np.asarray(model.x_train, dtype=np.float64)
            payload[p + "alpha"] = np.asarray(model._alpha, dtype=np.float64)
            payload[p + "length_scale"] = np.array(model.length_scale, dtype=np.float64)
            payload[p + "noise"] = np.array(model.noise, dtype=np.float64)
        else:
            model = mode.model
            x_data, y_data = model.data
            payload[p + "x_data"] = _tf_to_numpy(x_data).astype(np.float64)
            payload[p + "y_data"] = _tf_to_numpy(y_data).astype(np.float64)
            payload[p + "Z"] = _tf_to_numpy(model.inducing_variable.Z).astype(np.float64)
            payload[p + "k_var"] = np.array(
                float(_tf_to_numpy(model.kernel.variance)), dtype=np.float64
            )
            payload[p + "k_ls"] = _tf_to_numpy(model.kernel.lengthscales).astype(
                np.float64
            )
            payload[p + "lik_var"] = np.array(
                float(_tf_to_numpy(model.likelihood.variance)), dtype=np.float64
            )
    return payload


def load_gp_modes(raw: Any) -> list[SparseGPMode]:
    """Restore GP emulators saved by dump_gp_modes."""
    files = set(raw.files) if hasattr(raw, "files") else set(raw.keys())
    if "gp_n_modes" not in files:
        return []
    n = int(np.asarray(raw["gp_n_modes"]).reshape(-1)[0])
    modes: list[SparseGPMode] = []
    for i in range(n):
        p = f"gp_{i}_"
        scaler_x = _scaler_from_arrays(raw[p + "sx_mean"], raw[p + "sx_scale"])
        scaler_y = _scaler_from_arrays(raw[p + "sy_mean"], raw[p + "sy_scale"])
        kind = str(np.asarray(raw[p + "kind"]))
        if kind == "rbf":
            model = _RBFKernelGP(
                length_scale=float(np.asarray(raw[p + "length_scale"])),
                noise=float(np.asarray(raw[p + "noise"])),
            )
            model.x_train = np.asarray(raw[p + "x_train"], dtype=np.float64)
            model._alpha = np.asarray(raw[p + "alpha"], dtype=np.float64)
            model._refresh_cholesky()
        elif kind == "sgpr":
            model = _restore_sgpr(
                raw[p + "x_data"],
                raw[p + "y_data"],
                raw[p + "Z"],
                float(np.asarray(raw[p + "k_var"])),
                np.asarray(raw[p + "k_ls"]),
                float(np.asarray(raw[p + "lik_var"])),
            )
        else:
            raise ValueError(f"Unknown GP kind {kind!r} in saved state")
        modes.append(
            SparseGPMode(
                model=model, scaler_x=scaler_x, scaler_y=scaler_y, kind=kind
            )
        )
    return modes
