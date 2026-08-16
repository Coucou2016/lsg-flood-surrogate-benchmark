# Paper vs research report — boundary brief

## Intended split

| Belongs in **paper** (`docs/paper/manuscript.md`) | Belongs in **research report** (`docs/report/report.md`) |
| --- | --- |
| Scientific motivation, RQs, methods equations, protocols | Local chronology, failed attempts, SGPR debugging story |
| Public Figshare DOI + public GitHub for code/data | Absolute Windows paths, host brand/RAM diary |
| Capacity-controlled results & honest negative finding | Commands, wall-clock times, junction/MD5 ingest notes |
| Closed Limitations prose (no open TODOs) | “未运行” with measured justification; engineering logs |
| Author placeholders: “[To be finalized]” only | ChatGPT/Cursor session URLs, advisor logs |
| Third-person / standard scientific English | Chinese process narrative OK in report |

## Known leakage themes already present in the manuscript (audit seed)

Please read the current GitHub `manuscript.md` and **list every phrase/theme that violates the boundary**, citing section + short quote or paraphrase. Seed list from a local audit (verify / extend):

1. **Repo path cataloguing in Methods / Experimental design** — YAML config filenames, `scripts/*.py`, `outputs/evaluation/.../*.json`, `outputs/figures/` as if they were Methods prose rather than Availability pointers.
2. **Chinese process token** — “缺数据” in Results / Appendix for missing hydrographs (should be closed English limitation language).
3. **Process meta** — “an early reading of our own runs”; “which an earlier reading of our runs treated as…” (narrative of reinterpretation belongs in report or should be neutralized).
4. **Hardware diary in Section 3.8** — Dell Precision / Xeon / RAM / Windows build as Methods detail (journal-dependent; often SI or Availability, not core Methods).
5. **Appendix C “Completed in this revision”** — revision-log tone; cite of `docs/paper/05_carlisle_capacity.md` is report/handoff language.
6. **Table 1 config columns** — `` `config/carlisle.yaml` `` style cells may be too repo-internal for a journal table.
7. **Data Availability** — listing `outputs/...` without the public repository URL as the primary locator.

## Ask ChatGPT

1. Produce a **scrub list**: every violating phrase (section heading + quote theme), severity (must-fix / optional), and a suggested academic replacement or “move to report”.
2. Propose a clean **Data and code availability** paragraph that points to the public GitHub repo and Figshare DOI **without** private absolute paths.
3. Flag any report content that should **not** migrate into the paper (especially Chinese chronology and ChatGPT URLs).
