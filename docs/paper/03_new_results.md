# New experimental results (handoff for manuscript / report)

Machine- and human-readable closure of previously `待补充` gaps.
**Do not treat this file as the manuscript.** Merge numbers into `manuscript.md` / `report.md`, then delete matching `待补充` markers.
All metrics below are read from on-disk JSON / NPZ artifacts (not interpolated).
Host: Windows, ~127.7 GB RAM. No `.git` in this workspace. **仅本地修改，未提交、未推送。**

Baseline pytest (Phase 0, prior session): **77 passed, 1 skipped**.
Post-change pytest (this resume): **80 passed, 1 skipped** (`.\.venv\Scripts\python.exe -m pytest tests -q`).

---

## Gap 1 — Burnett global A/B (CLOSED)

| Item | Value |
|------|-------|
| Config | `config/burnett_global.yaml` (`lsg.zoning: none`; models → `outputs/models/burnett_global`) |
| Command | `.\.venv\Scripts\python.exe scripts\run_lsg_workflow.py --config config\burnett_global.yaml --variants lsg_max --no-pred-examples --summary-out outputs\evaluation\burnett\workflow_summary_grp1_wse_ext_global_max.json` |
| Exit | 0 |
| Wall | ~32 min (incl. Fraehr ingest); `runtime_train_s` ≈ 56.9; `runtime_predict_s` ≈ 4.3 |
| Artifact | `outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_global_max.json` |
| Smoke first | `--events E30,E31,E32,E33,E12` → `workflow_summary_smoke_global_E30E31E32E33E12_max.json` (EXIT=0, ~198 s) |

### Wet_train LSG-Max (Grp1)

| Model | CSI | RMSE (m) |
|-------|-----|----------|
| LF only | 0.853286 | 0.989488 |
| **Global** (`zoning: none`) | **0.975108** | **0.178787** |
| H-LSG (`residual_kmeans`) | 0.975152 | 0.386751 |

Source H-LSG: `outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_hlsg_max.json` (unchanged).

### Test error budget (O2−O1)

| Model | O1 | O2 | O2−O1 | O4 |
|-------|----|----|-------|----|
| Global | 0.074365 | 0.123272 | **0.048907** | 0.178787 |
| H-LSG | 0.074365 | 0.082880 | **0.008515** | 0.386751 |

**Figure panel:** Fig. 3 (`fig03_global_vs_hlsg_ab`) now includes Burnett Global + H-LSG bars.

---

## Gap 2 — Chowilla / Burnett UQ before/after (CLOSED)

Prefer re-score from saved states (no retrain).

### Chowilla

| Item | Value |
|------|-------|
| Command | `.\.venv\Scripts\python.exe scripts\rescore_uq_calibrated.py --config config\chowilla.yaml --summary-in outputs\evaluation\chowilla\workflow_summary_grp1_wse_ext_hlsg_max.json --summary-out outputs\evaluation\chowilla\workflow_summary_grp1_wse_ext_hlsg_max_uq_calibrated.json --variants lsg_max` |
| Exit / wall | 0 / ~42 s |
| Artifact | `outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max_uq_calibrated.json` |

| | CRPS (m) | cov90 | cov90_active | var_scale |
|--|----------|-------|--------------|-----------|
| Before | 2.154657 | 0.482195 | 0.334191 | 1.0 |
| After (`crps_scale`) | 2.155024 | 0.445839 | 0.287444 | 0.418634 |

Note: on Chowilla Grp1 the CRPS scale shrinks intervals but CRPS is essentially flat and coverage moves **away** from nominal — report honestly. Workflow-fit `var_scale` on the original H-LSG summary was 0.3088; this rescore refit is 0.4186 (same protocol, independent calib draw).

### Burnett

| Item | Value |
|------|-------|
| Command | `.\.venv\Scripts\python.exe scripts\rescore_uq_calibrated.py --config config\burnett.yaml --summary-in outputs\evaluation\burnett\workflow_summary_grp1_wse_ext_hlsg_max.json --summary-out outputs\evaluation\burnett\workflow_summary_grp1_wse_ext_hlsg_max_uq_calibrated.json --variants lsg_max` |
| Exit / wall | 0 / ~35–40 min (ingest + `predict_uq` on 18×780k) |
| Artifact | `outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_hlsg_max_uq_calibrated.json` |

| | CRPS (m) | cov90 | cov90_active | var_scale |
|--|----------|-------|--------------|-----------|
| Before | 0.133215 | 0.968304 | 0.943151 | 1.0 |
| After (`crps_scale`) | 0.126974 | 0.938744 | 0.890134 | 0.604178 |

Point CSI/RMSE unchanged vs H-LSG baseline (CSI 0.975152, RMSE 0.386751).

**Figure panel:** Fig. 4 (`fig04_uq_calibration_crps_scale`) panel (c) now has real Before/After CRPS for Chowilla and Burnett.

---

## Gap 3 — Cell-wise P(wet) / `inundation_prob` (CLOSED)

| Case | Command | Artifact key | Shape / mean |
|------|---------|--------------|--------------|
| Carlisle | `scripts\export_inundation_prob.py --config config\carlisle.yaml --variants lsg_max` | `outputs/evaluation/carlisle/pred_examples.npz` → `inundation_prob_lsg_max` | (1, 581061), mean≈0.364 |
| Chowilla | same w/ `config\chowilla.yaml` | `.../chowilla/pred_examples.npz` | (1, 109914), mean≈0.310 |
| Burnett | same w/ `config\burnett.yaml` | `.../burnett/pred_examples.npz` | (18, 780785), mean≈0.554; `predict_uq_s`≈11.9 |

Workflow also updated to persist `inundation_prob_lsg_max` on future runs (`scripts/run_lsg_workflow.py`).

**Figure panel:** Fig. 5 spatial maps panel (e) is now labeled **P(wet)** (not binary depth≥0.03 m).

---

## Gap 4 — `wet_correlation` zoning A/B (CLOSED on Chowilla)

| Item | Value |
|------|-------|
| Config | `config/chowilla_wet_correlation.yaml` (`zoning: wet_correlation`; models → `outputs/models/chowilla_wet_correlation`) |
| Command | `.\.venv\Scripts\python.exe scripts\run_lsg_workflow.py --config config\chowilla_wet_correlation.yaml --variants lsg_max --no-pred-examples --summary-out outputs\evaluation\chowilla\workflow_summary_grp1_wse_ext_wet_correlation_max.json` |
| Exit / train | 0 / `runtime_train_s` ≈ 41.1 |
| Artifact | `outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_wet_correlation_max.json` |

### Chowilla wet_train LSG-Max

| Zoning | CSI | RMSE (m) | test O2−O1 |
|--------|-----|----------|------------|
| global (`none`) | 0.974428 | 0.087668 | (see global summary) |
| `residual_kmeans` | 0.975597 | 0.093158 | 0.013275 |
| **`wet_correlation`** | **0.977800** | **0.094378** | **0.009976** |

**Figure panel:** new Fig. 6 `fig06_zoning_wet_correlation_ab` (CSI / RMSE bars).

---

## Gap 5 — Chowilla / Burnett full time-series Grp1 (未运行 — measured)

**Not attempted as a full workflow run** (would destabilize the working max-surface pipeline). Evidence:

### Burnett
- One HF event file: `wl_data` shape **(431, 780785)** float64 ≈ **2.69 GB** (`Paradise_e1971_real_slmin_1in2_002.npz`).
- 74 main HF NPZs; mean on-disk ≈ 1.77 GB/file.
- In-memory HF cube alone if stacked as float64: **74 × 431 × 780785 × 8 ≈ 199 GB**, plus LF + model state — **≫ 127.7 GB host RAM**.
- Working path remains `ingest.time_reduction: max` (per-event max ≈ 6.2 MB/event).

### Chowilla
- 31 HF plan HDFs under `HD_model_data/High-fidelity/`; **sum ≈ 25.5 GB** on disk (mean ≈ 0.82 GB); largest single plan ≈ 2.14 GB (`Chow_HF.p38.hdf`).
- Config / prior notes: full unsteady 29-event cube does not fit with dual EXT+WSE + UQ on this host; max-surface Grp1 is the practical default.
- Optional future path: streaming/chunked ingest or small `--events` full-TS smoke only — **not executed here**.

---

## Figures regenerated

Command: `.\.venv\Scripts\python.exe scripts\make_figures.py`  
Exit: 0 · wall ≈ 258 s · manifest skips: **[]**

| Figure | Path stem | What changed |
|--------|-----------|--------------|
| Fig. 3 | `outputs/figures/fig03_global_vs_hlsg_ab` | Burnett Global + H-LSG |
| Fig. 4 | `outputs/figures/fig04_uq_calibration_crps_scale` | Chowilla/Burnett before+after CRPS |
| Fig. 5 | `fig05_spatial_maps_{carlisle,chowilla,burnett}_E1` | Panel (e) = P(wet) |
| Fig. 6 | `outputs/figures/fig06_zoning_wet_correlation_ab` | Zoning sensitivity (new) |

Manifest: `outputs/figures/figure_manifest.json` (`n_files`: 24, `skips`: []).

---

## Code / config touchpoints (local only)

- `config/burnett_global.yaml` — models dir `outputs/models/burnett_global`
- `config/chowilla_wet_correlation.yaml` — wet_correlation twin
- `scripts/run_lsg_workflow.py` — `--variants`, `--summary-out`, `--no-pred-examples`, export `inundation_prob_*`
- `scripts/export_inundation_prob.py` — re-score P(wet) into pred_examples
- `scripts/make_figures.py` — Burnett global, UQ pairs, P(wet) panel, Fig. 6
- `tests/test_inundation_prob_export.py` — focused tests

H-LSG Burnett model MD5 unchanged vs backup after global A/B.

---

## Markers the writing agent can clear

| Prior `待补充` | Status |
|----------------|--------|
| Burnett global A/B (Fig. 3) | **Closed** — use table above |
| Chowilla / Burnett UQ before (Fig. 4) | **Closed** — use UQ tables |
| Cell-wise inundation probability (Fig. 5) | **Closed** — P(wet) in pred_examples |
| `wet_correlation` zoning | **Closed** — Chowilla Grp1 + Fig. 6 |
| Chowilla / Burnett full-TS Grp1 | **Still 未运行** — keep marker; cite Gap 5 evidence |
