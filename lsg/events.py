"""Multi-fidelity flood event library protocol.

Each independent HEC-RAS case uses a scaled/shifted copy of a base hydrograph:

    Q_i(t) = a_i * Q_0((t - tau_i) / s_i)

with Latin Hypercube Sampling over

    a in [0.6, 1.6],  s in [0.8, 1.2],  tau in [-3 h, +3 h].

The 40-event design is 24 train / 6 val / 10 test, where the test set holds
6 interpolation events plus 4 extrapolation events at the peak/duration ends.

This module writes parameters and hydrograph CSVs only. It does not invent
inundation rasters.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import yaml

DEFAULT_A_RANGE = (0.6, 1.6)
DEFAULT_S_RANGE = (0.8, 1.2)
DEFAULT_TAU_HOURS_RANGE = (-3.0, 3.0)
DEFAULT_N_EVENTS = 40
DEFAULT_N_TRAIN = 24
DEFAULT_N_VAL = 6
DEFAULT_N_TEST = 10
DEFAULT_N_TEST_EXTRAP = 4
DEFAULT_SEED = 20260814

INTERP_A_RANGE = (0.80, 1.40)
INTERP_S_RANGE = (0.90, 1.10)


def latin_hypercube(n: int, d: int, seed: int) -> np.ndarray:
    """Simple Latin Hypercube in the unit cube. Shape ``(n, d)``."""
    rng = np.random.default_rng(seed)
    cut = np.linspace(0.0, 1.0, n + 1)
    u = rng.random((n, d))
    samples = np.empty((n, d), dtype=np.float64)
    for j in range(d):
        perm = rng.permutation(n)
        samples[:, j] = cut[perm] + u[:, j] * (cut[1] - cut[0])
    return samples


def _scale(unit: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return lo + unit * (hi - lo)


def _in_range(value: float, bounds: tuple[float, float]) -> bool:
    return bounds[0] <= value <= bounds[1]


@dataclass
class EventSpec:
    event_id: str
    a: float
    s: float
    tau_hours: float
    split: str
    test_kind: str = ""
    drives: tuple[str, ...] = ()
    tributary_eps: dict[str, float] = field(default_factory=dict)

    @property
    def is_interpolation(self) -> bool:
        return _in_range(self.a, INTERP_A_RANGE) and _in_range(self.s, INTERP_S_RANGE)

    def to_row(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "event_id": self.event_id,
            "a": f"{self.a:.6f}",
            "s": f"{self.s:.6f}",
            "tau_hours": f"{self.tau_hours:.6f}",
            "split": self.split,
            "test_kind": self.test_kind,
            "interpolation_box": str(self.is_interpolation).lower(),
            "drives": ";".join(self.drives),
        }
        for name, eps in sorted(self.tributary_eps.items()):
            row[f"eps_{name}"] = f"{eps:.6f}"
            row[f"a_{name}"] = f"{self.a * (1.0 + eps):.6f}"
        return row


def assign_splits(
    specs: list[EventSpec],
    n_train: int = DEFAULT_N_TRAIN,
    n_val: int = DEFAULT_N_VAL,
    n_test: int = DEFAULT_N_TEST,
    n_test_extrap: int = DEFAULT_N_TEST_EXTRAP,
    seed: int = DEFAULT_SEED,
) -> list[EventSpec]:
    """
    Label events train/val/test.

    Extrapolation test events are chosen from samples outside the inner
    (a, s) box, preferring extremes of peak scale ``a`` and duration ``s``.
    Remaining test slots are interpolation events.
    """
    n = len(specs)
    if n_train + n_val + n_test != n:
        raise ValueError(
            f"split counts {n_train}+{n_val}+{n_test} != n_events {n}"
        )
    rng = np.random.default_rng(seed + 17)

    extrap_idx = [i for i, e in enumerate(specs) if not e.is_interpolation]
    interp_idx = [i for i, e in enumerate(specs) if e.is_interpolation]
    if len(extrap_idx) < n_test_extrap:
        raise ValueError(
            f"Need {n_test_extrap} extrapolation events, only {len(extrap_idx)} "
            "fell outside the interpolation box. Increase n_events or widen LHS."
        )
    n_test_extrap = min(int(n_test_extrap), int(n_test))
    n_test_interp = int(n_test) - n_test_extrap
    if n_test_interp < 0:
        raise ValueError("n_test_extrap cannot exceed n_test")
    if len(interp_idx) < n_test_interp:
        raise ValueError(
            f"Need {n_test_interp} interpolation test events, only "
            f"{len(interp_idx)} fell inside the interpolation box."
        )

    def _extrap_score(i: int) -> float:
        e = specs[i]
        a_lo, a_hi = DEFAULT_A_RANGE
        s_lo, s_hi = DEFAULT_S_RANGE
        a_edge = min(abs(e.a - a_lo), abs(e.a - a_hi)) / (a_hi - a_lo)
        s_edge = min(abs(e.s - s_lo), abs(e.s - s_hi)) / (s_hi - s_lo)
        return float(min(a_edge, s_edge))

    extrap_ranked = sorted(extrap_idx, key=_extrap_score)
    # Small score => closer to the range edge.
    test_extrap = extrap_ranked[:n_test_extrap]
    # Alternate peak-high / peak-low / duration-high / duration-low when possible.
    by_a = sorted(extrap_idx, key=lambda i: specs[i].a)
    by_s = sorted(extrap_idx, key=lambda i: specs[i].s)
    preferred = [by_a[-1], by_a[0], by_s[-1], by_s[0]]
    test_extrap = []
    for i in preferred:
        if i not in test_extrap:
            test_extrap.append(i)
        if len(test_extrap) >= n_test_extrap:
            break
    for i in extrap_ranked:
        if len(test_extrap) >= n_test_extrap:
            break
        if i not in test_extrap:
            test_extrap.append(i)
    test_extrap = test_extrap[:n_test_extrap]

    remaining_interp = [i for i in interp_idx if i not in test_extrap]
    rng.shuffle(remaining_interp)
    test_interp = remaining_interp[:n_test_interp]
    used = set(test_extrap) | set(test_interp)
    leftover = [i for i in range(len(specs)) if i not in used]
    rng.shuffle(leftover)
    # Val may mix interpolation and extrapolation; only the test set is typed.
    val_idx = leftover[:n_val]
    train_idx = leftover[n_val:]
    if len(train_idx) != n_train:
        raise ValueError(
            f"Internal split error: train={len(train_idx)} expected {n_train}"
        )

    for i in train_idx:
        specs[i].split = "train"
        specs[i].test_kind = ""
    for i in val_idx:
        specs[i].split = "val"
        specs[i].test_kind = ""
    for i in test_interp:
        specs[i].split = "test"
        specs[i].test_kind = "interpolation"
    kinds_extrap = ("extrap_peak_high", "extrap_peak_low", "extrap_dur_high", "extrap_dur_low")
    for k, i in enumerate(test_extrap):
        specs[i].split = "test"
        specs[i].test_kind = kinds_extrap[k] if k < len(kinds_extrap) else "extrapolation"
    return specs


def _in_interp_box(a: float, s: float) -> bool:
    return _in_range(a, INTERP_A_RANGE) and _in_range(s, INTERP_S_RANGE)


def _ensure_interp_extrap_coverage(
    a: np.ndarray,
    s: np.ndarray,
    tau: np.ndarray,
    n_test_interp: int,
    n_test_extrap: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Replace a few LHS draws with interior / corner points if needed."""
    a = np.asarray(a, dtype=np.float64).copy()
    s = np.asarray(s, dtype=np.float64).copy()
    tau = np.asarray(tau, dtype=np.float64).copy()
    interp = [i for i in range(len(a)) if _in_interp_box(float(a[i]), float(s[i]))]
    extrap = [i for i in range(len(a)) if i not in interp]
    interior = [
        (1.00, 1.00),
        (0.90, 1.00),
        (1.10, 1.00),
        (1.00, 0.95),
        (1.00, 1.05),
        (0.85, 0.95),
        (1.20, 1.05),
        (1.30, 0.92),
    ]
    corners = [
        (0.60, 0.80),
        (1.60, 1.20),
        (0.60, 1.20),
        (1.60, 0.80),
    ]
    k = 0
    while len(interp) < n_test_interp and k < len(interior):
        # Prefer converting an extrapolation sample.
        src = extrap.pop() if extrap else (len(a) - 1 - k)
        a[src], s[src] = interior[k]
        if src not in interp:
            interp.append(src)
        k += 1
    k = 0
    while len(extrap) < n_test_extrap and k < len(corners):
        src = interp.pop() if len(interp) > n_test_interp else (k)
        a[src], s[src] = corners[k]
        if src not in extrap:
            extrap.append(src)
        k += 1
    return a, s, tau


def generate_event_library(
    n_events: int = DEFAULT_N_EVENTS,
    seed: int = DEFAULT_SEED,
    a_range: tuple[float, float] = DEFAULT_A_RANGE,
    s_range: tuple[float, float] = DEFAULT_S_RANGE,
    tau_hours_range: tuple[float, float] = DEFAULT_TAU_HOURS_RANGE,
    drives: Sequence[str] = ("hf_100ft", "lf_400ft", "lf_800ft"),
    tributaries: Sequence[str] = (),
    n_train: int | None = None,
    n_val: int | None = None,
    n_test: int | None = None,
    n_test_extrap: int = DEFAULT_N_TEST_EXTRAP,
    id_prefix: str = "E",
) -> list[EventSpec]:
    """Draw an LHS event library and assign splits.

    For ``n_events != 40``, train/val/test counts scale by 24/6/10 when not
    given explicitly. A 10-event pilot uses 6/2/2 with 2 extrapolation tests.
    """
    if n_events < 4:
        raise ValueError("n_events must be >= 4")
    if n_train is None or n_val is None or n_test is None:
        if n_events == DEFAULT_N_EVENTS:
            n_train, n_val, n_test = DEFAULT_N_TRAIN, DEFAULT_N_VAL, DEFAULT_N_TEST
        elif n_events == 10:
            n_train, n_val, n_test = 6, 2, 2
            n_test_extrap = min(n_test_extrap, 2)
        else:
            n_test = max(2, int(round(n_events * 10 / 40)))
            n_val = max(1, int(round(n_events * 6 / 40)))
            n_train = n_events - n_test - n_val
            n_test_extrap = min(n_test_extrap, max(1, n_test // 2))
    n_test_extrap = min(int(n_test_extrap), int(n_test))
    unit = latin_hypercube(n_events, 3, seed)
    a = _scale(unit[:, 0], *a_range)
    s = _scale(unit[:, 1], *s_range)
    tau = _scale(unit[:, 2], *tau_hours_range)
    # Guarantee enough interpolation / extrapolation mass for the test split.
    a, s, tau = _ensure_interp_extrap_coverage(
        a, s, tau, n_test_interp=n_test - n_test_extrap, n_test_extrap=n_test_extrap
    )
    trib_eps: list[dict[str, float]] = [{} for _ in range(n_events)]
    if tributaries:
        # Independent LHS for tributary perturbations, then U(-0.15, 0.15).
        u_trib = latin_hypercube(n_events, len(tributaries), seed + 99)
        eps = _scale(u_trib, -0.15, 0.15)
        for i in range(n_events):
            trib_eps[i] = {
                name: float(eps[i, j]) for j, name in enumerate(tributaries)
            }
    specs = [
        EventSpec(
            event_id=f"{id_prefix}{i + 1:02d}",
            a=float(a[i]),
            s=float(s[i]),
            tau_hours=float(tau[i]),
            split="",
            drives=tuple(drives),
            tributary_eps=trib_eps[i],
        )
        for i in range(n_events)
    ]
    return assign_splits(
        specs,
        n_train=n_train,
        n_val=n_val,
        n_test=n_test,
        n_test_extrap=n_test_extrap,
        seed=seed,
    )


def resample_hydrograph(
    t_hours: np.ndarray,
    q: np.ndarray,
    a: float,
    s: float,
    tau_hours: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply Q_i(t) = a * Q_0((t - tau) / s) on the original time grid.

    Values that map outside the base record are 0 (no fabricated rising limb
    beyond the observed hydrograph support).
    """
    t = np.asarray(t_hours, dtype=np.float64)
    q0 = np.asarray(q, dtype=np.float64)
    order = np.argsort(t)
    t = t[order]
    q0 = q0[order]
    t_src = (t - tau_hours) / s
    qi = a * np.interp(t_src, t, q0, left=0.0, right=0.0)
    qi = np.clip(qi, 0.0, None)
    return t, qi


def load_usgs_rdb(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Parse USGS Instantaneous Values RDB (discharge, parameter 00060)."""
    path = Path(path)
    times: list[np.datetime64] = []
    values: list[float] = []
    header: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if not header:
                header = parts
                continue
            if parts and parts[0] in {"5s", "15s", "20d", "10s"}:
                continue
            if len(parts) < 5:
                continue
            try:
                dt_idx = header.index("datetime")
            except ValueError:
                dt_idx = 2
            q_idx = None
            for i, name in enumerate(header):
                if name.endswith("_00060") and not name.endswith("_cd"):
                    q_idx = i
                    break
            if q_idx is None:
                q_idx = 4 if len(parts) > 4 else 3
            raw_q = parts[q_idx].strip()
            if not raw_q:
                continue
            try:
                q = float(raw_q)
            except ValueError:
                continue
            times.append(np.datetime64(parts[dt_idx].replace(" ", "T")))
            values.append(q)
    if not times:
        raise ValueError(f"No discharge rows in {path}")
    t0 = times[0]
    hours = np.array(
        [(t - t0) / np.timedelta64(1, "h") for t in times], dtype=np.float64
    )
    return hours, np.asarray(values, dtype=np.float64)


def load_hydrograph_csv(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """CSV with columns time_hours,q (or datetime,q)."""
    path = Path(path)
    t_list: list[float] = []
    q_list: list[float] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"Empty hydrograph CSV: {path}")
        fields = [c.strip() for c in reader.fieldnames]
        lower = {c.lower(): c for c in fields}
        t_key = lower.get("time_hours") or lower.get("t_hours") or lower.get("hours")
        q_key = lower.get("q") or lower.get("discharge") or lower.get("flow")
        if q_key is None:
            raise ValueError(f"No discharge column in {path}: {fields}")
        t0 = None
        for row in reader:
            q = float(row[q_key])
            if t_key:
                t_list.append(float(row[t_key]))
            else:
                dt_key = lower.get("datetime") or lower.get("time")
                stamp = np.datetime64(row[dt_key].replace(" ", "T"))
                if t0 is None:
                    t0 = stamp
                t_list.append(float((stamp - t0) / np.timedelta64(1, "h")))
            q_list.append(q)
    return np.asarray(t_list, dtype=np.float64), np.asarray(q_list, dtype=np.float64)


def load_base_hydrograph(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".txt", ".rdb"}:
        return load_usgs_rdb(path)
    if suffix == ".csv":
        return load_hydrograph_csv(path)
    raise ValueError(f"Unsupported hydrograph file: {path}")


def write_event_table(path: str | Path, specs: Sequence[EventSpec]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [e.to_row() for e in specs]
    fieldnames: list[str] = []
    for row in rows:
        for k in row:
            if k not in fieldnames:
                fieldnames.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_hydrograph_csv(
    path: str | Path,
    t_hours: np.ndarray,
    q: np.ndarray,
    extra: dict[str, np.ndarray] | None = None,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    extra = extra or {}
    fieldnames = ["time_hours", "q"] + list(extra.keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(len(t_hours)):
            row = {"time_hours": f"{t_hours[i]:.6f}", "q": f"{q[i]:.6f}"}
            for k, arr in extra.items():
                row[k] = f"{arr[i]:.6f}"
            writer.writerow(row)


def write_event_hydrographs(
    out_dir: str | Path,
    specs: Sequence[EventSpec],
    t_hours: np.ndarray,
    q0: np.ndarray,
    tributaries: Sequence[str] = (),
    q0_by_tributary: dict[str, np.ndarray] | None = None,
) -> list[Path]:
    """Write one CSV per event. Tributary columns use a_j = a * (1+eps_j)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    q0_by_tributary = q0_by_tributary or {}
    for spec in specs:
        t, q = resample_hydrograph(t_hours, q0, spec.a, spec.s, spec.tau_hours)
        extra: dict[str, np.ndarray] = {}
        for name in tributaries:
            base = q0_by_tributary.get(name, q0)
            eps = spec.tributary_eps.get(name, 0.0)
            a_j = spec.a * (1.0 + eps)
            _, qj = resample_hydrograph(t_hours, base, a_j, spec.s, spec.tau_hours)
            extra[f"q_{name}"] = qj
        dest = out_dir / f"{spec.event_id}_hydrograph.csv"
        write_hydrograph_csv(dest, t, q, extra=extra)
        written.append(dest)
    return written


def protocol_dict(
    case_id: str,
    drives: Sequence[str],
    n_events: int = DEFAULT_N_EVENTS,
    seed: int = DEFAULT_SEED,
    tributaries: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "formula": "Q_i(t) = a_i * Q_0((t - tau_i) / s_i)",
        "sampling": "Latin Hypercube",
        "n_events_design": DEFAULT_N_EVENTS,
        "n_events_generated": n_events,
        "seed": seed,
        "ranges": {
            "a": list(DEFAULT_A_RANGE),
            "s": list(DEFAULT_S_RANGE),
            "tau_hours": list(DEFAULT_TAU_HOURS_RANGE),
        },
        "interpolation_box": {
            "a": list(INTERP_A_RANGE),
            "s": list(INTERP_S_RANGE),
        },
        "splits": {
            "train": DEFAULT_N_TRAIN,
            "val": DEFAULT_N_VAL,
            "test": DEFAULT_N_TEST,
            "test_interpolation": DEFAULT_N_TEST - DEFAULT_N_TEST_EXTRAP,
            "test_extrapolation": DEFAULT_N_TEST_EXTRAP,
        },
        "drives": list(drives),
        "tributaries": list(tributaries),
        "tributary_rule": (
            "a_j = a_storm * (1 + eps_j), eps_j ~ U(-0.15, 0.15); "
            "same s and tau as the storm event"
            if tributaries
            else "single inflow (no tributary perturbation)"
        ),
        "notes": [
            "Same boundary parameters drive every listed geometry (HF and LF).",
            "Meshes listed under drives are specifications; build them in HEC-RAS Mapper.",
            "Hydrograph CSVs can be imported to HEC-RAS or converted to DSS in DSSVue.",
        ],
    }


def write_protocol_yaml(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=False)
