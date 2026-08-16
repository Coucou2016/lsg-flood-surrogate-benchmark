# ChatGPT review notes — 2026-08-16 (this turn)

Advisor only. Local executor verified claims against primary sources and `outputs/evaluation/**/*.json`.

## Conversation 1 — Manuscript peer review

- **URL:** https://chatgpt.com/c/6a815ce3-60c4-83ea-99ad-0149a2ac3c4c
- **Purpose:** WRR/JoH/EMS referee review of diagnostic + calibrated UQ + condition-dependent zoning positioning
- **Web search:** YES (`已搜索` / cited DOIs; UI showed “已搜索 20 个网站” during generation)
- **GitHub URL read:** NO (gh publish blocked; pasted CONTEXT only; advisor stated no repo reviewed)
- **Rate limit:** temporary “请求过于频繁” modal mid-generation; reply completed after dismiss

### Advisor main points (summary)

1. Defensible as diagnostic framework; not as “new spatial localization method.”
2. Major: equal-capacity global vs H-LSG; training-only condition for “where helps”; wet_train/all_cells centrality; EXT gate vs full inundation UQ; leakage-safe CRPS calibration design; oracle non-additivity; zone contiguity.
3. Missing P0: matched budget A/B, Burnett global A/B, independent UQ design, oracle-order robustness.
4. Prefer EMS ≈ JoH > WRR until P0 filled; title softer (“Diagnosing when…”).

### Local accept / reject

| Advice | Verdict | Evidence |
|--------|---------|----------|
| Keep diagnostic framing; cite Tan/REOF/SFINCS tightly | **Accept** | Independent DOI checks 2026-08-16 |
| Clarify CSI/RMSE invariant *by construction* under variance-only scale | **Accept** | Method definition `Var_cal = s·Var_raw` |
| Call O1–O4 counterfactual ladder, not additive variance decomposition | **Accept** | Nonlinear EXT+WSE+clip path |
| Report N events / single-event Max holdouts explicitly | **Accept** | JSON: Carlisle/Chowilla Max `n_samples` test=1; Burnett test=18 |
| HF emulation target (perfect prognosis), not observations | **Accept** | Fraehr protocol / our ingest |
| Soften title / “where helps” wording | **Accept partially** | Discussion + optional title note; keep working title with diagnostic subtitle emphasis |
| Matched EOF/inducing budget A/B mandatory now | **Reject as completed claim**; mark **待补充/未运行** | No equal-budget JSON exists |
| Non-residual geographic zoning control | **Reject as done**; mark **未运行** | Not in repo |
| Nested CV for `s` | **Reject as done**; document train-fit `s` honestly | Calibrated JSON; method says fit on train |
| Invent Burnett global A/B numbers | **Reject** | Headline global Burnett **未运行** |
| Claim web search found exact residual hierarchical LSG match | **Reject** | Still NOT FOUND as exact match after re-check |

## Conversations 2–3

### Conversation 2 — Literature/novelty re-check

- **URL:** https://chatgpt.com/c/6a815fec-5b60-83ea-96a2-708928027aae
- **Purpose:** Web-search novelty re-check vs Tan / Rukai Wang / SFINCS-LSG / Markert / FIER; explicit FOUND/NOT FOUND
- **Web search:** YES (UI “已搜索”; reply lists DOIs; intermittent rate-limit modal)
- **GitHub URL read:** NO
- **Advisor verdict (aligned with local check):** exact combined residual hierarchical LSG + CRPS map posterior + O1–O4 **NOT FOUND**; cite Tan/REOF/Markert/SFINCS/SSRN as boundary priors; add Wang WRR 2026 + Lu 2025 to novelty paragraph (already in our lit review)

### Conversation 3 — Chinese report readability

- **URL:** https://chatgpt.com/c/6a816202-85e0-83ea-9ed9-3de1fdb994cb
- **Purpose:** Formal Chinese research-report structure / glossary / figure-narrative review
- **Web search:** YES (cited GB/T 7713.3-2014 tech-report structure; body is structure diagnosis)
- **GitHub URL read:** NO
- **Accepted locally:** add read-path note; keep O1–O4 as mechanism/counterfactual not additive causal; keep working-draft `待补充` list; avoid claiming engineering “bug fix” as science headline
- **Deferred (not executed this turn):** full chapter merge / move timeline to appendix / delete `待补充` from TOC (large rewrite; concurrent experimental agent)

## Independent literature re-check (local)

- Tan et al. 2025 HESS: **verified** DOI 10.5194/hess-29-3833-2025 (Zeli Tan et al.; regionalized LSG + DR vs mapping error).
- Rukai Wang et al. 2025: **verified** DOI 10.1007/s13753-025-00642-5 (REOF-SGP).
- Markert et al. 2026: **verified** DOI 10.5194/hess-30-459-2026.
- SFINCS–LSG EGU26-11062: **verified** DOI 10.5194/egusphere-egu26-11062; additional SSRN preprint 10.2139/ssrn.6727349 (metadata only; not peer-reviewed journal).
- Wang 2026 WRR local MD: zonal EOF named as **future work** (confirmed).
