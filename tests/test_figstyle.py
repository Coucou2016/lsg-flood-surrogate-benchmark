"""Smoke tests for publication figure style helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
pytest.importorskip("scienceplots")

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lsg.figstyle import (  # noqa: E402
    EXPORT_DPI,
    apply_lsg_style,
    resolve_serif_font,
    save_pub,
)


def test_resolve_serif_font_returns_registered_family():
    family, is_times = resolve_serif_font()
    assert isinstance(family, str) and family
    assert isinstance(is_times, bool)
    if is_times:
        assert family == "Times New Roman"


def test_apply_lsg_style_sets_serif_and_dpi():
    meta = apply_lsg_style(force=True)
    assert meta["export_dpi"] == EXPORT_DPI
    assert meta["serif_family"]
    import matplotlib as mpl

    family = mpl.rcParams["font.family"]
    if isinstance(family, (list, tuple)):
        assert "serif" in family
    else:
        assert family == "serif"
    assert mpl.rcParams["savefig.dpi"] == EXPORT_DPI
    assert mpl.rcParams["text.usetex"] is False


def test_save_pub_writes_pdf_svg_png(tmp_path):
    apply_lsg_style(force=True)
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    ax.plot([0, 1], [0, 1])
    ax.set_xlabel("x (−)")
    ax.set_ylabel("y (−)")
    paths = save_pub(fig, tmp_path / "smoke_fig")
    plt.close(fig)
    suffixes = {p.suffix for p in paths}
    assert suffixes == {".pdf", ".svg", ".png"}
    assert all(p.is_file() and p.stat().st_size > 0 for p in paths)
