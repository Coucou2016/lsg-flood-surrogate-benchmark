from lsg.config import load_config
from lsg.data import (
    PAPER_LSG_TS_TRAIN_IDS,
    PAPER_VALIDATION_IDS,
    load_split_ids,
    resolve_train_test_indices,
    split_by_event_ids,
)
from pathlib import Path


def test_paper_ts_split_uses_eight_and_ve():
    ids = list(PAPER_LSG_TS_TRAIN_IDS) + list(PAPER_VALIDATION_IDS)
    train, test = split_by_event_ids(
        ids, PAPER_LSG_TS_TRAIN_IDS, PAPER_VALIDATION_IDS
    )
    assert train.size == 8
    assert test.size == 4
    assert {ids[i] for i in test.tolist()} == set(PAPER_VALIDATION_IDS)


def test_missing_paper_ids_fall_back_to_random():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "config" / "brisbane.yaml")
    event_ids = [f"synthetic_event_{i:02d}" for i in range(12)]
    train, test, how = resolve_train_test_indices(event_ids, cfg, "lsg_ts")
    assert how == "random_fraction"
    assert train.size + test.size == 12
    assert train.size >= 1 and test.size >= 1


def test_splits_yaml_matches_paper_counts():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "config" / "brisbane.yaml")
    splits = load_split_ids(cfg)
    assert len(splits["lsg_ts_train"]) == 8
    assert len(splits["lsg_max_train"]) == 47
    assert splits["validation"] == ["FE21", "FE26", "FE50", "FE51"]
    assert "FE21" not in splits["lsg_max_train"]
    assert "FE26" not in splits["lsg_max_train"]
    assert "FE48" in splits["lsg_ts_train"]
    assert "FE49" in splits["lsg_ts_train"]
