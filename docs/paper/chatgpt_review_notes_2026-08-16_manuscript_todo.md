# ChatGPT review notes — 2026-08-16 (manuscript TODO triage)

Advisor only. Local executor verified against JSON / code / venv.

## Conversation

- **URL:** https://chatgpt.com/c/6a81b98e-2ae8-83ea-8d6f-0cbd277c1188
- **Title:** Manuscript Triage Advice
- **Web search:** YES (`网页搜索` enabled; UI showed “已搜索 2 个网站” then further web search)
- **GitHub read:** YES — listed README, manuscript.md, 04_capacity_controls.md, 00_progress_review.md, zoning.py, wse_ext.py, requirements.txt, case configs
- **Literature opened:** Tan 2025 HESS; Wang 2025 REOF-SGP; Markert 2026 HESS; EMS/Elsevier CRediT guidance via search

## Triage (advisor) → local fate

| # | Item | Advisor | Local fate |
|---|------|---------|------------|
| 1 | Authors / affiliations | D | Journal-safe working-draft placeholders |
| 2 | Nested CRPS beyond Chowilla | B | Ran Carlisle nested CV anyway (cheap); Burnett left as scope boundary |
| 3 | Oracle factorial swaps | B | Closed as path-ordered ladder wording |
| 4 | Package versions | A | Pinned from live venv + hardware query |
| 5 | Full-TS Chowilla/Burnett | B | Closed Limitation with ~199 GB vs ~128 GB |
| 6 | Brisbane appendix | C | Future external replication only |
| 7 | FloodCastBench | C | Future work; removed TODO tone |
| 8 | Zone contiguity | A | Cheap 8-NN diagnostic on Carlisle |
| 9 | Geographic partition factorial | C | Future work |
| 10 | Carlisle equal-capacity | A | Ran; documented in `05_carlisle_capacity.md` |
| 11 | CRediT / COI / acknowledgements | D | Neutral placeholders |
| 12 | Limitations rewrite | B | Adopted advisor structure with local Carlisle nuance |

## Advice accepted vs rejected

**Accepted:** Remove 待补充/待修改 tokens; pin env; finish Carlisle capacity; close full-TS/Brisbane/FloodCastBench as boundaries; path-order O1–O4 wording; keep metadata out of Limitations; novelty = falsification-oriented diagnostics.

**Partially accepted:** Zone contiguity — ran cheap 8-NN purity (≈0.95 locally when XY included) rather than full component maps; wording stresses no hard contiguity constraint.

**Rejected / amended:** Advisor B for all nested CV beyond Chowilla — we still ran Carlisle nested CV because it was cheap from saved state. Advisor phrasing that localisation has “no surviving support in these public folds” is narrowed: Carlisle Max shows residual stacking can help RMSE when global SVD is rank-capped; Chowilla/Burnett remain the capacity-matched anti-cases.
