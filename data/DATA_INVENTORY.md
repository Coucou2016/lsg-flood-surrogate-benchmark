# Data inventory

Last updated: 2026-08-16.

**Policy:** LSG trains on paired HF/LF inundation fields. Solver brand is irrelevant. Prefer public dumps that already contain results. Do **not** re-run HEC-RAS / TUFLOW when those fields exist.

This repository is a **multi-region public-data LSG benchmark**. Brisbane TUFLOW/URBS is an optional licensed appendix. **Do not treat synthetic demo arrays as real hydraulics.**

## Public cases (computed results vs generator-only)

| Dataset | Role | Local path | Status 2026-08-16 | How to get |
|---------|------|------------|-------------------|------------|
| **Carlisle.zip (Fraehr 2024)** | **primary** — already-computed HF/LF | `data/external/carlisle/` | **unzipped** 2026-08-15 (9,603,961,435 bytes, MD5 `5b4bf7b6007d858a67050fdecc7e6b5f`). `Geometry_data/`, `HD_model_data/` (11 HF NPZ + 11 LF HDF), `Train_test_split_data/`, `Result_data/` present. | `python scripts/download_published_benchmarks.py --dataset carlisle` — [10.26188/24312658](https://doi.org/10.26188/24312658) |
| **Comparison_results.zip (Fraehr 2024)** | published figure data / plotting scripts | `data/external/carlisle/comparison_results/` | **unzipped** 2026-08-15 (279,586,627 bytes, MD5 `a34de5b89811804d8baa8c6bfb11ef7f`). No CSI/RMSE CSV; numeric arrays are `Result_data/Validation_results.npz` inside Carlisle.zip. | `python scripts/download_published_benchmarks.py --dataset comparison_results` |
| **Chowilla.zip (Fraehr 2024)** | **secondary** — fine/coarse HEC-RAS | `data/external/chowilla/` | **available** 2026-08-16 via junctions to sibling Fraehr unzip (zip MD5 `16e3f4d2b8514b1493a1d78af2751707`). Config `config/chowilla.yaml`; default `ingest.time_reduction: max`. | `python scripts/download_published_benchmarks.py --dataset chowilla` if junctions unavailable |
| **BurnettRV.zip (Fraehr 2024)** | **tertiary** — TUFLOW × HEC-RAS | `data/external/burnett/` | **available** 2026-08-16 via junctions to sibling Fraehr unzip (zip MD5 `93df54d5bb54e9b23a09e648648146d8`). Config `config/burnett.yaml`; HF 780785 / LF 15256; `time_reduction: max`; event ids = LF plan via CSV. | `python scripts/download_published_benchmarks.py --dataset burnett` if junctions unavailable |
| FloodCastBench | deferred | — | skipped (~21.6 GB); 60 m is resampled, not re-run LF | Zenodo 14017092 |
| Merced River HEC-RAS tutorial ZIP | generator-only (no result HDF) | `data/external/hecras_merced/original/` | downloaded; **not used for training** | USACE tutorial |
| Bald Eagle Creek tutorial ZIP | generator-only | `data/external/hecras_bald_eagle/original/` | downloaded; **not used for training** | USACE tutorial |

Carlisle event CSVs and exact CV splits are under `HD_model_data/` and `Train_test_split_data/` (unzipped from Carlisle.zip; not a separate Figshare file). Published CSI/RMSE arrays: `Result_data/Validation_results.npz` (9 CV folds x 5 models) and `Result_data/Validation_results_extrap.npz`; paper boxplots in `comparison_results/Figures/`.

Chowilla: 29 events / 10 groups; published `Result_data/Validation_results.npz` is (29, 5). Full 29-event unsteady cubes do not fit in RAM (~110k HF cells); use max-surface ingest or a small `--events` subset for full TS.

Burnett: 74 events / 4 groups; published `Result_data/Validation_results.npz` is (74, 5). HF is TUFLOW `wl_data` (~780k cells; skip 48-step pad). Pair HF/LF via `BurnettRV_event_summary.csv` (plan `p12` → event `E12`). Full TS OOM — default `time_reduction: max`.

---

# Brisbane appendix — Wang et al. (2026) WRR e2025WR042481

Paper: Wang, W., Wang, Q. J., & Nathan, R., *Water Resources Research*, 62, e2025WR042481. DOI: [10.1029/2025WR042481](https://doi.org/10.1029/2025WR042481).

This section lists the **licensed** Lower Brisbane TUFLOW/URBS library. Keep `data/metadata/` and the ingest pipeline; do not treat it as the only case.

## Open Research / Data Availability (paper text)

The Availability Statement says:

- URBS hydrology and TUFLOW hydrodynamics, plus the HF/LF simulation data, are **licensed by the Queensland Government** (Queensland Government, 2017).
- Access is **upon request**: [Brisbane River Catchment Flood Study reports and models](https://www.business.qld.gov.au/industries/mining-energy-water/water/maps-data/modelling/brisbane-river-catchment).
- LSG Python code is cited as Fraehr (2024) [10.26188/24312658](https://doi.org/10.26188/24312658) — that deposit is **Carlisle / Chowilla / Burnett**, not this Lower Brisbane TUFLOW event library.

No Zenodo, HydroShare, Figshare, or GitHub archive of the 51-event HF/LF depth cubes was declared or found (see `metadata/sources.yaml`).

## Paper specifications

| Item | Paper value | Local config |
|------|-------------|--------------|
| HF computational grid | 30 m TUFLOW 1D/2D | `hydrodynamic.hf_cell_size_m: 30` |
| HF output rasters | 15 m (TUFLOW interpolation) | `hf_output_cell_size_m: 15` |
| LF120 | 120 m compute, 60 m output | `data/raw/lf120` |
| LF300 | 300 m compute, 150 m output | `data/raw/lf300` |
| Time step | 2 h (LSG-TS time series) | `timestep_hours: 2` |
| Wet threshold | 0.03 m | `depth_threshold_m` |
| Domain | Wivenhoe Dam → Moreton Bay mouth; ~2000 km² floodplain | `data/metadata/grid_spec.yaml` |
| CRS | not stated | conventional EPSG:28356 (confirm on licensed files) |
| Hydrology | URBS (Seqwater / BRCFS, Aurecon 2015) | licensed |
| Hydrodynamics | TUFLOW (BRCFS, BMT WBM 2016) | licensed |
| Synthetic design events | 47 (FE1–FE47), 11 AEP classes in text; table lists AEP 1-in-2 to 1-in-500 | `metadata/events.csv` |
| Historical LSG events | 1996, 1999, 2011, 2013 (FE48–FE51) | same |
| HF calibration (not all used in LSG) | 1974, 1996, 1999, 2011, 2013 | 1974 not in Appendix A |

### Training / validation (Section 3.3 + Appendix A)

| Split | Count | Event IDs |
|-------|-------|-----------|
| **LSG-TS train** | 8 | FE20, FE22, FE27, FE30, FE32, FE34 (synthetic AEP 1-in-20 to 1-in-100) + FE48 (1999) + FE49 (2011) |
| **LSG-Max train** | 47 | FE1–FE47 except FE21 & FE26, plus FE48 & FE49 |
| **Validation VE1–VE4** | 4 | FE21 (VE1), FE26 (VE2), FE50 (VE3=1996), FE51 (VE4=2013) |
| LSG-TS synthetic-only train | 6 | TS train without 1999/2011 |
| LSG-Max synthetic-only train | 45 | Max train without 1999/2011 |

Machine-readable copies: `metadata/events.csv`, `metadata/splits.yaml`. Paper Table 1 metrics: `metadata/paper_table1_metrics.csv`.

Figure 5 labels **TE1–TE4**; the article does not map those labels onto FE IDs.

## Dataset checklist

| Dataset | Required for paper reproduction | Local path | Status 2026-08-15 | How to get |
|---------|--------------------------------|------------|-------------------|------------|
| HF depth time series / max maps, FE1–FE51 | yes | `data/raw/hf/FE{n}.npz` or `.nc` | **missing** | QLD BRCFS licence + author export |
| LF120 depths, same events | yes | `data/raw/lf120/` | **missing** | same |
| LF300 depths, same events | yes (resolution experiment) | `data/raw/lf300/` | **missing** | same |
| DEM / terrain on HF grid | yes | `data/raw/dem/dem.tif` or `terrain` in NPZ | **missing** | BRCFS LiDAR/bathymetry under same licence |
| URBS hydrographs / dam / tide BC | supporting | not ingested here | **missing** | BRCFS licence |
| TUFLOW control files / mesh | supporting | not ingested here | **missing** | BRCFS licence (AUD 821 USB; email hydrology@detsi.qld.gov.au) |
| Fraehr 2024 LSG code (other catchments) | method reference only | not downloaded | N/A | https://doi.org/10.26188/24312658 |
| SFINCS–LSG Zenodo (Eilander et al.) | **not this paper** | not downloaded | N/A | different model/paper |
| BCC 2011 flood extent polygons | auxiliary only | `data/raw/auxiliary/bcc_2011_flood_extent.geojson` | **downloaded** (~5.4 MB, CC BY 4.0) | BCC Open Data; LGA extent, not TUFLOW depths |
| Synthetic demo cube | CI / smoke tests | `data/synthetic/training_events.npz` | generated on demand | `scripts/generate_synthetic_data.py` |

Expected file list (all `missing` until you drop licensed NPZ/NetCDF in): `metadata/file_manifest.csv`.

## NPZ / NetCDF contract

Paired by **filename stem** (`FE21.npz` ↔ `FE21.npz`). Keys:

- `depth` — `(n_timesteps, n_cells)` or `(n_cells,)` for max-only LSG-Max events
- `terrain` — optional `(n_cells,)` metres AHD
- `shape` — optional `[ny, nx]`

LSG-TS needs full 2-hour time series on the 8 training + 4 validation events. LSG-Max can use per-event maximum surfaces for the 47 training events.

## What was searched (not found)

AGU Open Research page (Availability Statement only); Queensland BRCFS model portal (licence, not download); Queensland Publications (PDFs); University of Melbourne Figshare 10.26188/24312658 and 10.26188/21235782; Zenodo SFINCS–LSG; HydroShare; GitHub; CSIRO DAP. **No public copy of the paper’s TUFLOW HF/LF cubes.**

## After licensed files arrive

1. Copy event files into `data/raw/hf`, `data/raw/lf120`, `data/raw/lf300` using stems FE1–FE51 (zero-padding `FE01` is accepted).
2. Optionally add `data/raw/dem/dem.tif`.
3. From the project root:

```powershell
python scripts/run_lsg_workflow.py --config config/brisbane.yaml
python scripts/run_lsg_workflow.py --config config/brisbane.yaml --lf-resolution lf300
```

The workflow uses Appendix A event IDs when they are present; otherwise it falls back to a random split and says so. Force the demo with `--synthetic`.
