"""Real-data ingest: pair by event id, skip empty dirs without crashing."""

from pathlib import Path

import numpy as np
import pytest

from lsg.data import (
    detect_real_event_data,
    has_paired_event_data,
    ingest_lf_hf_npz_dir,
    normalize_event_id,
)


def _write_event(path: Path, depth, terrain=None, shape=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"depth": np.asarray(depth, dtype=np.float64)}
    if terrain is not None:
        payload["terrain"] = np.asarray(terrain, dtype=np.float64)
    if shape is not None:
        payload["shape"] = np.asarray(shape)
    np.savez(path, **payload)


def test_normalize_event_id():
    assert normalize_event_id("FE01") == "FE1"
    assert normalize_event_id("fe21") == "FE21"
    assert normalize_event_id("VE1") == "VE1"


def test_ingest_pairs_by_stem_not_sort_order(tmp_path):
    hf = tmp_path / "hf"
    lf = tmp_path / "lf"
    terrain = np.zeros(4)
    _write_event(hf / "FE21.npz", np.ones((3, 4)), terrain, (2, 2))
    _write_event(hf / "FE20.npz", np.full((3, 4), 2.0), terrain, (2, 2))
    _write_event(lf / "FE20.npz", np.full((3, 1), 0.2), None, (1, 1))
    _write_event(lf / "FE21.npz", np.full((3, 1), 0.1), None, (1, 1))
    data = ingest_lf_hf_npz_dir(hf, lf)
    assert data["event_ids"] == ["FE20", "FE21"]
    assert data["hf_depth"].shape == (2, 3, 4)
    np.testing.assert_allclose(data["hf_depth"][0, 0, 0], 2.0)


def test_ingest_raises_on_mismatch_when_strict(tmp_path):
    hf = tmp_path / "hf"
    lf = tmp_path / "lf"
    _write_event(hf / "FE1.npz", np.ones((2, 3)))
    _write_event(lf / "FE2.npz", np.ones((2, 1)))
    with pytest.raises(ValueError, match="mismatch"):
        ingest_lf_hf_npz_dir(hf, lf, strict=True)


def test_empty_dirs_are_not_real_data(tmp_path):
    hf = tmp_path / "hf"
    lf = tmp_path / "lf"
    hf.mkdir()
    lf.mkdir()
    assert has_paired_event_data(hf, lf) is False
    with pytest.raises(FileNotFoundError):
        ingest_lf_hf_npz_dir(hf, lf)


def test_detect_real_event_data_on_repo_config():
    from lsg.config import load_config

    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "config" / "brisbane.yaml")
    status = detect_real_event_data(cfg)
    assert status["available"] is False
    assert status["paired_event_ids"] == []
