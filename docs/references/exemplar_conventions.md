# Exemplar presentation conventions (Fraehr / Wang → our outputs)

Source-grounded notes from local Markdown extracts of Fraehr 2022/2023/2024 (Water Research + J. Environ. Manage.) and Wang 2026. MinerU API produced the two 2024 Elsevier full-text Markdown files (local-only).

## 1. Figure order (visual-first)

Exemplars present **geography and inundation pictures before aggregate statistics**.

| Order | Exemplar pattern | Evidence |
| --- | --- | --- |
| 1 | **Study-area / domain map** | Fraehr 2022 Fig. 2; Fraehr 2023 Fig. 4; Fraehr 2024 Fig. 2; Wang 2026 Fig. 2 |
| 2 | **Inundation extent comparisons** (HF vs LF vs LSG) with categorical **hit / miss / false-alarm** (or agreement) coloring | Fraehr 2022 Fig. 3 + text on detected/missed/false alarm; Fraehr 2023 Fig. 8–9; Fraehr 2024 Fig. 3 (CSI boxplots after maps); Wang 2026 Fig. 7 |
| 3 | **Peak-depth / depth error maps** with **diverging red–blue** (over- vs under-estimation) | Wang 2026 Fig. 6; Fraehr 2023 Fig. 7; Fraehr 2024 peak-depth panels + Fig. 11 (extrapolation) |
| 4 | **Hydrographs / time-series at gauges or selected locations** (when dynamics exist) | Wang 2026 Fig. 5; Fraehr 2022 Fig. 4; Fraehr 2024 AvgRMSE/FI on hydrographs |
| 5 | **Metric plots** (boxplots, bubbles, bars) and **tables** | Fraehr 2024 Fig. 3 + Table 2; Fraehr 2023 Fig. 5–6 + Tables 1–3; Wang 2026 Fig. 4, 8 + Table 1 |

**Our Results order (unchanged intent):** domain → extent (H/M/FA) → depth-error maps → P(wet) (UQ, after deterministic maps) → CSI/RMSE bars/tables → O1–O4 error budget → capacity controls → UQ calibration → zoning sensitivity. Hydrographs: Carlisle/Chowilla/Burnett `pred_examples.npz` store **max-only** fields → no per-timestep gauge panels; stated as 缺数据, not invented.

## 2. Fraehr 2024 Water Research — benchmark protocol (source of our cubes)

Verified from MinerU extract of *Assessment of surrogate models…* (Water Research 252:121202):

| Item | Fraehr 2024 published protocol | Our implementation / wording |
| --- | --- | --- |
| Competitors | LSG vs **1dCNN**, **LSTM-SRR**, **GP-EOF**, **LSTM-EOF** | We do **not** re-train those ML baselines; we cite Fraehr 2024 for the comparison framing and use the same public cubes |
| Cases | Carlisle 14.5 km² / 9 events / **9 groups**; Chowilla 740 km² / 29 / **10**; Burnett 1,479 km² / 74 / **4** | Same Figshare cubes; our Table 1 event counts match |
| CV | **Leave-one-out on groups** sharing temporal patterns (one group held out per fold) | Headline tables use published **ValidateOnGrp_1 / Grp1** fold only (one fold of that LOOCV), not mean±std over all folds |
| Wet mask | Score (and train) only cells **flooded in the training events** | **`wet_train`** = Fraehr Categories wet index; also report **`all_cells`** for protocol sensitivity |
| Extent metric | **CSI** = TP/(TP+FN+FP) | Same CSI; plus POD/RFA |
| Depth metrics | **AvgPeakDiff**, **R²** (peak); **AvgRMSE**, **FI** (±5 cm / ±5% timing) on hydrographs | Headline depth skill is **RMSE on max surfaces** (and TS RMSE where available). We do **not** claim numerical identity to AvgPeakDiff/FI |
| Wet threshold τ | Evaluation text scores “flooded” cells; numeric τ restated in companion Categories / Wang 2026 as **depth ≥ 0.03 m** | We use **τ = 0.03 m** throughout and state that inheritance explicitly |
| Extrapolation | Hold-out event with inflows **50% larger** than training; optional retrain with 100% larger | **Not run** here — closed limitation (perfect-prognosis Grp1 only) |
| Early stopping | Within-fold 90%/10% random split of training samples | Not mirrored; our Max path uses event-level Grp1 splits |

**Carlisle number reconciliation (wording, not data edits):** Fraehr 2024 reports LSG CSI high on Carlisle (all models median CSI > 0.75; pooled Table 2 LSG CSI **0.95±0.05** across sites/folds). Our Carlisle LSG-Max H-LSG Grp1 wet_train CSI **0.976** and LF CSI **0.966** are **Grp1 single-fold** scores under τ=0.03 m and wet_train — consistent with “high CSI,” **not** a re-report of their pooled mean±std or AvgRMSE/FI. Do not equate our Table 2 cells to Fraehr 2024 Table 2.

## 3. Fraehr 2024/2025 J. Environ. Manage. — LESS (relevant conventions only)

Verified: *Generation and selection of training events…* (J. Environ. Manage. 373:123570). Introduces **LESS** (Low-fidelity Event Selection Strategy): simulate many candidates with LF → keep historic HF events → add maximum-inundation contributors (≥90% of envelope) → iteratively add EOF-space-diverse events → run HF only on the selected subset. Demonstrated with LSG on the same three sites; claims RMSE < 0.23 m on unseen events with up to **97%** fewer HF runs versus using all candidates.

**What we take:** Related-work positioning only — LESS addresses *which* HF events to buy under a budget; our capacity controls address *how* residual EOF capacity is allocated **given** a fixed published split. We do **not** force-fit LESS into our Results or re-run event selection.

## 4. Categorical extent map colors

Prefer Wang Fig. 7 / Fraehr Fig. 9 semantics at wet threshold **τ = 0.03 m**:

| Category | Definition | Color (our maps) |
| --- | --- | --- |
| Hit / agreement | HF wet ∧ pred wet | Blue |
| Miss | HF wet ∧ pred dry | Red |
| False alarm | HF dry ∧ pred wet | Gold / yellow |
| Both dry | HF dry ∧ pred dry | Light gray / omitted |

Plot separate panels for **LF vs HF** and **LSG vs HF**.

## 5. Peak-depth error maps

- Field: `pred − HF` (and `LF − HF` for contrast).
- Colormap: diverging **RdBu_r** (red = overestimate, blue = underestimate), symmetric limits from robust percentiles.
- Equal aspect; easting/northing axes; no flipped coordinates.

## 6. Tables / metric style

| Item | Convention |
| --- | --- |
| Wet threshold | **0.03 m** (Wang 2026; our `DEPTH_TAU_M` / Categories) |
| Extent skill | **CSI** = H/(H+M+F); also POD, RFA |
| Depth skill | **RMSE** on wet cells / protocol wet index (our headline); Fraehr 2024 additionally AvgPeakDiff/R²/AvgRMSE/FI |
| Event naming | Case + event id (Carlisle E1; Burnett hold-outs; Wang VE1–VE4) |
| Wet mask | Always state **all_cells** vs **wet_train** |
| Variants | Name **LSG-Max** vs **LSG-TS** (Wang); cite Fraehr 2024 ML baselines when positioning |

## 7. What we changed in our stack

1. Figures in `scripts/make_figures.py`: domain; extent H/M/FA; peak-depth error; P(wet) after deterministic maps.
2. Results renumbered so maps precede bars/tables.
3. Capacity-control **negative** localisation framing kept honest after Fraehr 2024 re-read.
4. Honest gaps: no fabricated hydrographs; no Fraehr 2024 ML re-benchmark; no 50% extrapolation suite; Elsevier full texts local-only.
