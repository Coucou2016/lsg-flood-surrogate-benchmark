# Capacity / zoning controls (referee handoff)

Machine-readable closure of referee concerns that hierarchical residual zoning (H-LSG) may be confounded with **extra model capacity** (more retained ECs / wider GP inputs) relative to the global EOF baseline.

**Do not treat this file as the manuscript.** Numbers below are read from on-disk JSON artifacts only.
Host: Windows, ~128 GB RAM. Workspace has **no `.git`**. **仅本地修改，未提交、未推送、未创建 PR、未部署。**

Phase 0 pytest (this session, before/after code): **80 passed, 1 skipped** → after changes **83 passed, 1 skipped** (`outputs/evaluation/pytest_capacity_controls.txt`).

---

## Verdict (plain)

**The localization claim does *not* survive capacity matching as a general explanation of H-LSG gains.**

| Claim framing | Survives? | Evidence |
|---------------|-----------|----------|
| H-LSG O2−O1 shrink is *localization*, not capacity | **No** | Matched-capacity global matches or beats H-LSG on O2−O1 (Chowilla + Burnett) |
| H-LSG improves final wet RMSE via localization | **No** (already weak; controls weaken further) | Chowilla: matched global RMSE **better** than H-LSG; Burnett: H-LSG RMSE **worse** than auto-global; matched-18 global also worse |
| Inducing-point floor can dominate zoning reads | **Yes** | Chowilla H-LSG `m=2` RMSE 0.244 vs `m=16` 0.093; O2−O1 unchanged |
| CRPS scale `s` is unstable / train-overfit with N_test=1 | **No evidence of instability on Chowilla** | 8-fold LOO: `s = 0.3099 ± 0.0073` vs full-train `0.3088` |
| `n_zones=4` is a lucky setting | **Partially sensitive** | More zones → smaller O2−O1 but **worse** wet RMSE (over-capacity) |

Honest manuscript implication: report H-LSG primarily as a **truncated-gap (O2−O1) device with capacity-matched controls**, not as a CSI/RMSE upgrade over global EOF. On Burnett, residual capacity **hurts** operational depth RMSE while still shrinking O2−O1.

---

## Phase 0 — baseline

| Check | Result |
|-------|--------|
| `.git` | **Absent** (no commit/push) |
| pytest | `.\.venv\Scripts\python.exe -m pytest tests -q` → **80 passed, 1 skipped** (start); **83 passed, 1 skipped** (end) |
| Prior handoff | `docs/paper/03_new_results.md` |

Code added for matched capacity:

- `lsg.force_n_modes` via `eof.resolve_n_modes` (used in `lsg/base.py`, `lsg/wse_ext.py`)
- `base.capacity_snapshot` + `metrics["capacity"]` in `scripts/run_lsg_workflow.py`
- Fixed `config/chowilla_global.yaml` models path → `outputs/models/chowilla_global` (was sharing `chowilla/` and had overwritten H-LSG weights)
- Config twins under `config/chowilla_*`, `config/burnett_global_matched18.yaml`
- Scripts: `scripts/run_capacity_controls.py`, `scripts/diagnose_burnett_hlsg_gap.py`, `scripts/nested_crps_scale_cv.py`
- Tests: `tests/test_eof.py` (`resolve_n_modes`), `tests/test_zoning.py` (`capacity_snapshot`)

---

## Exp 1 — Equal-capacity control (headline)

### Question
Does the H-LSG effect survive when total WSE GP input dimensionality matches the global baseline (and vice versa)?

### Design
- H-LSG default: global modes + `n_zones × residual_eof_modes` residual ECs stacked into the WSE GP.
- **Matched global up:** `zoning: none`, `force_n_modes = H-LSG gp_input_dim`.
- **Matched H-LSG down:** `residual_eof_modes: 0` (zones built but no residual ECs).

### Chowilla (cheapest full Grp1 Max)

| Run | Command | Exit | Wall (s) | Artifact |
|-----|---------|------|----------|----------|
| H-LSG restore | `python scripts/run_lsg_workflow.py --config config/chowilla.yaml --variants lsg_max --no-pred-examples --summary-out outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max_capacity_rerun.json` | 0 | 123.1 | `.../hlsg_max_capacity_rerun.json` |
| Global auto (3) | `... --config config/chowilla_global.yaml ... --summary-out .../global_max_capacity_rerun.json` | 0 | 85.3 | `.../global_max_capacity_rerun.json` |
| Global matched (15) | `... --config config/chowilla_global_matched15.yaml ... --summary-out .../global_matched15_max.json` | 0 | 114.4 | `.../global_matched15_max.json` |
| H-LSG budget=3 | `... --config config/chowilla_hlsg_budget3.yaml ... --summary-out .../hlsg_budget3_max.json` | 0 | 78.9 | `.../hlsg_budget3_max.json` |

**Wet_train metrics (Grp1, `score_protocol.lsg_max.wet_train`):**

| Model | WSE `gp_input_dim` | CSI | RMSE (m) | test O2−O1 | test O4 |
|-------|--------------------|-----|----------|------------|---------|
| Global auto | 3 | 0.974428 | **0.087668** | 0.057124 | 0.087668 |
| H-LSG (`residual_kmeans`) | 15 (=3+12) | **0.975597** | 0.093158 | 0.013275 | 0.093158 |
| Global matched-15 | **15** | 0.975200 | **0.085066** | **0.001767** | **0.085066** |
| H-LSG residual_modes=0 | 3 | 0.974428 | 0.087668 | 0.057124 | 0.087668 |

**Interpretation:** On Chowilla, giving the global model the **same EC count** as H-LSG **closes and exceeds** the O2−O1 “zoning” benefit and yields the **best** wet RMSE. H-LSG with residual modes disabled collapses to the global baseline. → **Weakens / undermines** the claim that O2−O1 gains are from localization rather than capacity.

### Burnett

| Run | Command | Exit | Artifact |
|-----|---------|------|----------|
| Prior global | (from `03_new_results.md`) | 0 | `outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_global_max.json` |
| Prior H-LSG | (existing) | 0 | `.../hlsg_max.json` |
| Global matched-18 | `python scripts/run_lsg_workflow.py --config config/burnett_global_matched18.yaml --variants lsg_max --no-pred-examples --summary-out outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_global_matched18_max.json` | 0 | `.../global_matched18_max.json` (`runtime_train_s`≈100; log `matched18_run.log`) |

| Model | WSE dim | CSI | RMSE (m) | test O2−O1 | test O4 |
|-------|---------|-----|----------|------------|---------|
| Global auto | 6 | **0.975108** | **0.178787** | 0.048907 | **0.178787** |
| H-LSG | 18 (=6+12) | 0.975152 | 0.386751 | 0.008515 | 0.386751 |
| Global matched-18 | **18** | 0.971973 | 0.415512 | **0.003976** | 0.415512 |

**Interpretation:** Extra capacity (global 18 **or** H-LSG residual stack) **improves O2−O1** but **degrades** operational RMSE vs the North/Kaiser global. Matched-18 global is as bad as or worse than H-LSG on RMSE. → Capacity explains the O2−O1 pattern; it does **not** justify H-LSG as a skill upgrade on Burnett.

**Strengthens / weakens:** **Weakens** the localization framing for O2−O1; **does not rescue** H-LSG RMSE on Burnett.

---

## Exp 2 — Inducing-point sensitivity

### Question
Can SGPR inducing budget be confused with a zoning effect?

### Commands (Chowilla H-LSG; `min_inducing_points` ∈ {2,8,16,28})

```text
python scripts/run_lsg_workflow.py --config config/chowilla_inducing_m{2,8,28}.yaml --variants lsg_max --no-pred-examples --summary-out outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_inducing_m{2,8,28}_max.json
```

Baseline `m=16`: `.../hlsg_max_capacity_rerun.json`.  
Global `m=2`: `config/chowilla_global_inducing_m2.yaml` → `.../global_inducing_m2_max.json`.

| Zoning | `min_inducing` | CSI | RMSE | test O2−O1 | Exit / wall |
|--------|----------------|-----|------|------------|-------------|
| H-LSG | 2 | 0.946741 | **0.244407** | 0.013275 | 0 / 84 s |
| H-LSG | 8 | 0.989936 | 0.095713 | 0.013275 | 0 / 90 s |
| H-LSG | 16 (default) | 0.975597 | 0.093158 | 0.013275 | 0 / 123 s |
| H-LSG | 28 (=n_train) | 0.982525 | **0.073015** | 0.013275 | 0 / 88 s |
| Global | 2 | 0.978988 | 0.085118 | 0.036728* | 0 |
| Global | 16 | 0.974428 | 0.087668 | 0.057124 | 0 / 85 s |

\*Oracle O2−O1 should be inducing-invariant; H-LSG rows confirm that. Global m2 vs m16 O2−O1 differs across independent refits (EOF numerical/refit variance) — treat operational RMSE/CSI as the inducing readout.

**Interpretation:** With H-LSG’s **15-D** WSE inputs, `m=2` is catastrophic on RMSE while **O2−O1 is unchanged** — classic sparse-GP pathology, not zoning. Raising `m` to `n_train` improves H-LSG RMSE below the default. Global 3-D inputs tolerate `m=2`. → Zoning papers must report inducing budget; low-`m` H-LSG collapses can be misread as “zoning hurts.”

**Strengthens / weakens:** Strengthens caution about capacity/approximation confounds; does not restore a localization-only story.

---

## Exp 3 — Burnett O2−O1 vs RMSE discrepancy

### Question
Why does H-LSG shrink test O2−O1 but worsen wet RMSE / O4 on Burnett?

### Command

```text
python scripts/diagnose_burnett_hlsg_gap.py
```

Exit 0 · wall ≈ 2136 s · artifact: `outputs/evaluation/burnett/diagnose_hlsg_o2_vs_rmse.json`.

### Measured evidence

| Quantity | H-LSG | Global |
|----------|-------|--------|
| wet CSI | 0.975152 | 0.975108 |
| wet RMSE | **0.386751** | **0.178787** |
| test O2−O1 | **0.008515** | 0.048907 |
| test O4−O2 | **0.303871** | **0.055515** |
| test O3 | 0.667825 | 0.708017 |
| train O4 | 0.359535 | 0.115027 |
| EXT cell agree | **0.986139** | **0.986139** (identical; EXT is global in both) |
| frac gate miss / FA | 0.00251 / 0.01155 | same |
| RMSE on both-wet cells | **0.509491** | **0.220441** |
| Ungated WSE→depth RMSE (wet) | **0.442028** | **0.193371** |
| frac WSE floor-clipped (wet) | 0.198 | 0.293 |
| WSE `gp_input_dim` | 18 | 6 |

**Interpretation (evidence-based):**

1. **Not an EXT-gate story** — EXT agreement and gate miss/FA fractions are identical.
2. **Not “O2 better ⇒ map better”** — O2 is an HF-oracle truncated reconstruction; O4−O2 isolates LF projection + GP EC mapping (+ gating). H-LSG’s O4−O2 (0.304) dwarfs global’s (0.056).
3. **WSE branch overfits / mis-maps residual ECs** — even ungated WSE depth error is ~2.3× worse; train O4 is already 0.36 vs 0.12, so the damage is not only holdout.
4. Matched-18 global (Exp 1) also worsens RMSE while improving O2−O1 → **extra EC capacity improves expressibility but harms LF→HF GP maps on Burnett**.

**Strengthens / weakens:** **Weakens** any framing that cites Burnett O2−O1 as evidence of operational zoning skill. Prefer: “H-LSG truncates better; residual GP capacity can hurt depth RMSE.”

---

## Exp 4 — Nested / repeated CV for CRPS scale `s`

### Question
Is train-fit `s` stable across folds when official test is N_event=1?

### Command

```text
python scripts/nested_crps_scale_cv.py --config config/chowilla.yaml --model outputs/models/chowilla/lsg_max_state.npz --summary-out outputs/evaluation/chowilla/nested_crps_scale_cv.json --max-folds 8
```

Exit 0 · wall ≈ 84 s · artifact: `outputs/evaluation/chowilla/nested_crps_scale_cv.json`.

| Statistic | Value |
|-----------|-------|
| Full-train `s` | 0.308849 |
| 8-fold LOO mean ± std | **0.309909 ± 0.007296** |
| Fold min / max | 0.298373 / 0.323837 |
| Folds used | E4, E6, E9, E14, E18, E26, E27, E29 |

**Interpretation:** On Chowilla Max H-LSG, `s` is **stable** under leave-one-train-event-out. This does **not** claim Chowilla CRPS calibration is useful (prior rescore: CRPS flat / coverage drifts) — only that the scalar is not a fragile single-draw artefact.

**Strengthens / weakens:** Neutral-to-slightly strengthening for UQ methodology honesty; unrelated to zoning localization.

**未运行:** nested `s` on Carlisle full / Burnett (RAM/time); not required once cheapest case is clean.

---

## Exp 5 — Zone-count sensitivity

### Question
Is `n_zones=4` a lucky setting?

### Commands

```text
python scripts/run_lsg_workflow.py --config config/chowilla_nzones_{2,6}.yaml --variants lsg_max --no-pred-examples --summary-out outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_nzones{2,6}_max.json
```

| `n_zones` | WSE dim | CSI | RMSE | test O2−O1 | Exit / wall |
|-----------|---------|-----|------|------------|-------------|
| 2 | 9 | 0.975169 | **0.087276** | 0.019275 | 0 / 82 s |
| 4 (default) | 15 | 0.975597 | 0.093158 | 0.013275 | 0 / 123 s |
| 6 | 21 | 0.975397 | 0.102822 | **0.012240** | 0 / 144 s |

**Interpretation:** O2−O1 improves monotonically with zone/EC count; **wet RMSE worsens**. Default `n_zones=4` is not a magic CSI peak — it trades truncation gap vs map error. Aligns with Exp 1 capacity confound.

**Strengthens / weakens:** Weakens “lucky n_zones” CSI claims; consistent with capacity-driven O2−O1.

---

## Still **未运行** (measured justification)

| Item | Status | Justification |
|------|--------|---------------|
| Chowilla / Burnett **full-TS** Grp1 | **未运行** | Burnett HF stack ≈199 GB ≫ ~128 GB RAM (`03_new_results.md` Gap 5); unchanged |
| Carlisle full equal-capacity / inducing sweeps | **未运行** | ~40 min / up to ~85–100 GB per full run; Chowilla Max answers the same questions cheaper |
| Nested `s` on Burnett / Carlisle | **未运行** | Chowilla LOO already shows stability; Burnett UQ rescore is multi-10-min |
| Geographic non-residual partition control | **未运行** | Out of scope this pass; `wet_correlation` already in `03_new_results.md` |

---

## Code / config changelog (local only)

| Path | Role |
|------|------|
| `lsg/eof.py` | `resolve_n_modes` + `force_n_modes` |
| `lsg/base.py` / `lsg/wse_ext.py` | use `resolve_n_modes`; `capacity_snapshot` |
| `scripts/run_lsg_workflow.py` | emit `metrics.capacity` |
| `config/chowilla_global.yaml` | models → `outputs/models/chowilla_global` |
| `config/chowilla_global_matched15.yaml` | `force_n_modes: 15` |
| `config/burnett_global_matched18.yaml` | `force_n_modes: 18` |
| `config/chowilla_hlsg_budget3.yaml` | `residual_eof_modes: 0` |
| `config/chowilla_nzones_{2,6}.yaml` | zone sweep |
| `config/chowilla_inducing_m{2,8,28}.yaml` | inducing sweep |
| `config/chowilla_global_inducing_m2.yaml` | global inducing control |
| `scripts/diagnose_burnett_hlsg_gap.py` | Burnett O2 vs RMSE attribution |
| `scripts/nested_crps_scale_cv.py` | LOO CRPS `s` |
| `scripts/run_capacity_controls.py` | batch runner + JSONL log |
| `tests/test_eof.py`, `tests/test_zoning.py` | focused tests |

**Did not edit:** `docs/paper/manuscript.md`, `docs/report/report.md`, `docs/paper/01_literature_review.md` (concurrent writing agent).

---

## Pytest

```text
83 passed, 1 skipped, 2 warnings in 78.16s
```

Source: `outputs/evaluation/pytest_capacity_controls.txt`.

---

## Bottom line for manuscript authors

1. **Do not claim** that H-LSG beats global EOF on depth RMSE *because of localization* without stating the matched-capacity negative controls above.
2. **Do claim** (with controls): residual hierarchy **reduces O2−O1**, and that reduction is **largely reproducible by increasing global mode count**.
3. On **Burnett**, state clearly that H-LSG **worsens** wet RMSE via **GP/LF mapping (O4−O2)**, not EXT gating; matched-18 global shows the same failure mode under pure capacity.
4. Keep **inducing floor** and **n_zones** sensitivity in Methods/SI — both move RMSE as much as zoning.
5. CRPS `s` on Chowilla is **fold-stable**; still report Chowilla calibration CRPS as flat/coverage-hostile where previously documented.

**仅本地修改，未提交、未推送、未创建 PR、未部署。**
