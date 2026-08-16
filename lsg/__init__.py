"""LSG: Low-fidelity, Spatial analysis, and Gaussian Process Learning."""

from __future__ import annotations

from typing import Any

__all__ = ["LSGMaxModel", "LSGTSModel"]
__version__ = "0.2.0"


def __getattr__(name: str) -> Any:
    # Lazy imports keep light modules (e.g. figstyle) free of TensorFlow/GPflow.
    if name == "LSGMaxModel":
        from lsg.lsg_max import LSGMaxModel

        return LSGMaxModel
    if name == "LSGTSModel":
        from lsg.lsg_ts import LSGTSModel

        return LSGTSModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
