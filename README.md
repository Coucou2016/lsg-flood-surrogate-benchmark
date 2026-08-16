# LSG flood surrogate benchmark

Physics-guided **Low-fidelity, Spatial analysis, and Gaussian Process Learning (LSG)** for flood inundation, with residual hierarchical zoning (H-LSG), O1–O4 oracle error budgets, and CRPS-scale GP uncertainty calibration.

This public snapshot is intended for code/docs review. It does **not** ship the multi-GB Figshare HF/LF cubes.

## Repository map

| Path | Contents |
|------|----------|
| `lsg/` | Core library (EOF, GP/SGPR, zoning, UQ, diagnostics, ingest) |
| `scripts/` | Workflow runners, rescoring, figure/report builders |
| `tests/` | Pytest suite (synthetic + unit) |
| `config/` | Case YAMLs (`carlisle`, `chowilla`, `burnett`, …) |
| `docs/paper/` | Manuscript + literature/progress notes |
| `docs/report/` | Chinese research report |
| `outputs/evaluation/**/*.json` | Curated metric summaries (evidence for tables) |
| `outputs/figures/` | SVG/PDF figure sources + `figure_manifest.json` |

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest tests -q
```

Optional Sparse GP: `pip install "gpflow>=2.10" "tensorflow>=2.16"`.

## Data (not in this repo)

Public cubes: Figshare [10.26188/24312658](https://doi.org/10.26188/24312658). Download with `scripts/download_published_benchmarks.py` after placing data under `data/external/`.

## Headline positioning (bounded)

- Multi-fidelity LSG is the dominant skill source vs LF-only.
- Residual zoning mainly shrinks truncation gap **O2−O1**, not large CSI gains vs global EOF.
- CRPS-scale variance calibration improves probabilistic scores without changing CSI/RMSE.
- Chowilla all-cells CSI collapse is a **strong-LF scoring-protocol anti-case**.

Do not claim “first localized EOF” or “first LSG error decomposition” (see `docs/paper/01_literature_review.md`).

## License / citation

Method lineage: Fraehr et al. (2022, 2023, 2024); Wang et al. (2026). Public data DOI above.
