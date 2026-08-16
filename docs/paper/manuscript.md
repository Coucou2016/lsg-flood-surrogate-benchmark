# Does residual hierarchical zoning improve multi-fidelity flood surrogates? A capacity-controlled negative result with oracle error budgets and CRPS-calibrated inundation uncertainty on public benchmarks

**Authors:** [Author names and affiliations to be finalized by the author team before submission]  
**Affiliations:** [To be finalized]  
**Corresponding author:** [To be finalized]

---

## Abstract

Fast flood inundation maps remain costly at high fidelity. Multi-fidelity Low-fidelity–Spatial analysis–Gaussian Process Learning (LSG) maps low-fidelity (LF) fields onto high-fidelity (HF) Empirical Orthogonal Function modes with Sparse Gaussian Process Regression. Residual hierarchical zoning (H-LSG) adds per-zone residual modes intended to localise remaining error. We evaluate that interpretation under matched-capacity controls on three public Figshare cases (Carlisle, Chowilla, Burnett), using a Fraehr-compatible extent-plus-water-surface-elevation stack, an O1–O4 oracle error-budget ladder, and Continuous Ranked Probability Score (CRPS)–scale variance calibration on published Grp1 maximum-inundation folds. Multi-fidelity LSG provides the primary skill where LF is weak (Burnett wet_train CSI 0.853→0.975). Matched-capacity controls show that the apparent H-LSG truncation advantage is not uniquely attributable to localisation and does not improve held-out depth RMSE: Chowilla capacity-matched global wet RMSE is 0.085 m versus 0.093 m for H-LSG (O2−O1 0.002 m versus 0.013 m); Burnett residual capacity narrows O2−O1 but worsens depth RMSE (0.387 m versus 0.179 m) via the LF→HF map, not the shared extent gate. Carlisle Max remains heterogeneous under a training-rank constraint. CRPS-scale calibration helps over-dispersed Carlisle Max posteriors but is null on Chowilla. We contribute a public diagnostic package—oracle attribution, calibrated uncertainty, and capacity controls—and a controlled negative result for residual hierarchical zoning on the evaluated Grp1 maximum-surface setting.

**Keywords:** flood inundation; multi-fidelity surrogate; LSG; empirical orthogonal functions; Gaussian process; model capacity; spatial localisation; uncertainty quantification; model evaluation

---

## 1. Introduction

Flood inundation forecasting and scenario assessment require maps that resolve channels, floodplains, and temporary wet cells at resolutions that full hydrodynamic solvers can deliver only at high cost. Surrogate models trained on paired LF and HF inundation fields offer a route to near-instant prediction once HF training events exist, without re-running the HF solver for every new boundary condition.

LSG couples an LF hydrodynamic field to an HF EOF basis through SGPR on expansion coefficients (ECs), recovering HF-like depth or water-surface maps from cheap LF runs (Fraehr et al., 2022, 2023a). Subsequent work compared LSG with machine-learning surrogates on public Carlisle, Chowilla, and Burnett cubes (Fraehr et al., 2024a) and examined strategies for large floodplain applications, including LSG time-series (LSG-TS) versus maximum-surface (LSG-Max) training (Wang et al., 2026). Wang et al. (2026) explicitly name zonal EOF analysis as future work rather than a completed component of that study.

Three practical gaps remain for methods-oriented reuse. First, spatial localization of EOF energy has been pursued in adjacent lines—rotated EOF with Sparse GP (REOF–SGP; Wang et al., 2025), regionalized LSG focus subdomains (Tan et al., 2025), and satellite REOF forecasting (FIER and watershed mosaicking; Chang et al., 2020, 2023; Markert et al., 2026)—yet whether a simultaneous whole-domain residual hierarchical decomposition (global modes plus residual zonal EOFs) actually improves multi-fidelity hydrodynamic LSG, once the extra parameters it introduces are controlled for, has not been tested on public data; localised variants add capacity (more retained modes, wider GP inputs) that a fair evaluation must match before crediting localisation. Second, error attribution in LSG is often summarized by end-to-end CSI/RMSE; Tan et al. (2025) introduce a two-part split, yet a staged counterfactual ladder that isolates truncation, LF expressibility, and GP mapping on the same dual EXT+WSE path is still needed for diagnosis. Third, probabilistic flood surrogates exist outside LSG (Donnelly et al., 2022; López-Lopera et al., 2022; Kohanpur et al., 2023; Siripatana et al., 2025; Zanchetta and Coulibaly, 2022), but calibrated propagation of LSG GP posteriors to inundation probability and depth CRPS, with an explicit variance scale that leaves point CSI/RMSE unchanged, remains underexplored.

This paper therefore evaluates residual hierarchical LSG under fair capacity controls, embedded in a diagnostic and probabilistic methods contribution. We ask four research questions. **RQ1 (capacity-controlled localisation):** When the global EOF baseline is matched to H-LSG in total GP-input dimension (and, conversely, H-LSG is stripped of its residual modes), does the apparent zoning benefit in the truncation gap O2−O1 and in held-out depth skill survive? **RQ2 (attribution):** Using O1–O4 oracles, where is remaining depth error concentrated—truncation, LF expressibility, or the LF→HF GP map—and does that localise the Burnett failure of H-LSG? **RQ3 (UQ):** Does CRPS-scale variance calibration improve probabilistic scores without changing CSI/RMSE, and where does it fail? **RQ4 (boundary):** When does strong LF extent create a scoring-domain sensitivity under all-cells evaluation, and how should protocols be reported?

We implement Fraehr-compatible EXT+WSE reconstruction, residual *k*-means H-LSG on the WSE branch, an SGPR inducing-point floor required for stable Max-path mapping, O1–O4 dual-path budgets, and CRPS-scale uncertainty calibration. Evaluation uses the three public Fraehr (2024) cases together with capacity-matched controls, an inducing-point sweep, a zone-count sweep, and a Burnett oracle attribution. The remainder of the paper presents Methods, datasets, experimental design, results, discussion, and limitations.

---

## 2. Related work and novelty boundary

### 2.1 Multi-fidelity LSG lineage

Fraehr et al. (2022) introduced LSG for upskilling LF hydrodynamic flood models via EOF compression and Sparse GPs. Fraehr et al. (2023a) developed hybrid floodplain formulations separating extent-like and water-surface information. Nature Water commentary framed LSG as a route to “supercharging” inundation models (Fraehr et al., 2023b). Fraehr et al. (2024a) benchmarked LSG against four state-of-the-art surrogates (**1dCNN**, **LSTM-SRR**, **GP-EOF**, **LSTM-EOF**) on the public Carlisle, Chowilla, and Burnett cubes used here, using leave-one-group-out cross-validation, wet-train scoring, CSI for extent, and peak/hydrograph depth metrics, including 50%-larger extrapolation tests. Fraehr et al. (2024b) introduced LESS (low-fidelity event selection) to choose a minimal HF training-event set from LF candidates—orthogonal to our question of residual EOF *capacity* once a split is fixed. Wang et al. (2026) extended LSG strategies for large complex floodplains and retained zonal EOF as future work. Lu et al. (2025) studied GP kernel choice within LSG. Public data and companion code are deposited at Figshare DOI 10.26188/24312658 (Fraehr, 2024).

### 2.2 Localization and regionalization near LSG

Tan et al. (2025) regionalize LSG training on focus subdomains and report a two-component error decomposition (downscaling versus LSG mapping). Wang et al. (2025) combine rotated EOF with Sparse GP for LF→HF hydrodynamic mapping. Satellite FIER and watershed-mosaic REOF systems partition space for extent forecasting (Chang et al., 2020, 2023; Wan et al., 2025; Markert et al., 2026). SFINCS–LSG abstracts discuss EOF compression in compound coastal settings (Eilander et al., 2025, 2026a), with accompanying open scripts and data on Zenodo (Eilander et al., 2026b). These works constrain novelty: this paper does **not** claim the first localized EOF flood model, the first LSG error split, or the first probabilistic flood surrogate. Relative to Fraehr et al. (2024b), we do not re-select training events; LESS and capacity-matched zoning answer different budget questions.

### 2.3 Probabilistic inundation surrogates and evaluation practice

Gaussian-process and related probabilistic emulators for flood depth or coastal inundation appear in Donnelly et al. (2022), López-Lopera et al. (2022), Kohanpur et al. (2023), Siripatana et al. (2025), and Zanchetta and Coulibaly (2022). Our claim is narrower: CRPS-calibrated LSG GP posterior variance propagated to dual-field depth maps and inundation probabilities on public multi-fidelity LSG cases. More generally, evaluating environmental models benefits from combining visual diagnostics, quantitative criteria, and purpose-dependent testing (Bennett et al., 2013); the present capacity controls and oracle ladder are intended in that spirit.

### 2.4 Defensible novelty statement

We contribute a reproducible, public-data diagnostic and probabilistic methods package for multi-fidelity LSG, and—centrally—a capacity-controlled negative result for residual hierarchical zoning. Using matched-capacity controls (equal total GP-input dimension for the global EOF baseline versus H-LSG), an inducing-point sweep, and a zone-count sweep, we show that the apparent H-LSG advantage in the truncation gap O2−O1 is largely reproduced by simply increasing the global mode count and does not translate into held-out depth-RMSE skill once capacity is matched: on Chowilla a capacity-matched global model attains lower wet RMSE (0.085 m versus 0.093 m) and smaller O2−O1 (0.002 m versus 0.013 m) than H-LSG, while on Burnett residual capacity worsens operational RMSE through the LF→HF GP map (O4−O2 0.304 m versus 0.056 m), not the shared extent gate. The defensible contributions are therefore the diagnostic apparatus itself (a Fraehr-compatible EXT+WSE stack, an O1–O4 oracle error-budget ladder, and CRPS-scale calibrated GP inundation uncertainty), the demonstration that multi-fidelity LSG—not zoning—carries the skill, and an honest, controlled negative result for residual localisation. We do **not** claim the first localized EOF flood model, the first LSG error split, the first probabilistic flood surrogate, or that residual hierarchical zoning improves holdout inundation skill.

---

## 3. Methods

### 3.1 Problem formulation

Let **h**<sup>HF</sup> ∈ ℝ<sup>*n*</sup> and **h**<sup>LF→HF</sup> ∈ ℝ<sup>*n*</sup> denote HF depth and LF depth interpolated to the HF mesh for one event (or timestep). Wet cells are those with depth ≥ τ, with τ = 0.03 m throughout. Always-flooded (AF) and temporary-flooded (TF) masks follow Fraehr-style cell categories. The surrogate learns a map from LF fields to HF-like depth without calling the HF solver at prediction time.

### 3.2 Dual-field EXT+WSE reconstruction

Following Fraehr et al. (2023a), the operational field mode `wse_ext` fits two emulators:

1. **EXT** — binary wet/dry on TF cells (AF forced wet), reconstructed by EOF+GP.  
2. **WSE** — water-surface elevation on wet cells, reconstructed by EOF+GP.

Combination into depth uses terrain elevation *Z*:

> **WSE′** = WSE if EXT = 1; **WSE′** = *Z* if EXT = 0;  
> *h* = max(WSE′ − *Z*, 0),

with depths below τ set to dry. This is **not** an LF-extent post-gate on a depth-only prediction; EXT is learned jointly with WSE.

### 3.3 Global LSG and residual hierarchical LSG (H-LSG)

**Global path.** HF training fields on the retained wet index are compressed by EOF. LF fields projected onto HF modes yield pseudo-ECs. One SGPR per mode maps LF pseudo-ECs to HF ECs. Reconstruction inverts the EOF expansion (plus Tobit-style thresholding for operational maps).

**Residual hierarchical path.** Hard partitions of the full water surface create boundary jumps. H-LSG keeps basin-scale global modes and lets zones model residuals only:

> **h** = Φ<sub>global</sub> **c**<sub>global</sub> + Σ<sub>*z*</sub> **1**<sub>*z*</sub> Φ<sub>*z*</sub><sup>res</sup> **c**<sub>*z*</sub>.

Zone labels use `residual_kmeans` on per-cell residual magnitude (optional XY). Residual ECs stack into the same LF→HF GP as global ECs. Under `wse_ext`, residual zones attach to the **WSE** branch only; binary EXT remains global so zone labels do not fragment the extent field. Because each zone contributes `residual_eof_modes` additional ECs, H-LSG raises the total WSE GP input dimension from *k*<sub>global</sub> to *k*<sub>global</sub> + *n*<sub>zones</sub> × `residual_eof_modes` (for example, 3 → 15 on Chowilla, 6 → 18 on Burnett). Any comparison of H-LSG to a global baseline therefore confounds *localisation* with *capacity*; Section 5 introduces matched-capacity controls that hold this input dimension fixed, and Section 6.8 reports the result.

### 3.4 Sparse GP regression and inducing-point floor

Each mode uses SGPR (GPflow) or a NumPy RBF GP fallback. For LSG-Max, the number of training events can be small (Carlisle Grp1: 8 events). A small default inducing fraction then yields too few inducing points relative to the expanded H-LSG GP input dimension (global plus residual ECs), so that the sparse approximation cannot represent the LF→HF map and Max-path O4/RMSE degrade. The implementation therefore initialises inducing points from training rows and floors the inducing budget at a configurable minimum (capped at *n*<sub>train</sub>). This is treated as a robustness requirement, not a novelty claim; Section 6.8 reports sensitivity of wet RMSE to that budget.

### 3.5 Posterior variance, inundation probability, and CRPS-scale calibration

GP predictive variance on ECs is mapped through the linear EOF reconstruction and inflated by a cell-wise residual/truncation term, yielding latent depth *Z* ∼ 𝒩(μ, σ²). Observation uses Type-I left censoring (Tobit):

> *h* = 0 if *Z* < τ; *h* = *Z* if *Z* ≥ τ.

Inundation probability is

> *P*(*h* ≥ τ) = *P*(*Z* ≥ τ) = 1 − Φ((τ − μ) / σ).

Uncalibrated intervals can be over-dispersed (Carlisle Max `coverage_90` ≈ 0.996). A single global scale is fit on train by minimising mean Gaussian CRPS:

> Var<sub>cal</sub> = *s* · Var<sub>raw</sub>,

with latent mean unchanged. Unchanged CSI/RMSE after calibration is therefore **by construction** (mean maps are untouched), not an independent empirical finding that calibration “preserves accuracy.” The scientific claim is improved probabilistic scores (CRPS, coverage) on held-out scoring of variance-rescaled maps, with *s* fit on **training** events only. We also report `coverage_*_active` on cells where observation or predictive mean ≥ τ, because all-cell coverage is inflated by EXT-dry zeros with near-zero σ. Under `wse_ext`, EXT remains a learned binary/extent field that gates continuous WSE; scalar *s* primarily recalibrates continuous depth variance on that gated path rather than a fully free inundation-probability model. Nested leave-one-train-event CV for *s* is reported for Chowilla and Carlisle Max (Section 6.8); Burnett nested CV is outside the present scope.

Closed-form Gaussian CRPS follows Gneiting and Raftery (2007):

> CRPS(*N*(μ, σ²), *y*) = σ [ *z* (2Φ(*z*) − 1) + 2φ(*z*) − 1/√π ], *z* = (*y* − μ) / σ.

### 3.6 O1–O4 oracle error ladder

On the dual EXT+WSE path, matched oracles are combined with production gating into clipped depth RMSE on the protocol wet index. Because EXT gating, WSE reconstruction, clipping, and GP mapping are nonlinear, these stages are a **counterfactual attribution ladder**, not an additive variance decomposition with unique shares of total error. Differences such as O2−O1 should be read as path-ordered contrasts under the fixed production combination rule.

| Stage | Inputs | Interpretation |
|-------|--------|----------------|
| **O1** | HF true ECs, full training-rank modes | Numerical SVD floor |
| **O2** | HF true ECs, truncated to \(k\) modes | EOF truncation / out-of-subspace expressibility |
| **O3** | LF pseudo-ECs, no GP | LF expressibility in the HF subspace |
| **O4** | Full LSG (GP + \(k\) modes) | Total surrogate error (mirrors `predict_dual_depth`) |

The gap O2−O1 quantifies the incremental contrast associated with truncation (or held-out out-of-subspace energy) along this ordering; O3−O2 with LF projection limits; O4−O3 with GP mapping. Because reconstruction, clipping, extent gating, and GP mapping are nonlinear, these contrasts are path-ordered diagnostics rather than order-invariant causal shares. Train and test budgets are reported separately: for LSG-Max with full-rank training (Wang et al., 2026 retained 47 ECs for 47 events), in-sample O2−O1 can be near zero while test O2−O1 remains informative.

### 3.7 Metrics and scoring masks

Binary inundation metrics use τ = 0.03 m (Wang et al., 2026 binary inundation threshold; Fraehr Categories wet indexing): Probability of Detection (POD), Rate of False Alarms (RFA), and CSI. Depth skill uses RMSE (m). **all_cells** scores the full HF mesh; **wet_train** scores Fraehr category wet indices used in training—the same “cells flooded in training” restriction emphasised by Fraehr et al. (2024a). We distinguish **time-series** scores (`ts_*` for LSG-TS over timesteps) from **max-surface** scores (event maximum depth). Unless noted, headline CSI/RMSE for LSG-Max and for LSG-TS “max surface” refer to maximum inundation surfaces. Probabilistic scores include CRPS, Brier score, PIT mean on wet cells, and coverage at 50%/90%.

**Protocol alignment with Fraehr et al. (2024a).** Matches: public Carlisle/Chowilla/Burnett cubes; CSI definition; wet-train scoring mask; group-structured event sets. Differs (stated explicitly, no silent retuning of our numbers): (i) we report the published **Grp1** fold rather than mean±std over full leave-one-group-out; (ii) headline depth skill is **RMSE** on Max (or TS) surfaces, not their AvgPeakDiff / R² / AvgRMSE / FI suite; (iii) we do not re-implement 1dCNN / LSTM-SRR / GP-EOF / LSTM-EOF or their 50% extrapolation battery. Carlisle LSG-Max wet_train CSI 0.976 under Grp1 is therefore comparable in *spirit* to their high LSG CSI on Carlisle, not a cell-wise reprint of their pooled Table 2 (LSG CSI 0.95±0.05 across sites/folds).

### 3.8 Statistical reporting note

This study evaluates deterministic and probabilistic scores on fixed published event splits (Grp1), not biological replicates. The independent evaluation unit is the **hold-out event** (or event set) under each case’s Fraehr/Wang-style split protocol—not the raster cell. We report effect sizes (CSI, RMSE, CRPS, O1–O4 RMSE) without inventing \(p\)-values. Cell counts enter contingency tables but are not treated as independent experimental replicates for inferential tests.

**Hold-out sizes for headline Max summaries:** Carlisle Grp1 Max test *N*<sub>event</sub> = 1 (E1); Chowilla Grp1 Max test *N*<sub>event</sub> = 1 (E1); Burnett Grp1 Max test *N*<sub>event</sub> = 18. Carlisle LSG-TS reports many timesteps on the held-out event, but Max-surface skill for Carlisle/Chowilla remains a single-event contrast under Grp1 and must not be over-generalised.

**Software stack.** Headline Max runs used Python 3.12 with NumPy/SciPy/scikit-learn, h5py, and a GPflow SGPR backend (TensorFlow). Host memory constrained Chowilla/Burnett full time-series folds (Section 8); package versions are pinned in the public repository environment file.

**Emulation target.** Metrics compare surrogate maps to **HF hydrodynamic fields** (perfect-prognosis style), not to independent remote-sensing flood observations.

---

## 4. Public datasets and case studies

Public multi-fidelity cubes are from Fraehr (2024), DOI [10.26188/24312658](https://doi.org/10.26188/24312658) (CC BY 4.0). Solver brand is irrelevant to LSG; paired HF/LF fields are ingested without re-running hydrodynamics.

**Table 1. Case inventory (public benchmarks used in this study).**

| Case | HF / LF solvers | HF scale (order) | Events / Grp1 split used | Time reduction |
|------|-----------------|------------------|--------------------------|----------------|
| Carlisle (primary) | LISFLOOD-FP × HEC-RAS | ~5.8×10⁵ cells | E1–E9; train E2–E9, test E1 | Full TS + Max |
| Chowilla (secondary) | fine/coarse HEC-RAS | ~1.1×10⁵ cells | 29 events; train 28, test E1 | Max surfaces |
| Burnett (tertiary) | TUFLOW × HEC-RAS | ~7.8×10⁵ cells | 74 events; train 56, test 18 | Max surfaces |

Headline Chowilla and Burnett results use maximum-inundation surfaces because full time-series Grp1 folds exceed the computational memory budget available for this study (Burnett in-memory HF stack ≈199 GB versus ≈128 GB RAM; Chowilla dual EXT+WSE with uncertainty quantification is similarly constrained). Brisbane TUFLOW/URBS (Wang et al., 2026) is licence-gated and is therefore outside the public, redistributable evidence base of this paper. Other external multi-fidelity benchmarks (e.g. FloodCastBench) are left for future capacity-controlled replication.

---

## 5. Experimental design

1. **Field mode:** Dual-path EXT+WSE (`wse_ext`) for all headline runs.  
2. **Zoning:** Residual hierarchical LSG with residual-response *k*-means partitions by default; global baselines omit zoning. A Chowilla wet-correlation partitioning sensitivity is reported alongside residual *k*-means.  
3. **Capacity controls (RQ1).** To separate localisation from capacity we run matched-capacity contrasts under identical folds and field mode. (i) **Matched global up:** global EOF with the mode count forced to the H-LSG WSE GP input dimension where feasible (Chowilla 15; Burnett 18; Carlisle requested 13, realised 8 under the Max train-rank cap). (ii) **Matched H-LSG down:** residual EOF modes set to zero so zones are built but contribute no residual ECs, collapsing H-LSG to the global input dimension. (iii) **Inducing-point sweep** (minimum inducing points ∈ {2, 8, 16, 28}) and **zone-count sweep** (*n*<sub>zones</sub> ∈ {2, 4, 6}) on Chowilla H-LSG, to test whether SGPR approximation budget or EC count—not localisation—drives the observed RMSE and O2−O1. A Burnett oracle attribution isolates whether the H-LSG RMSE loss originates in the extent gate or the WSE GP map.  
4. **Folds:** Fraehr ValidateOnGrp_1 / Wang-style group hold-out protocol as recorded in the published splits.  
5. **Baselines:** LF only (WSE→DEM clip on HF mesh); global LSG at native and matched capacity; H-LSG after the SGPR inducing-point floor.  
6. **Diagnostics:** O1–O4 dual-path error budgets; CRPS-scale variance calibration (Carlisle from the calibrated workflow; Chowilla/Burnett from independent rescores of saved states); nested leave-one-train-event CV for the CRPS scale *s* on Chowilla and Carlisle; Carlisle residual-zone spatial coherence via 8-nearest-neighbour same-zone fraction.  

Machine-readable workflow summaries and figure exports are archived with the public code repository (Section 10).

---

## 6. Results

Results follow the Fraehr/Wang visual-first convention: study domains and inundation maps precede aggregate metric tables. Gauge hydrographs are not shown because the exported prediction examples for Carlisle, Chowilla, and Burnett store maximum-surface peak fields only; inventing time-series panels would misrepresent the available evidence (Section 8).

### 6.1 Study domains

**Figure 1** shows HF cell centres for Carlisle, Chowilla, and Burnett side by side. No DEM/bathymetry raster is available in the public geometry packages used here, so the panels are honest cell-scatter domain maps (equal aspect; easting/northing). They orient the subsequent extent and error maps.

### 6.2 Inundation extent maps (hit / miss / false alarm)

**Figure 2** compares LF and LSG-Max against HF at τ = 0.03 m using Fraehr/Wang categorical colours: blue = hit (both wet), red = miss (HF wet only), gold = false alarm (pred wet only), light gray = both dry. Burnett shows the clearest LF→LSG cleaning of misses/false alarms, consistent with the large CSI lift in Table 2. Carlisle differences are subtler (already-strong LF extent). Chowilla’s wet-mask / all-cells tension (Section 6.9) is visible as extent disagreements outside the Fraehr Categories wet index.

### 6.3 Peak-depth error maps

**Figure 3** maps LF−HF and LSG-Max−HF peak depths with a diverging red/blue scale (red = overestimate). These panels make the multi-fidelity depth correction spatially legible before any bar chart: Burnett and Chowilla exhibit large LF errors that LSG shrinks; Carlisle residuals are smaller.

### 6.4 Probabilistic P(wet) maps

**Figure 4** shows cell-wise inundation probability *P*(wet) = *P*(*h* ≥ 0.03 m) from the LSG-Max GP posterior. Placed **after** deterministic extent/error maps as a probabilistic complement to the categorical extent panels.

### 6.5 Point skill across cases (wet_train and all_cells)

**Table 2. Headline CSI and RMSE on Grp1 folds (threshold 0.03 m).** Values rounded from workflow JSON; wet_train is the Fraehr-style protocol mask. These are **our** Grp1 workflow scores—not Fraehr et al. (2024a) pooled mean±std (their Table 2).

| Case | Model | CSI all_cells | CSI wet_train | RMSE all (m) | RMSE wet_train (m) |
|------|-------|--------------:|--------------:|-------------:|-------------------:|
| Carlisle | LF only | 0.960 | 0.966 | 0.074 | 0.101 |
| Carlisle | LSG-TS (max surface) | 0.970 | 0.970 | 0.099 | 0.154 |
| Carlisle | LSG-Max H-LSG | 0.976 | 0.976 | 0.061 | 0.094 |
| Chowilla | LF only | 0.930 | 0.925 | 0.690 | 0.690 |
| Chowilla | LSG-Max H-LSG | 0.390 | 0.976 | 3.789 | 0.093 |
| Chowilla | LSG-Max global | 0.390 | 0.974 | 3.789 | 0.088 |
| Burnett | LF only | 0.853 | 0.853 | 0.983 | 0.989 |
| Burnett | LSG-Max H-LSG | 0.975 | 0.975 | 0.384 | 0.387 |
| Burnett | LSG-Max global | 0.975 | 0.975 | 0.179 | 0.179 |

**Figure 5** summarises wet_train CSI and RMSE across cases. Burnett shows a clear multi-fidelity lift (CSI 0.853→0.975; RMSE 0.989→0.387 m). Carlisle already has strong LF extent (CSI 0.966 wet_train); LSG-Max still improves CSI to 0.976 and cuts wet_train RMSE from 0.101 m to 0.094 m. Chowilla wet_train LSG-Max CSI (0.976) exceeds LF (0.925) and collapses depth RMSE from 0.690 m to 0.093 m, even though all-cell CSI collapses (Section 6.9).

For Carlisle LSG-TS, **time-series** scores on the held-out event are CSI 0.959 and RMSE 0.065 m (`ts_*`), while the **max surface** derived from the TS model matches Table 2 (CSI 0.970; RMSE 0.099 m all_cells). These quantities must not be conflated.

### 6.6 O1–O4 error budgets

**Table 3. Test-split dual-path O1–O4 depth RMSE (m) on protocol wet index.**

| Case | Variant | O1 | O2 | O3 | O4 | O2−O1 |
|------|---------|---:|---:|---:|---:|------:|
| Carlisle | LSG-TS H-LSG | 0.018 | 0.033 | 0.240 | 0.102 | 0.015 |
| Carlisle | LSG-Max H-LSG | 0.048 | 0.052 | 0.068 | 0.094 | 0.005 |
| Chowilla | LSG-Max H-LSG | 0.020 | 0.034 | 0.701 | 0.093 | 0.013 |
| Chowilla | LSG-Max global | 0.020 | 0.078 | 0.666 | 0.088 | 0.057 |
| Burnett | LSG-Max H-LSG | 0.074 | 0.083 | 0.668 | 0.387 | 0.009 |
| Burnett | LSG-Max global | 0.074 | 0.123 | 0.708 | 0.179 | 0.049 |

**Figure 6** shows the ladder structure. On Carlisle Max, O3 and O4 remain close (0.068 vs 0.094 m), indicating that after truncation the GP mapping is not the dominant failure. On Chowilla and Burnett Max, O3 is large (≈0.67–0.70 m) relative to O2, so LF expressibility in the HF subspace dominates before GP mapping; O4 then recovers substantially on Chowilla wet_train (0.093 m) via learned EXT+WSE mapping, while Burnett H-LSG O4 remains 0.387 m—still far below LF-only RMSE (0.989 m wet_train) but leaving residual depth error. Burnett global O4 is lower (0.179 m) with a larger truncation gap (Section 6.7).

### 6.7 Global versus residual H-LSG

**Figure 7** contrasts global (no zoning) versus residual H-LSG on Chowilla and Burnett Max Grp1 at their **native** capacities (WSE GP input dimension 3 vs 15 on Chowilla, 6 vs 18 on Burnett). On Chowilla, wet_train CSI is essentially flat (0.974 global vs 0.976 H-LSG); wet_train RMSE is already slightly lower for global (0.088 m) than H-LSG (0.093 m). The truncation gap O2−O1 appears smaller for H-LSG: **0.057** (global) versus **0.013** (H-LSG). On Burnett, wet_train CSI is likewise flat (0.975 both), O2−O1 shrinks from **0.049** (global) to **0.009** (H-LSG), yet Burnett global wet_train RMSE (0.179 m) is far lower than H-LSG (0.387 m). Read on their own, these native-capacity contrasts might be taken to credit localisation with the O2−O1 reduction. Section 6.8 shows this reading does not survive once the global baseline is granted the same EC budget as H-LSG: the O2−O1 reduction is not uniquely attributable to localisation, and it buys no held-out depth skill.

### 6.8 Capacity-matched controls: the localisation claim does not survive (RQ1)

The native-capacity contrasts of Section 6.8 confound localisation with capacity, because H-LSG feeds more ECs into the WSE GP than the global baseline. We remove that confound by holding the GP input dimension fixed.

**Chowilla equal-capacity.** Table 6 matches the global EOF baseline to the H-LSG input dimension (15) by forcing the retained mode count, and conversely disables the H-LSG residual modes. Given the same 15 ECs, the **global** model attains the **lowest** wet RMSE (0.085 m, versus 0.093 m for H-LSG and 0.088 m for the native 3-mode global) and the **smallest** truncation gap O2−O1 (0.002 m, versus 0.013 m for H-LSG and 0.057 m for the native global). Disabling residual modes collapses H-LSG exactly onto the native global baseline (RMSE 0.088 m; O2−O1 0.057 m). The apparent O2−O1 shrinkage credited to zoning in Section 6.8 is therefore reproduced—and exceeded—by simply retaining more global modes, and once capacity is matched, zoning yields **no** wet-RMSE advantage.

**Table 6. Chowilla equal-capacity control (Grp1 Max, wet_train).** WSE dimension is the total EC count entering the WSE GP.

| Model | WSE dim | CSI | RMSE (m) | test O2−O1 (m) |
|-------|--------:|----:|---------:|---------------:|
| Global (native) | 3 | 0.974 | 0.088 | 0.057 |
| H-LSG residual *k*-means | 15 | 0.976 | 0.093 | 0.013 |
| **Global matched-15** | **15** | 0.975 | **0.085** | **0.002** |
| H-LSG residual modes = 0 | 3 | 0.974 | 0.088 | 0.057 |

**Burnett equal-capacity and error attribution.** Table 7 repeats the control at dimension 18 and adds an oracle decomposition. Extra capacity—whether supplied by the H-LSG residual stack or by a matched-18 global model—**narrows O2−O1 but worsens** operational wet RMSE relative to the native 6-mode global (0.179 m): H-LSG reaches 0.387 m and matched-18 global 0.416 m. The failure is localised by the oracle ladder: the extent gate is identical in both models (EXT cell agreement 0.986; equal gate miss/false-alarm fractions), so it is **not** an extent-gate story; instead the gap opens in the LF→HF GP mapping, where H-LSG’s O4−O2 (0.304 m) is ~5.5× the global value (0.056 m) and its training O4 (0.360 m) already triples the global (0.115 m). Residual EC capacity increases expressibility but degrades the LF→HF GP map on Burnett, and the matched-capacity global reproduces the same pathology under pure capacity.

**Table 7. Burnett equal-capacity control and oracle attribution (Grp1 Max, wet_train / test split).**

| Model | WSE dim | CSI | RMSE (m) | test O2−O1 (m) | test O4−O2 (m) | EXT agree |
|-------|--------:|----:|---------:|---------------:|---------------:|----------:|
| Global (native) | 6 | 0.975 | **0.179** | 0.049 | **0.056** | 0.986 |
| H-LSG residual *k*-means | 18 | 0.975 | 0.387 | 0.009 | **0.304** | 0.986 |
| Global matched-18 | 18 | 0.972 | 0.416 | 0.004 | — | 0.986 |

**Inducing-point and zone-count confounds.** Two nuisance factors move RMSE as much as zoning does. On Chowilla H-LSG (15-D WSE input), the SGPR inducing budget dominates depth RMSE while leaving O2−O1 unchanged: RMSE is 0.244 m at *m* = 2, 0.096 m at *m* = 8, 0.093 m at *m* = 16 (default), and 0.073 m at *m* = 28 (= *n*<sub>train</sub>), whereas the 3-D global tolerates *m* = 2 (RMSE 0.085 m). A low-*m* H-LSG collapse can thus be misread as “zoning hurts.” Separately, increasing the zone count from 2 to 6 monotonically shrinks O2−O1 (0.019 → 0.012 m) but **worsens** wet RMSE (0.087 → 0.103 m), because more zones add EC capacity that the GP map cannot exploit—again decoupling the O2−O1 diagnostic from operational skill. Both sweeps are consistent with a capacity/approximation account rather than a localisation account (Table 8).

**Table 8. Chowilla H-LSG inducing-point and zone-count sweeps (Grp1 Max, wet_train).**

| Factor | Setting | WSE dim | CSI | RMSE (m) | test O2−O1 (m) |
|--------|---------|--------:|----:|---------:|---------------:|
| Inducing-point floor | 2 | 15 | 0.947 | 0.244 | 0.013 |
| | 8 | 15 | 0.990 | 0.096 | 0.013 |
| | 16 (default) | 15 | 0.976 | 0.093 | 0.013 |
| | 28 (= *n*<sub>train</sub>) | 15 | 0.983 | 0.073 | 0.013 |
| Zone count | 2 | 9 | 0.975 | 0.087 | 0.019 |
| | 4 (default) | 15 | 0.976 | 0.093 | 0.013 |
| | 6 | 21 | 0.975 | 0.103 | 0.012 |

**CRPS scale is fold-stable (methodology check).** A residual concern for the UQ result is whether the CRPS variance scale *s*, fit on training events, is a fragile single-draw artefact when the official test fold has one event. On Chowilla Max H-LSG, 8-fold leave-one-train-event-out CV gives *s* = 0.310 ± 0.007 (range 0.298–0.324) around the full-train value 0.309. On Carlisle Max H-LSG the same protocol gives *s* = 0.418 ± 0.031 around the full-train value 0.417. Fold stability does not claim calibration is useful everywhere—Section 6.10 reports flat CRPS and adverse coverage on Chowilla—only that those null/adverse outcomes are not caused by an unstable *s* estimator. Burnett nested CV is not required for the localisation claim and is left outside the present scope.

**Carlisle equal-capacity (third-site control).** Table 9 repeats the matched-capacity protocol on Carlisle Max. H-LSG uses WSE dim 13 (1 global + 4×3 residual), but with only eight Max training events a global-only EOF cannot realise 13 modes: requesting 13 modes is capped at realised dim **8** (full train rank). Maxing global capacity clears O2−O1 (0.000 m) yet **worsens** wet RMSE (0.202 m) relative to native global (0.112 m) and H-LSG (0.094 m). Disabling residual modes again collapses H-LSG onto the native global baseline. Carlisle therefore does **not** reproduce the Chowilla “matched global beats H-LSG” pattern: residual EC stacking improves depth RMSE here while pure global capacity does not. We report this as site heterogeneity under a hard Max-rank constraint, not as a general rescue of residual localisation—Chowilla and Burnett remain the capacity-matched counter-examples where extra residual capacity fails to improve (and can degrade) held-out depth skill.

**Table 9. Carlisle equal-capacity control (Grp1 Max, wet_train).** Realised WSE dim for the matched global is capped by *n*<sub>train</sub> = 8.

| Model | Requested / realised WSE dim | CSI | RMSE (m) | test O2−O1 (m) |
|-------|------------------------------|----:|---------:|---------------:|
| Global (native) | auto / 1 | 0.976 | 0.112 | 0.064 |
| H-LSG residual *k*-means | — / 13 | 0.976 | **0.094** | 0.005 |
| Global forced to 13 modes | 13 / **8** | 0.975 | 0.202 | **0.000** |
| H-LSG residual modes = 0 | — / 1 | 0.976 | 0.112 | 0.064 |
### 6.9 Chowilla scoring-domain sensitivity

Under all_cells, Chowilla LSG-Max CSI is 0.390 with RMSE 3.789 m for both H-LSG and global, because many HF-wet cells outside the train wet mask are scored as misses when EXT training focuses on Fraehr wet categories. Under wet_train, CSI is 0.976 (H-LSG) with RMSE 0.093 m. LF only remains high on all_cells CSI (0.930) because the coarse LF already floods a large footprint. This contrast is a **result about scoring protocol**, not evidence that LSG “fails” Chowilla under Fraehr wet_train reporting. **Figure 2** (Chowilla panels) visualises the spatial pattern for event E1.

### 6.10 CRPS-scale uncertainty calibration

**Table 4. Variance calibration (CRPS scale) and selected probabilistic scores.** Carlisle values are from the calibrated Max workflow summary. Chowilla/Burnett before→after pairs are from independent rescores of saved H-LSG states; the workflow-fit variance scale on the original Max summaries was 0.309 (Chowilla) and 0.606 (Burnett).

| Case / surface | *s* | CRPS (uncal. → cal.) | Active cov90 (uncal. → cal.) | Point CSI/RMSE |
|----------------|----:|----------------------|------------------------------|----------------|
| Carlisle Max | 0.417 | 0.039 → 0.028 | 0.990 → 0.966 | Unchanged (CSI 0.976; RMSE 0.061 m all_cells) |
| Carlisle TS | 0.900 | ≈0.0165 (near-calibrated) | — | Unchanged |
| Chowilla H-LSG Max (rescore) | 0.419 | 2.155 → 2.155 | 0.334 → 0.287 | Unchanged by construction (CSI 0.976; RMSE 0.093 m wet_train) |
| Burnett H-LSG Max (rescore) | 0.604 | 0.133 → 0.127 | 0.943 → 0.890 | Unchanged (CSI 0.975; RMSE 0.387 m wet_train) |

On Carlisle Max, active 90% coverage moves closer to nominal after shrinking over-wide intervals. **Figure 8** includes Chowilla/Burnett before/after CRPS. On Burnett, CRPS falls and active coverage moves toward 0.90. On Chowilla Grp1 Max the same CRPS-scale protocol yields essentially **flat CRPS** (2.155 → 2.155) while coverage moves **away** from nominal—report this as a negative/null calibration outcome on that fold, not as a silent success. Prefer active-cell coverage over all-cell coverage when EXT-dry zeros dominate.

### 6.11 Chowilla wet-correlation zoning sensitivity

**Figure 9** and **Table 5** compare Chowilla Max Grp1 under global, residual *k*-means, and wet-correlation zoning. Wet_train CSI rises slightly under wet-correlation (0.978) versus H-LSG (0.976) and global (0.974), with O2−O1 = 0.010—still a small CSI delta relative to the LF→LSG lift. This is a single-fold sensitivity, not a claim that correlation zoning dominates residual *k*-means.

**Table 5. Chowilla Max Grp1 wet_train zoning sensitivity (LSG-Max).**

| Zoning | CSI wet_train | RMSE wet_train (m) | test O2−O1 (m) |
|--------|--------------:|-------------------:|---------------:|
| global (none) | 0.974 | 0.088 | 0.057 |
| residual *k*-means | 0.976 | 0.093 | 0.013 |
| wet-correlation | 0.978 | 0.094 | 0.010 |


## 7. Discussion

### 7.1 Central advance

The central advance is twofold: a **diagnostic and probabilistic methods package** for multi-fidelity LSG on public data—O1–O4 attribution and CRPS-calibrated map uncertainty—and a **capacity-controlled evaluation** of residual hierarchical zoning. Rather than presenting localisation as an accuracy win, we test that reading under matched capacity. On Chowilla and Burnett the apparent O2−O1 zoning benefit is reproduced or exceeded by capacity-matched global models and does not translate into held-out depth-RMSE gains; on Carlisle Max, residual stacking can still improve RMSE when global SVD is rank-capped by *n*<sub>train</sub>. Reporting the controls—including this heterogeneity—is the methodological point.

### 7.2 Where multi-fidelity LSG carries the skill

Burnett and Chowilla wet_train depth RMSE show large LF→LSG lifts. Carlisle’s LF is already skillful on extent; LSG still tightens depth and slightly improves CSI. Leading with zoning CSI or O2−O1 deltas would misrepresent the evidence: the skill lives in the multi-fidelity map, not in localisation.

### 7.3 Why residual zoning is capacity-confounded on Chowilla/Burnett (and qualified on Carlisle)

At native capacity, H-LSG shows a smaller truncation gap O2−O1 than the global baseline (Section 6.7), which can appear to credit localisation. The matched-capacity controls (Section 6.8) show that on Chowilla and Burnett the native-capacity difference is **not uniquely attributable to localisation**: giving the global model the same EC count reproduces (Burnett) or beats (Chowilla) the O2−O1 reduction, and on Chowilla the matched global also attains the best wet RMSE. Two mechanisms explain the decoupling. First, O2−O1 is an HF-oracle truncation contrast that shrinks whenever more variance is retained—by extra zonal residual ECs or by extra global modes alike—so it rewards capacity, not spatial partitioning per se. Second, the extra residual ECs must still be predicted from LF inputs through the SGPR map; on Burnett this map degrades (O4−O2 0.304 m versus 0.056 m; train O4 already 0.360 m versus 0.115 m) while the shared extent gate is unchanged, so localisation buys expressibility that the LF→HF regression cannot honour. Inducing-point budget and zone count move RMSE by more than zoning does (Section 6.8), reinforcing that the observable movements are capacity/approximation effects. Carlisle Max qualifies the generality: exact dim-13 global matching is infeasible under eight training events, and max-rank global capacity worsens RMSE while H-LSG residual stacking improves it (Table 9). We therefore communicate residual hierarchy as a **diagnostic device** whose apparent truncation benefit must be capacity-controlled and site-qualified, not as a blanket accuracy upgrade. Residual `kmeans` labels are residual-response classes optionally augmented by XY; they do not impose geographic contiguity. On Carlisle Max an 8-nearest-neighbour same-zone fraction ≈ 0.95 indicates local spatial coherence when XY is included, but the algorithm remains a response-feature clusterer rather than a watershed or adjacency-constrained partition. Chowilla `wet_correlation` yields a marginally higher wet_train CSI (0.978) with O2−O1 ≈ 0.010, but this too is a small, capacity-consistent delta rather than a localisation win.

### 7.4 Relation to prior art

Relative to Fraehr et al. (2024a), we inherit the public cubes and wet-train/CSI language but do not claim to reproduce their ML horse-race or extrapolation suite; our contribution is capacity-controlled residual zoning and diagnostics on those cubes. Relative to Fraehr et al. (2024b) LESS, which reduces HF training cost by selecting informative events from LF candidates, we hold the published split fixed and ask how residual EOF capacity should be spent—complementary budgets, not competing claims. Relative to Tan et al. (2025), we agree that regionalization and error splitting matter; we differ by adding a four-stage oracle ladder on dual EXT+WSE and, crucially, by subjecting whole-domain residual hierarchy to matched-capacity controls that it fails. Relative to Wang et al. (2025) REOF–SGP, we test residual (not rotated) hierarchical EOFs inside Fraehr-style LSG with public three-case diagnostics. Relative to Wang et al. (2026), which lists zonal EOF as future work, our contribution is not a positive demonstration of that direction but a public-data, capacity-controlled evaluation that cautions against crediting it before capacity is matched—together with calibrated UQ and O1–O4 attribution. This is a reason to report matched-capacity baselines in future localised-EOF flood surrogates.

### 7.5 Rival explanations and risks

We considered whether the H-LSG signals could be genuine localisation. (i) *Fold noise / hyperparameters.* O2−O1 and RMSE differences could reflect fold noise, GP hyperparameter sensitivity, or mask definitions; the matched-capacity controls, inducing sweep, and zone sweep were run precisely to separate these from zoning, and on Chowilla/Burnett they attribute the movements to capacity. (ii) *Extent-gate artefact on Burnett.* The identical EXT agreement and gate miss/false-alarm fractions rule out a gating explanation, isolating the loss to the WSE GP map. (iii) *Unstable CRPS estimator.* Nested CV on Chowilla and Carlisle shows *s* is fold-stable, so the Chowilla UQ null is not an estimator artefact. (iv) *Protocol misreading.* Chowilla all-cell CSI 0.390 could be misread as model collapse; wet_train and O4 refute that. (v) *SGPR floor as trivia.* SGPR inducing floors are engineering necessities for Max-path H-LSG; without them, O4 regressions can masquerade as “zoning hurts.” (vi) *Carlisle residual win.* Table 9 shows residual stacking can help under Max-rank limits; this does not overturn the Chowilla/Burnett capacity-matched anti-cases, but it warns against over-generalising “localisation never helps.” After these controls, residual hierarchical zoning has no demonstrated accuracy advantage over appropriate capacity-matched global baselines on Chowilla and Burnett; Carlisle remains a qualified, rank-limited exception. The main residual risk is external validity: full time-series folds and additional sites remain outside the present computational envelope (Section 8).

### 7.6 Open questions

Does CRPS-scale *s* transfer across sites without retuning? Chowilla’s flat CRPS under the same protocol already warns against universal transfer, even though Carlisle’s nested *s* is fold-stable near 0.42. Would full time-series Chowilla/Burnett folds change the zoning story under memory budgets that can hold ≈200 GB HF stacks? How does residual H-LSG compare with Tan-style single-focus retraining on the same public splits?

---

## 8. Limitations

1. The capacity-controlled localisation analysis is based primarily on maximum-inundation Grp1 evaluations. Full time-series capacity-controlled evaluations were not performed for Chowilla and Burnett because their in-memory requirements exceed the available configuration (Burnett HF stack ≈199 GB versus ≈128 GB host RAM; Chowilla dual EXT+WSE+UQ similarly constrained). Conclusions therefore apply to the evaluated Max-surface setting and should not be extrapolated quantitatively to full time-series training.  
2. Capacity matching controls the WSE representation / GP-input dimension, with inducing-point and zone-count sensitivities addressing two important approximation confounders. It does not equate every kernel, noise, regularisation, or optimisation degree of freedom. The inference is that apparent residual-H-LSG advantages cannot be attributed uniquely to localisation under the tested controls—not that all conceivable capacity effects have been eliminated. On Carlisle Max, exact dim matching to H-LSG’s 13-D residual stack is infeasible because global EOF rank is capped by eight training events.  
3. The `residual_kmeans` formulation defines zones from residual-response statistics, optionally including XY, but does not impose geographic connectivity. A Carlisle Max 8-nearest-neighbour diagnostic yields a mean same-zone fraction ≈ 0.95 when XY is included, indicating local spatial coherence without converting the method into a watershed or adjacency-constrained partition. Results concern residual-response hierarchical zoning and should not be generalised to connectivity-constrained geographic partitions without further capacity-controlled tests.  
4. O1–O4 is an ordered counterfactual diagnostic ladder rather than an additive variance decomposition. Successive contrasts quantify changes along the specified evaluation path and should not be read as unique, order-invariant causal shares of total error.  
5. Nested event-level validation of the scalar CRPS variance factor is reported for Chowilla and Carlisle Max; Burnett nested CV is outside the present scope. Fold stability does not establish transferability of *s* across sites, and variance scaling can be neutral or adverse for some probabilistic diagnostics.  
6. Event replication differs among the published Grp1 splits (Carlisle/Chowilla Max: one held-out event; Burnett: 18). Reported differences are controlled effect-size comparisons rather than population-level significance tests; raster cells are not treated as independent statistical replicates.  
7. Accuracy is evaluated against the corresponding high-fidelity hydrodynamic simulations (perfect-prognosis). The study does not independently validate LF or HF models against observed flood depths or extents.  
8. Empirical evidence is restricted to the public Carlisle, Chowilla, and Burnett cubes. Licensed sites (e.g. Brisbane TUFLOW/URBS) and other multi-fidelity benchmark families are outside the redistributable public evidence base and are left for future external replication.  
9. We do not re-train Fraehr et al. (2024a) ML baselines (1dCNN, LSTM-SRR, GP-EOF, LSTM-EOF) or their 50%-larger extrapolation protocol; those remain cited benchmarks, not reproduced numbers. LESS-style HF-event reselection (Fraehr et al., 2024b) is likewise outside scope given fixed published Grp1 splits.

---

## 9. Conclusions

We present a reproducible EXT+WSE LSG methods stack with O1–O4 oracle attribution and CRPS-calibrated GP uncertainty on three public multi-fidelity flood cases, and we use it to test residual hierarchical zoning under matched-capacity controls on published Grp1 maximum-inundation folds. On Chowilla and Burnett the controls yield a clear negative result for residual localisation as an accuracy upgrade: the apparent H-LSG advantage in the truncation gap O2−O1 is reproduced or exceeded by a capacity-matched global EOF model, disabling residual modes collapses H-LSG onto the global baseline, and on Burnett residual capacity worsens held-out depth RMSE through the LF→HF GP map rather than the shared extent gate. Inducing-point budget and zone count move RMSE as much as zoning does. Carlisle Max qualifies the generality under a hard train-rank cap: residual stacking improves wet RMSE relative to native and max-rank global baselines, while exact dim-13 global matching is infeasible. Multi-fidelity LSG—not localisation per se—provides the primary skill gains where LF is weak. Strong-LF settings require explicit wet_train versus all_cells reporting, and calibrated variance scaling can improve probabilistic scores on over-dispersed posteriors (while leaving mean maps, and therefore CSI/RMSE, unchanged by construction) but can be null, as on Chowilla. The broader methodological implication is to report matched-capacity baselines, attribute error with oracle ladders, publish calibrated uncertainty, and treat localised-EOF gains as capacity-confounded until controlled—and site-qualified when Max-rank limits bind. Residual hierarchical zoning is best used as a truncation diagnostic, not as a claimed universal accuracy upgrade.

---

## 10. Data and code availability

Public multi-fidelity HF/LF cubes are available from Fraehr (2024), DOI [10.26188/24312658](https://doi.org/10.26188/24312658) (CC BY 4.0). Workflow configurations, evaluation summaries, figure exports, and the code used to reproduce the analyses in this paper are archived at [https://github.com/Coucou2016/lsg-flood-surrogate-benchmark](https://github.com/Coucou2016/lsg-flood-surrogate-benchmark). Upstream Hybrid LSG reference code is available at [https://github.com/nfraehr/Hybrid_LSG_model](https://github.com/nfraehr/Hybrid_LSG_model). Brisbane licensed TUFLOW/URBS library access is upon request via Queensland BRCFS channels (Wang et al., 2026) and is **not redistributed** with this study.

---

## 11. Author contributions

[CRediT roles to be finalized and agreed by the author team before submission.]

---

## 12. Competing interests

[Competing-interest statement to be finalized by the author team before submission.]

---

## 13. Acknowledgements

[Acknowledgements and funding disclosures to be finalized by the author team before submission.]

---

## References

Bennett, N. D., Croke, B. F. W., Guariso, G., Guillaume, J. H. A., Hamilton, S. H., Jakeman, A. J., Marsili-Libelli, S., Newham, L. T. H., Norton, J. P., Perrin, C., Pierce, S. A., Robson, B., Seppelt, R., Voinov, A. A., Fath, B. D., & Andreassian, V. (2013). Characterising performance of environmental models. *Environmental Modelling & Software*, 40, 1–20. https://doi.org/10.1016/j.envsoft.2012.09.011

Chang, C.-H., Lee, H., Kim, D., Hwang, E., Hossain, F., Chishtie, F., Jayasinghe, S., & Basnayake, S. (2020). Hindcast and forecast of daily inundation extents using satellite SAR and altimetry data with rotated empirical orthogonal function analysis: Case study in Tonle Sap Lake Floodplain. *Remote Sensing of Environment*, 241, 111732. https://doi.org/10.1016/j.rse.2020.111732

Chang, C.-H., Lee, H., Do, S. K., Du, T. L. T., Markert, K., Hossain, F., Ahmad, S. K., Piman, T., Meechaiya, C., Bui, D. D., Bolten, J. D., Hwang, E., & Jung, H. C. (2023). Operational forecasting inundation extents using REOF analysis (FIER) over lower Mekong and its potential economic impact on agriculture. *Environmental Modelling & Software*, 162, 105643. https://doi.org/10.1016/j.envsoft.2023.105643

Donnelly, J., Abolfathi, S., Pearson, J., Chatrabgoun, O., & Daneshkhah, A. (2022). Gaussian process emulation of spatio-temporal outputs of a 2D inland flood model. *Water Research*, 225, 119100. https://doi.org/10.1016/j.watres.2022.119100

Eilander, D., Fraehr, N., Leijnse, T., & de Goede, R. (2025). Surrogate flood models for compound flood risk assessments and early warning. EGU General Assembly 2025, abstract EGU25-5209. https://doi.org/10.5194/egusphere-egu25-5209

Eilander, D., de Goede, R., Leijnse, T., & Fraehr, N. (2026a). Hybrid surrogate modeling of compound flood events using SFINCS-LSG. EGU General Assembly 2026, abstract EGU26-11062. https://doi.org/10.5194/egusphere-egu26-11062

Eilander, D., de Goede, R., Leijnse, T., & Fraehr, N. (2026b). SFINCS-LSG dataset, model files, python environment and scripts (Version v1) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.20352880

Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2022). Upskilling low-fidelity hydrodynamic models of flood inundation through spatial analysis and Gaussian process learning. *Water Resources Research*, 58(8), e2022WR032248. https://doi.org/10.1029/2022WR032248

Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2023a). Development of a fast and accurate hybrid model for floodplain inundation simulations. *Water Resources Research*, 59(6), e2022WR033836. https://doi.org/10.1029/2022WR033836

Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2023b). Supercharging hydrodynamic inundation models for instant flood insight. *Nature Water*, 1(10), 835–843. https://doi.org/10.1038/s44221-023-00132-2

Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2024a). Assessment of surrogate models for flood inundation: The physics-guided LSG model vs. state-of-the-art machine learning models. *Water Research*, 252, 121202. https://doi.org/10.1016/j.watres.2024.121202

Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2024b). Generation and selection of training events for surrogate flood inundation models. *Journal of Environmental Management*, 373, 123570. https://doi.org/10.1016/j.jenvman.2024.123570

Fraehr, N. (2024). Surrogate flood model comparison – Datasets and python code [Data set]. The University of Melbourne. https://doi.org/10.26188/24312658

Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359–378. https://doi.org/10.1198/016214506000001437

Kohanpur, A. H., Saksena, S., Dey, S., Johnson, J. M., Riasi, M. S., Yeghiazarian, L., & Tartakovsky, A. M. (2023). Urban flood modeling: Uncertainty quantification and physics-informed Gaussian processes regression forecasting. *Water Resources Research*, 59(3), e2022WR033939. https://doi.org/10.1029/2022WR033939

López-Lopera, A. F., Idier, D., Rohmer, J., & Bachoc, F. (2022). Multioutput Gaussian processes with functional data: A study on coastal flood hazard assessment. *Reliability Engineering & System Safety*, 218, 108139. https://doi.org/10.1016/j.ress.2021.108139

Lu, J., Wang, Q. J., Fraehr, N., Xiang, X., & Wu, X. (2025). Choice of Gaussian Process kernels used in LSG models for flood inundation predictions. *Journal of Hydrology*, 655, 132949. https://doi.org/10.1016/j.jhydrol.2025.132949

Markert, K. N., Lee, H., Williams, G. P., Nelson, E. J., Ames, D. P., Griffin, R. E., & Meyer, F. J. (2026). Evaluating the feasibility of scaling the FIER framework for large-scale flood inundation prediction. *Hydrology and Earth System Sciences*, 30(2), 459–484. https://doi.org/10.5194/hess-30-459-2026

Siripatana, A., Wilson, A. L., & Beevers, L. (2025). Uncertainty quantification for multi-input fluvial flood inundation using GPR- and PCE-based surrogates. *Water Resources Research*, 61(10), e2024WR039668. https://doi.org/10.1029/2024WR039668

Tan, Z., Xu, D., Taraphdar, S., Ma, J., Bisht, G., & Leung, L. R. (2025). An efficient hybrid downscaling framework to estimate high-resolution river hydrodynamics. *Hydrology and Earth System Sciences*, 29(16), 3833–3852. https://doi.org/10.5194/hess-29-3833-2025

Wan, H.-H., Lee, H., Thuy Du, T. L., Rostami, A., Chang, C.-H., Markert, K. N., Nelson, E. J., Williams, G. P., Li, S., Straka, W., Helfrich, S. R., & Meyer, F. J. (2025). An interpretable and scalable model for rapid flood extent forecasting using satellite imagery and machine learning with rotated EOF analysis. *Environmental Modelling & Software*, 192, 106562. https://doi.org/10.1016/j.envsoft.2025.106562

Wang, R., Lian, J., Yuan, X., Tian, F., Li, K., & Liu, Z. (2025). Rapid simulation of floods by considering the spatial and temporal characteristics of inundation. *International Journal of Disaster Risk Science*, 16(3), 481–495. https://doi.org/10.1007/s13753-025-00642-5

Wang, W., Wang, Q. J., & Nathan, R. (2026). Strategies for predicting flood inundation in a large and complex floodplain based on low-fidelity hydrodynamic models. *Water Resources Research*, 62(5), e2025WR042481. https://doi.org/10.1029/2025WR042481

Zanchetta, A. D. L., & Coulibaly, P. (2022). Probabilistic forecasts of flood inundation maps using surrogate models. *Geosciences*, 12(11), 426. https://doi.org/10.3390/geosciences12110426

---

## Appendix A. Terminology ledger (canonical forms)

LSG; LSG-TS; LSG-Max; LF; HF; EOF; EC; EXT; WSE; H-LSG; residual_kmeans; SGPR; CRPS; CSI; POD; RFA; O1–O4; O2−O1 (truncation gap); O4−O2 (LF projection + GP map); wet_train; all_cells; `var_scale`; `force_n_modes` (matched-capacity mode budget); `gp_input_dim`; `min_inducing_points`; `n_zones`; AF; TF; τ = 0.03 m.

## Appendix B. Figure and table inventory

| ID | Content | Role |
|----|---------|------|
| Fig. 1 | Study domains | Three-case domain cell-scatter |
| Fig. 2 | Extent hit/miss/false-alarm maps | Extent agreement (LF & LSG vs HF) |
| Fig. 3 | Peak-depth error maps | Peak-depth residuals (LF−HF, LSG−HF) |
| Fig. 4 | Inundation probability maps | P(wet) probabilistic maps |
| Fig. 5 | Cross-case CSI/RMSE | Wet_train CSI/RMSE across cases |
| Fig. 6 | O1–O4 error budgets | Attribution ladders |
| Fig. 7 | Global versus H-LSG | Native-capacity contrast (Chowilla + Burnett) |
| Fig. 8 | CRPS-scale calibration | UQ before/after |
| Fig. 9 | Zoning sensitivity | Chowilla residual *k*-means vs wet-correlation |
| — | Hydrographs | Not available (maximum-surface prediction exports only) |
| Table 1 | Case inventory | Data |
| Table 2 | CSI/RMSE | Point skill |
| Table 3 | O1–O4 | Attribution |
| Table 4 | Variance scale / CRPS | UQ |
| Table 5 | Chowilla zoning CSI/RMSE/O2−O1 | Zoning sensitivity |
| Table 6 | Chowilla equal-capacity control | Capacity confound (RQ1) |
| Table 7 | Burnett equal-capacity + oracle attribution | Capacity confound (RQ1/RQ2) |
| Table 8 | Chowilla inducing / zone sweeps | Nuisance-capacity confounds |
| Table 9 | Carlisle equal-capacity control | Capacity control + Max-rank caveat (RQ1) |

## Appendix C. Scope boundaries

Closed scientific boundaries (not open TODOs): Chowilla/Burnett full time-series Grp1 folds (memory: Burnett HF stack ≈199 GB ≫ ≈128 GB RAM); Brisbane licensed appendix and FloodCastBench (outside the public redistributable evidence base); exhaustive capacity × zoning × site factorials and oracle-order permutation decompositions (O1–O4 retained as a path-ordered ladder); Burnett nested CRPS *s* CV.

Capacity-controlled evidence reported in the main text comprises Chowilla and Burnett equal-capacity global versus H-LSG contrasts (Tables 6–7), Chowilla inducing-point and zone-count sweeps (Table 8), Burnett oracle attribution (Table 7), Carlisle equal-capacity control with Max-rank caveat (Table 9), nested CV for CRPS *s* on Chowilla and Carlisle, and a Carlisle residual-zone 8-nearest-neighbour coherence diagnostic.

Author names, affiliations, CRediT roles, competing interests, and acknowledgements remain working-draft metadata fields to be finalized by the author team before journal submission.