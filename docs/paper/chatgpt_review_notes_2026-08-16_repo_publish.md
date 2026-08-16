# ChatGPT review notes — 2026-08-16 (GitHub-publish turn)

Advisor only. Local executor verified claims against sources + `outputs/evaluation/**/*.json`.

## GitHub publication

- **URL:** https://github.com/Coucou2016/lsg-flood-surrogate-benchmark
- **Visibility:** PUBLIC
- **Pushed commit (initial refresh):** `604661293ace8e62e3afc972b960e33ddecdbc69`
- **Secret scan:** no `.env`/keys/tokens; local absolute paths sanitized before push
- **Excluded:** `data/external/**`, `*.npz` models/cubes, bulk zips, files >~50 MB

## Conversation 1 — Repo-aware code review

- **URL:** https://chatgpt.com/c/6a8189d9-bac4-83ea-a149-5c8ecf88d721
- **Purpose:** Architecture / correctness / tests / reproducibility of `lsg/`
- **Web search:** YES (`正在搜索 raw.githubusercontent.com`; citation chips; file URL list)
- **GitHub read:** YES — listed raw URLs for README, `lsg/*.py`, tests, `config/carlisle.yaml`, etc. at pinned commit
- **Rate limit:** mid-generation “请求过于频繁”; dismissed; continuation partially citation-noisy but first reply completed (~28k)

### Advisor main points (verified locally)

| Advice | Verdict | Evidence |
|--------|---------|----------|
| EXT+WSE dual path + residual-on-WSE only is real | **Accept** | `wse_ext.py`, `zoning.py` |
| Constant AF excluded from WSE → depth 0 under EXT=1 | **Accept + fixed** | `wet_cell_mask` excludes max==min; `classify_extent_cells` now unions AF into WSE support; test added |
| O1 not always uncapped SVD floor when `max_eof_modes` binds | **Accept + docstring** | `diagnostics.py` O1 wording clarified |
| “calibration split” overstates train-fit CRPS scale | **Accept + docstring** | `uq.py` + `run_lsg_workflow.py` already train-fit |
| Dual UQ latent mean pre-thresholded; EXT gate hard | **Accept as wording** | code-review-only for paper; no API change this turn |
| CRPS is latent-Gaussian vs censored Brier/map | **Accept as wording** | already partly in `uq.py`; keep honest language |
| SGPR Z may move in first L-BFGS pass | **Partially accept** | intentional two-phase; README “exact at M=n” is approximate — mark caveat, no refactor |
| `gp_kernel` config unused | **Accept as known** | declarative; **未运行** to wire |
| Missing CI / frozen env | **Accept** | no `.github/` in publish mirror |
| Equal-capacity A/B mandatory now | **Reject as done**; leave **待补充** | concurrent agent owns `04_capacity_controls.md` |

## Conversation 2 — Manuscript + repo

- **URL:** *(filled when completed)*
- **Purpose:** Claims vs code; overclaiming; novelty vs Tan/REOF/SFINCS/Markert/FIER
- **Status:** see live log below / final report

## Conversation 3 — Chinese report (completed)

- **URL:** https://chatgpt.com/c/6a819be9-19c4-83ea-9721-6809bf203f0f
- **Purpose:** Teaching depth / glossary / causal narrative vs formal report standard
- **Web search:** YES (GitHub + raw report.md + figure SVGs/manifest)
- **GitHub read:** YES — `docs/report/report.md`, figure SVGs, `figure_manifest.json` at commit `19ff7ad`
- **Accepted locally (this turn):** glossary inducing-point symbol `Z_ind`; sanitize `figure_manifest.json` relative paths; keep `待补充`; soft O2−O1 wording in conclusion
- **Deferred:** full report chapter rewrite / Fig5 merge / HTML+PDF full rebuild cycle (**PDF QA 未运行** this turn after md-only report tweaks)

## Independent literature re-check (this turn)

- Tan et al. 2025 HESS 10.5194/hess-29-3833-2025: **verified** (Zeli Tan et al.; regionalized LSG for velocity ERDR)
- SFINCS–LSG 10.5194/egusphere-egu26-11062: **verified** (EGU26 abstract; compound SFINCS×LSG)
- Prior notes still hold for REOF-SGP / Markert 2026 / FIER / Wang WRR 2026

## Local code changes this turn

1. `lsg/wse_ext.py` — AF ∪ varying → WSE `wet_idx`
2. `tests/test_wse_ext.py` — constant-AF regression
3. `lsg/uq.py` — train-fit variance scale wording
4. `lsg/diagnostics.py` — O1 / `max_eof_modes` wording

## Conversation 2 — Manuscript + repo (completed)

- **URL:** https://chatgpt.com/c/6a819989-7148-83ea-a8c8-d0b1785e4164
- **Purpose:** Claims vs code; overclaiming; novelty vs Tan/REOF/SFINCS/Markert/FIER
- **Web search:** YES (github.com + raw.githubusercontent.com + HESS/Springer citations)
- **GitHub read:** YES — manuscript.md, 03_new_results.md, README, zoning/uq/diagnostics/wse_ext/gp, evaluation JSONs

### Local accept / reject

| Advice | Verdict |
|--------|---------|
| Soften “truncation gap” → held-out subspace-expressibility (O2−O1) | **Accept** (wording) |
| Capacity confounding; equal-budget 待补充 | **Accept**; do not invent numbers |
| H-LSG not accuracy-win on Chowilla/Burnett RMSE | **Accept** (already in notes/JSON) |
| Novelty sentence as integrated diagnostic framework | **Accept** |
| Chang M. → Chi-Hung Chang metadata | **Accept** if manuscript has wrong given name — check |
| Demand REOF/Tan reimplementation now | **Reject as completed**; keep 未运行 |
| Equal-capacity runs | **Do not run** (concurrent agent) |

