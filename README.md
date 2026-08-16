# LSG — multi-region multi-fidelity flood surrogate benchmark

Physics-guided **Low-fidelity, Spatial analysis, and Gaussian Process Learning (LSG)** for flood inundation (Fraehr et al. 2022, 2023; Wang et al. 2026).

LSG does **not** depend on HEC-RAS, TUFLOW, or any particular solver. It needs paired high-fidelity / low-fidelity inundation fields (depth or water-surface on a mesh). If a public dump already contains those fields, we ingest them. We do **not** re-run hydrodynamics.

## Repository map (start here)

| Path | What it is |
|------|------------|
| `lsg/` | Core library: EOF, GP/SGPR, EXT+WSE dual field, residual zoning (`zoning.py`), UQ (`uq.py`), diagnostics/O1–O4 (`diagnostics.py`), Fraehr/HEC-RAS ingest |
| `scripts/` | Workflow entrypoints (`run_lsg_workflow.py`), downloads, figure/report builders, UQ rescore |
| `config/` | Case YAMLs: `carlisle.yaml`, `chowilla.yaml`, `burnett.yaml`, zoning A/B twins, `cases.yaml` |
| `tests/` | Unit/integration tests (synthetic + adapter checks); run `pytest tests -q` |
| `docs/paper/` | Progress notes `00`–`03`, English `manuscript.{md,html,pdf}` |
| `docs/report/` | Chinese research report `report.{md,html,pdf}` |
| `outputs/evaluation/{carlisle,chowilla,burnett}/` | Curated metric JSON summaries (source of truth for numbers) |
| `outputs/figures/` | SciencePlots SVG/PDF + `figure_manifest.json` |
| `data/DATA_INVENTORY.md` | What external cubes exist and how to obtain them (**cubes not shipped**) |
| `requirements.txt` | Minimal deps; GPflow/TensorFlow optional |

**Not in this public mirror:** `data/external/**` result cubes (multi-GB), `*.npz` model states / prediction cubes, licensed Brisbane TUFLOW dumps. Download Carlisle/Chowilla/Burnett from Figshare [10.26188/24312658](https://doi.org/10.26188/24312658).

**Reproduce (after downloading cubes):** see Setup below, then `python scripts/run_lsg_workflow.py --config config/carlisle.yaml`. Metrics land under `outputs/evaluation/`. Figures via scripts under `scripts/` / report builders under `docs/`.

## Main line: published result cubes

| Case | HF / LF already computed? | Config | Size | Action |
|------|---------------------------|--------|------|--------|
| **Carlisle (primary)** | Yes — LISFLOOD-FP × HEC-RAS | `config/carlisle.yaml` | ~9.6 GB | Download + unzip + train |
| **Chowilla (secondary)** | Yes — fine/coarse HEC-RAS | `config/chowilla.yaml` | ~32 GB | Same Carlisle stack; `time_reduction: max` |
| **Burnett (tertiary)** | Yes — TUFLOW × HEC-RAS | `config/burnett.yaml` | ~32 GB | Same stack; CSV plan pairing; `time_reduction: max` |
| FloodCastBench | Partial (30 m; 60 m is resampled) | — | ~21.6 GB | After Carlisle |
| Merced / Bald Eagle USACE ZIPs | **No** (terrain + hydrographs only) | kept as optional generators | — | Not required |
| Brisbane TUFLOW | Licensed, not public | `config/brisbane.yaml` | — | Appendix only |

Registry: [`config/cases.yaml`](config/cases.yaml). Inventory: [`data/DATA_INVENTORY.md`](data/DATA_INVENTORY.md).

## Setup

```powershell
cd <this-repo>
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

GPflow remains optional on CPython: `pip install "gpflow>=2.10" "tensorflow>=2.16"`.

## Download Carlisle (already-computed HF/LF)

```powershell
python scripts/download_published_benchmarks.py --dataset carlisle
# unzip data/external/carlisle/Carlisle.zip into data/external/carlisle/
python scripts/run_lsg_workflow.py --config config/carlisle.yaml
pytest tests -q
```

Source: Fraehr (2024) [10.26188/24312658](https://doi.org/10.26188/24312658), CC BY 4.0. Companion `Python_data.zip` (loaders) is already under `data/external/carlisle/python_data/`.

Events `E1`–`E9` are HF `Run1..Run9_alltimesteps.npz` (LISFLOOD-FP, 581 061 cells) paired
with LF `Carlisle_LFmodelA.p01..p09.hdf` (HEC-RAS). The `_extrap` runs and LF plans
`p10`/`p11` are extrapolation cases and stay out of the main set.

The full 9-event LSG-TS fit holds a ~13 GB HF cube in RAM. On a smaller machine,
ingest a subset and keep the same code path:

```powershell
python scripts/run_lsg_workflow.py --config config/carlisle.yaml --events E2,E3,E6
```

`--events` (or `events.include` in the YAML) selects which paired events are read.
`events.splits` in `config/carlisle.yaml` follows Fraehr's leave-one-event-out folds
(`Train_test_split_ValidateOnGrp_N`); with a subset that excludes the validation
event the workflow falls back to the random fraction split.

### LF plan HDFs vs the published geometry export

HEC-RAS writes 5 991 cells per timestep for the Carlisle LF area, of which 310 are
perimeter *ghost* cells with `Cells Minimum Elevation = NaN`. `LF_Geometry_data.npz`
(and `Geometry_data/get_LF_geometry.py`) already drops them, hence 5 681. The plan
HDFs also start ~2 h before the LISFLOOD-FP output, so each event has 8 more LF than
HF timesteps. `lsg.hecras.active_cell_mask` and `lsg.fraehr.align_lf_to_hf_time`
reproduce both steps; the resulting LF pseudo-ECs match Fraehr's published
`LSG_modeldata/LSG_WSE_ValidateOnGrp_1.npz` inputs to 8 decimal places.

## Variants

| Variant | Training target | Maximum flood surface |
|---------|-----------------|------------------------|
| **LSG-TS** | Full inundation time series | `max(predicted time series, axis=time)` |
| **LSG-Max** | Per-event maximum depth surface | Direct prediction |

**Field mode (`lsg.field`):**

| Mode | What is learned | Official depth map |
|------|-----------------|--------------------|
| `depth` (default elsewhere) | Single depth EOF/GP | Reconstructed depth |
| `wse_ext` (Carlisle) | Separate **EXT** (binary) + **WSE** EOF/GP | `where(EXT==1, WSE, Z) → depth` |

Carlisle uses `wse_ext` so CSI can approach Fraehr’s published ~0.969 without treating an LF-extent post-gate as the model. Set `lsg.field: depth` for the depth-only A/B baseline.

**Burnett (tertiary):** same stack under `config/burnett.yaml`. Data junctions at
`data/external/burnett/` (TUFLOW HF × HEC-RAS LF; Figshare `BurnettRV.zip`, file id
`44120564`). Pairing uses `BurnettRV_event_summary.csv` (plan `p12` → `E12`).
Default `time_reduction: max` (~780k HF cells). Grp1 max summary:
`outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_hlsg_max.json`.

Unstructured meshes (HEC-RAS cells, LISFLOOD points) use nearest-neighbour XY interpolation (Fraehr). Structured synthetic grids still use raster upsampling.

**Zonal vs global EOF:** `lsg.zoning` is `none` (global-only baseline) or H-LSG
`residual_kmeans` / `wet_correlation`. Zones model *residuals* on top of global
modes (`lsg/zoning.py`), not hard partitions of the water surface. Under
`wse_ext`, residual zones attach to the **WSE** branch only; binary EXT stays
global.

**Probabilistic LSG:** each EOF mode keeps GP variance; cell-wise depth variance
is closed-form plus a residual/truncation term (`lsg/uq.py`). Enable with
`evaluation.uq` and `evaluation.error_budget` (O1–O4 oracles in `lsg/diagnostics.py`).
With `lsg.field: wse_ext`, O1–O4 run synchronously on EXT and WSE, then combine
with production gating into depth RMSE (same keys as the depth-path budget;
O4 mirrors `predict_dual_depth`).

**UQ calibration (innovation A):** train truncation MSE often leaves intervals
*too wide* (Carlisle Max `coverage_90` ≈ 0.996). A single global scale
`Var_cal = s · Var_raw` is fit on train by minimising Gaussian CRPS
(`evaluation.uq_calibration: crps_scale`; optional `coverage_90`). The latent
mean is unchanged, so CSI/RMSE stay put. Re-score saved states with:

```powershell
python scripts/rescore_uq_calibrated.py --config config/carlisle.yaml
```

Output: `outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix_uq_calibrated.json`.
Also report `coverage_*_active` (obs or mean ≥ τ) — all-cell coverage is inflated
by EXT-dry zeros with σ≈0.

## Synthetic demo (CI only)

```powershell
python scripts/run_lsg_workflow.py --config config/brisbane.yaml --synthetic
```

That is **not** Carlisle, Merced, or Brisbane hydraulics.

## Method summary

1. **Trim domain** — wet / always-flooded / temporary cells (threshold 0.03 m).
2. **EOF on HF** — SVD/PCA; retain modes via North's rule and Kaiser rule.
   With `lsg.field: wse_ext`, fit **two** EOFs: binary EXT on TF cells and WSE
   on wet cells (Fraehr). With `depth`, a single depth EOF.
3. **Interpolate LF → HF** — LF depth → WSE on the LF mesh → nearest HF cell →
   clip to the HF DEM → HF depth (Fraehr). Structured synthetic grids use the
   same WSE clip with a coarsened LF DEM.
4. **Pseudo ECs** — project LF onto HF EOF modes (Fraehr et al. 2022).
5. **Sparse GP** — one SGPR per mode (GPflow) or NumPy RBF GP; mean *and* variance
   (separate emulators for EXT and WSE when dual).
6. **Reconstruct** — for `wse_ext`: binary EXT (AF forced wet) gates WSE, then
   `depth = max(WSE − Z, 0)`; for `depth`: inverse EOF + Tobit. LSG-TS takes
   temporal max of the point map.

## Evaluation metrics

- **RMSE** — depth (wet cells)
- **POD, RFA, CSI** — binary inundation at 0.03 m
- **CRPS, Brier, PIT, coverage** — when `evaluation.uq: true`
- **O1–O4 error budget** — when `evaluation.error_budget: true`

## References

- Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2022). WRR, 58, e2022WR032248.
- Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2023). WRR, 59, e2022WR033836.
- Wang, W., Wang, Q. J., & Nathan, R. (2026). WRR, 62, e2025WR042481. (Brisbane — licensed appendix)
- Fraehr (2024) datasets: https://doi.org/10.26188/24312658
- Hybrid LSG reference code: https://github.com/nfraehr/Hybrid_LSG_model

## Carlisle status (fold: validate on E1)

Official fold with `lsg.field: wse_ext` (trained EXT + WSE). Threshold 0.03 m.

| Model | CSI all / wet_train | RMSE all / wet_train | RFA |
|-------|---------------------|----------------------|-----|
| LF only (WSE→DEM clip) | 0.960 / 0.966 | 0.074 / 0.101 | 0.035 |
| LSG-TS (`depth` EOF, prior) | 0.925 / 0.925 | 0.083 / 0.129 | 0.075 |
| LSG-Max (`depth` EOF, prior) | 0.896 / 0.896 | 0.103 / 0.161 | 0.104 |
| LSG-TS + LF extent gate (diagnostic only) | 0.968 | — | 0.027 |
| **LSG-TS (`wse_ext`, official)** | **0.969 / 0.969** | **0.080 / 0.124** | **0.026** |
| LSG-Max (`wse_ext`) | 0.976 / 0.976 | 0.099 / 0.154 | 0.017 |
| Fraehr published LSG (Grp1, wet cells, EXT+WSE) | 0.969 | 0.087 (WSE TS) | — |

**H-LSG vs global** (`lsg.zoning: residual_kmeans`, same `wse_ext` Grp1 fold).
Summaries: `workflow_summary_full_Grp1_wse_ext_budget.json` (global, pre-fix
SGPR) vs `workflow_summary_full_Grp1_wse_ext_hlsg_residual_kmeans.json`
(H-LSG, pre-fix SGPR) vs `workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix.json`
(H-LSG after the inducing-point fix below).

| Variant | CSI | RMSE | test O1 | O2 | O3 | O4 | O2−O1 |
|---------|-----|------|---------|----|----|----|-------|
| LSG-TS global (pre-fix) | 0.969 | 0.080 | 0.018 | 0.035 | 0.239 | 0.136 | 0.017 |
| LSG-TS H-LSG (pre-fix SGPR) | 0.969 | **0.055** | 0.018 | **0.033** | 0.240 | 0.149 | 0.015 |
| LSG-TS H-LSG + SGPR fix | **0.970** | 0.099 | 0.018 | **0.033** | 0.240 | **0.102** | 0.015 |
| LSG-Max global (pre-fix) | 0.976 | 0.099 | 0.048 | 0.112 | 0.122 | 0.154 | 0.064 |
| LSG-Max H-LSG (pre-fix SGPR) | 0.976 | 0.172 | 0.048 | **0.052** | **0.068** | 0.267 | **0.005** |
| LSG-Max H-LSG + SGPR fix | 0.976 | **0.061** | 0.048 | 0.052 | 0.068 | **0.094** | 0.005 |

**Root cause of the Max O4 regression:** not residual-EOF count or zone
starvation. LSG-Max has 8 train rows, so `inducing_point_fraction: 0.02`
collapsed to **2** SGPR inducing points placed on a per-column `linspace`
diagonal. With H-LSG the GP input grows from 1 EC to 13 ECs; a rank-2
diagonal inducing set cannot represent the LF→HF map, so train O4 blew up
(0.20 → 0.72) and test O4 followed (0.15 → 0.267). Fix: initialise inducing
points from training rows and floor the budget at
`lsg.min_inducing_points` (capped at `n_train`, where SGPR is exact). LSG-TS
(>2000 rows) still uses the fraction rule (~42 points). Default config keeps
`zoning: residual_kmeans`.

Takeaway: residual zones cut Max-path truncation gap (O2−O1). With the SGPR
fix, Max O4/RMSE recover and beat the global baseline; TS O4 also improves
(0.149 → 0.102) and CSI stays flat/slightly up. The pre-fix TS max-surface
RMSE of 0.055 coincided with a defective residual GP and does **not** survive
a correct SGPR (post-fix 0.099); treat that older number as an artifact.

**UQ calibration (post SGPR-fix stack):** CRPS-optimal global variance scale on
train (`crps_scale`). Summary:
`workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix_uq_calibrated.json`.
Point CSI/RMSE unchanged (delta ≈ 0). Max benefits most (`s≈0.42`, CRPS
0.039→0.028); TS is already near-calibrated (`s≈0.90`, active cov50≈0.49 before
scaling). Prefer `coverage_*_active` over all-cell coverage (EXT-dry σ≈0 inflates
the latter).

Subset smoke (`--events E2,E3,E6`, random holdout): LSG-TS max CSI ≈ 0.943–0.944
under both zonings (see `*_subset_E2E3E6_*` summaries).

**Scoring:** Our `wet_idx` matches Fraehr `Categories_HFdata_ValidateOnGrp_1`
exactly (239 482 cells). CSI is unchanged under that mask because all LSG false
alarms already sit inside it; RMSE rises when dry zeros are excluded. The
depth-only path over-predicted extent (high RFA); `wse_ext` recovers published
CSI without using an LF-extent post-gate as the model. LF gate remains
diagnostic only in `score_protocol`.

**Training target:** Interpolate uses Fraehr’s WSE→HF-DEM clip. With
`wse_ext`, EXT learns binary wet/dry on temporary cells and WSE learns the
water surface on wet cells; depth is `where(EXT==1, WSE, Z) − Z`. With
`depth`, a single depth EOF/GP is used (A/B baseline). Re-score / retrain:

```powershell
python scripts/rescore_fraehr_protocol.py
python scripts/run_lsg_workflow.py --config config/carlisle.yaml
# depth-only A/B: set lsg.field: depth in the YAML (or a copy)
```

## Chowilla status (fold: validate on E1 / Grp1)

Same Carlisle-proven stack (`wse_ext`, `residual_kmeans`, SGPR floor, `crps_scale`).
Config: `config/chowilla.yaml`. Data via junctions under `data/external/chowilla/`
(or download `Chowilla.zip`). Default ingest uses HEC-RAS **max** surfaces
(`ingest.time_reduction: max`) so 29 events × ~110k cells fit in RAM; full TS
smoke: `--events E1,E2,E3 --time-reduction full`.

| Surface (Grp1 max) | CSI all / wet_train | RMSE all / wet_train |
|--------------------|---------------------|----------------------|
| LF only (WSE→DEM clip) | 0.930 / 0.925 | 0.690 / 0.690 |
| LSG-Max H-LSG (`wse_ext`) | 0.390 / **0.976** | 3.79 / **0.093** |
| Fraehr published LSG (Grp1) | — / 0.982 | — / 0.108 |

**Zoning:** kept `residual_kmeans` (stable O1–O4). Vs global (`config/chowilla_global.yaml`):
wet CSI 0.9756 vs 0.9744; RMSE 0.093 vs 0.088; test **O2−O1** 0.013 vs 0.057
(residual zones shrink truncation gap, same Carlisle Max story). UQ `var_scale`
≈ 0.31 H-LSG / 0.42 global (Carlisle Max ≈ 0.42).
**Anti-case read:** LF extent already strong (CSI ~0.93 all-cells). On Fraehr
`wet_train`, LSG still cuts depth RMSE sharply (0.69 → 0.09) and lifts CSI
(0.925 → 0.976). All-cells LSG CSI is low because EXT learns only on the train
wet mask (Fraehr Categories) — score `wet_train` for protocol comparison.
Summaries: `outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max.json`
and `..._global_max.json`.
## Remaining gaps

- Chowilla full-TS Grp1 fold (memory); optional `wet_correlation` / global A/B polish.
- Brisbane TUFLOW/URBS remains licence-gated; ingest under `data/raw/` is unchanged.
- Optional H-LSG A/B: `wet_correlation` zoning; further residual-mode / zone sweeps
  after the SGPR inducing fix.

## Paper drafting notes

Progress review, literature gap analysis, and manuscript framework (local drafts):
[`docs/paper/00_progress_review.md`](docs/paper/00_progress_review.md),
[`docs/paper/01_literature_review.md`](docs/paper/01_literature_review.md),
[`docs/paper/02_paper_framework.md`](docs/paper/02_paper_framework.md).
