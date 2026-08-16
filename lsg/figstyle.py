"""Publication figure style for LSG reports (SciencePlots + Times New Roman).

Apply once at process start via :func:`apply_lsg_style`. All report/paper
figures should call this before creating axes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Journal column widths (Nature-family approximate).
SINGLE_COL_IN = 3.5
DOUBLE_COL_IN = 7.2
EXPORT_DPI = 600

# Restrained categorical palette (shared across figures).
PALETTE = {
    "lf": "#767676",
    "lsg_max": "#0F4D92",
    "lsg_ts": "#42949E",
    "global": "#4D4D4D",
    "hlsg": "#3775BA",
    "sgpr": "#B64342",
    "train": "#8BCF8B",
    "test": "#E9A6A1",
    "o1": "#CFCECE",
    "o2": "#AADCA9",
    "o3": "#3775BA",
    "o4": "#0F4D92",
    "depth": "Blues",
    "error": "RdBu_r",
    "inundation": "viridis",
    # Fraehr/Wang categorical extent map (hit / miss / false alarm / dry)
    "hit": "#2C7BB6",
    "miss": "#D7191C",
    "false_alarm": "#FDAE61",
    "dry": "#E8E8E8",
}

_FONT_CANDIDATES: Sequence[str] = (
    "Times New Roman",
    "Nimbus Roman",
    "Liberation Serif",
    "DejaVu Serif",
)

_STYLE_APPLIED = False
_ACTIVE_SERIF: str | None = None


def resolve_serif_font() -> tuple[str, bool]:
    """Return (family_name, is_times_new_roman).

    Prefers Times New Roman when registered with Matplotlib; otherwise the
    first metric-compatible serif that resolves on this machine.
    """
    available = {f.name for f in font_manager.fontManager.ttflist}
    # Also probe Windows font files directly in case the name map is stale.
    times_path = Path(r"C:\Windows\Fonts\times.ttf")
    if times_path.is_file() and "Times New Roman" not in available:
        try:
            font_manager.fontManager.addfont(str(times_path))
            available = {f.name for f in font_manager.fontManager.ttflist}
        except (OSError, RuntimeError, ValueError):
            pass

    for name in _FONT_CANDIDATES:
        if name in available:
            try:
                path = font_manager.findfont(
                    font_manager.FontProperties(family=name),
                    fallback_to_default=False,
                )
            except (ValueError, RuntimeError):
                continue
            if path and "DejaVuSans" not in Path(path).name:
                return name, name == "Times New Roman"
        if name == "Times New Roman" and times_path.is_file():
            return "Times New Roman", True
    return "DejaVu Serif", False


def apply_lsg_style(*, force: bool = False) -> dict:
    """Apply SciencePlots ``science`` + ``no-latex`` and LSG rcParams.

    Returns a small metadata dict (font family, whether Times was used, dpi).
    """
    global _STYLE_APPLIED, _ACTIVE_SERIF
    if _STYLE_APPLIED and not force:
        return style_metadata()

    import scienceplots  # noqa: F401  — registers styles with matplotlib

    plt.style.use(["science", "no-latex"])
    serif, is_times = resolve_serif_font()
    _ACTIVE_SERIF = serif

    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [serif, "DejaVu Serif", "serif"],
            "mathtext.fontset": "stix",
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.titlesize": 10,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.2,
            "lines.markersize": 4.0,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "xtick.minor.width": 0.6,
            "ytick.minor.width": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "figure.dpi": 150,
            "savefig.dpi": EXPORT_DPI,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "text.usetex": False,
        }
    )
    _STYLE_APPLIED = True
    return {
        "serif_family": serif,
        "times_new_roman": is_times,
        "export_dpi": EXPORT_DPI,
        "single_col_in": SINGLE_COL_IN,
        "double_col_in": DOUBLE_COL_IN,
    }


def style_metadata() -> dict:
    serif = _ACTIVE_SERIF or resolve_serif_font()[0]
    return {
        "serif_family": serif,
        "times_new_roman": serif == "Times New Roman",
        "export_dpi": EXPORT_DPI,
        "single_col_in": SINGLE_COL_IN,
        "double_col_in": DOUBLE_COL_IN,
    }


def figsize_single(height: float = 2.6) -> tuple[float, float]:
    return (SINGLE_COL_IN, height)


def figsize_double(height: float = 3.2) -> tuple[float, float]:
    return (DOUBLE_COL_IN, height)


def add_panel_label(ax, label: str, *, x: float = -0.12, y: float = 1.06) -> None:
    """Add a Nature-style panel tag such as ``(a)``."""
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        fontweight="bold",
        clip_on=False,
    )


def save_pub(fig: mpl.figure.Figure, stem: Path | str, *, dpi: int = EXPORT_DPI) -> list[Path]:
    """Write PDF, SVG, and high-DPI PNG for one figure stem."""
    stem_path = Path(stem)
    stem_path.parent.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for ext in ("pdf", "svg", "png"):
        out = stem_path.with_suffix(f".{ext}")
        kw = {"bbox_inches": "tight"}
        if ext == "png":
            kw["dpi"] = dpi
        fig.savefig(out, **kw)
        written.append(out)
    return written
