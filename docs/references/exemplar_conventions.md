# Exemplar presentation conventions (Fraehr / Wang → our outputs)

Source-grounded notes from local Markdown extracts of Fraehr 2022/2023 and Wang 2026 (English structural readers). Fraehr 2024 PDF was not lawfully available here; case-benchmark framing still follows that paper’s public Carlisle/Chowilla/Burnett design as cited in our literature review.

## 1. Figure order (visual-first)

Exemplars present **geography and inundation pictures before aggregate statistics**.

| Order | Exemplar pattern | Evidence |
| --- | --- | --- |
| 1 | **Study-area / domain map** | Fraehr 2022 Fig. 2; Fraehr 2023 Fig. 4; Wang 2026 Fig. 2 |
| 2 | **Inundation extent comparisons** (HF vs LF vs LSG) with categorical **hit / miss / false-alarm** (or agreement) coloring | Fraehr 2022 Fig. 3 + text on detected/missed/false alarm; Fraehr 2023 Fig. 8–9 (Detected/Misses/False alarms); Wang 2026 Fig. 7 (blue agreement, red HF-only, yellow LSG-only, white both-dry) |
| 3 | **Peak-depth / depth error maps** with **diverging red–blue** (over- vs under-estimation) | Wang 2026 Fig. 6; Fraehr 2023 Fig. 7 (peak depth fields; error discussed in text) |
| 4 | **Hydrographs / time-series at gauges or selected locations** (when dynamics exist) | Wang 2026 Fig. 5; Fraehr 2022 Fig. 4 (extent time series) |
| 5 | **Metric plots** (boxplots, bubbles, bars) and **tables** | Fraehr 2023 Fig. 5–6 + Tables 1–3; Wang 2026 Fig. 4, 8 + Table 1 |

**Our change:** manuscript/report Results now follow domain → extent (H/M/FA) → depth-error maps → P(wet) (novel UQ panel, **after** deterministic maps) → then CSI/RMSE bars, O1–O4, capacity controls, UQ calibration curves, zoning sensitivity. Hydrographs: **Carlisle/Chowilla/Burnett `pred_examples.npz` store max-only fields** → no per-timestep gauge panels; stated as 缺数据, not invented.

## 2. Categorical extent map colors

Prefer Wang Fig. 7 / Fraehr Fig. 9 semantics at wet threshold **τ = 0.03 m**:

| Category | Definition | Color (our maps) |
| --- | --- | --- |
| Hit / agreement | HF wet ∧ pred wet | Blue |
| Miss | HF wet ∧ pred dry | Red |
| False alarm | HF dry ∧ pred wet | Gold / yellow |
| Both dry | HF dry ∧ pred dry | Light gray / omitted |

Plot separate panels for **LF vs HF** and **LSG vs HF** so the multi-fidelity correction is visually obvious (Fraehr-style HF/LF/LSG juxtaposition).

## 3. Peak-depth error maps

- Field: `pred − HF` (and `LF − HF` for contrast).
- Colormap: diverging **RdBu_r** (red = overestimate, blue = underestimate), symmetric limits from robust percentiles.
- Equal aspect; easting/northing axes; no flipped coordinates.

## 4. Tables

Exemplars use:

- **Per-event / per-fold CSI, RMSE** (and POD/RFA when reported) — Fraehr 2023 Table 1; Wang Table 1.
- **Runtime / speed-up** when computational claims matter — Wang §3.5 / results text; Fraehr efficiency statements.
- Explicit **wet-mask / Categories wet_idx** statements when scoring is mask-dependent (our Fraehr-compatible `wet_train` protocol).

## 5. Metric presentation style

| Item | Convention |
| --- | --- |
| Wet threshold | **0.03 m** depth (Wang Eq. 3 text; our pipeline `DEPTH_TAU_M`) |
| Extent skill | **CSI** = H/(H+M+F); Fraehr also reports **POD**, **RFA** |
| Depth skill | **RMSE** on wet cells / protocol wet index |
| Event naming | Case + event id (e.g. Carlisle E1; Burnett hold-out ids; Wang VE1–VE4) |
| Wet mask | State whether scores are **all_cells** vs **wet_train** (Fraehr Categories); never silently mix |
| Variants | Name **LSG-Max** vs **LSG-TS** explicitly (Wang) |

## 6. What we changed in our stack

1. **New figures** in `scripts/make_figures.py`: domain overview; per-case extent H/M/FA maps; peak-depth error maps (LSG−HF and LF−HF); P(wet) moved after those deterministic maps.
2. **Renumbered Results** in `docs/paper/manuscript.md` and the Chinese report builder so intuition (maps) precedes bars/tables.
3. **Kept** capacity-control **negative** framing and O1–O4 / CRPS sections **after** the visual block.
4. **Honest gaps:** no fabricated hydrographs; Fraehr 2024 PDF absent; domain figure is cell-scatter outlines when DEM raster is unavailable.
