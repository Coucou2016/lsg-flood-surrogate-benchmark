#!/usr/bin/env python3
"""Sync selected public-safe paths from workspace -> staging publish copy."""
from __future__ import annotations

import shutil
from pathlib import Path

WS = Path(r"I:\Projects\20260522-LSG-WRR")
ST = Path(r"I:\Projects\_publish_lsg-flood-surrogate-benchmark")

FILES = [
    # paper / report
    "docs/paper/manuscript.md",
    "docs/paper/manuscript.html",
    "docs/paper/manuscript.pdf",
    "docs/paper/00_progress_review.md",
    "docs/paper/02_paper_framework.md",
    "docs/paper/04_capacity_controls.md",
    "docs/paper/05_carlisle_capacity.md",
    "docs/paper/chatgpt_review_notes_2026-08-16_manuscript_todo.md",
    "docs/paper/_build_html.py",
    "docs/report/report.md",
    "docs/report/report.html",
    "docs/report/report.pdf",
    "docs/report/_build_summary.json",
    # scripts
    "scripts/build_lsg_research_report.py",
    "scripts/validate_report_html.py",
    "scripts/run_capacity_controls.py",
    "scripts/diagnose_burnett_hlsg_gap.py",
    "scripts/nested_crps_scale_cv.py",
    "scripts/_print_capacity_metrics.py",
    "scripts/_patch_capacity_configs.py",
    "scripts/run_lsg_workflow.py",
    # code + tests
    "lsg/eof.py",
    "lsg/base.py",
    "tests/test_eof.py",
    "tests/test_zoning.py",
    # configs
    "config/burnett_global_matched18.yaml",
    "config/chowilla_global_matched15.yaml",
    "config/chowilla_global_inducing_m2.yaml",
    "config/chowilla_hlsg_budget3.yaml",
    "config/chowilla_inducing_m2.yaml",
    "config/chowilla_inducing_m8.yaml",
    "config/chowilla_inducing_m28.yaml",
    "config/chowilla_nzones_2.yaml",
    "config/chowilla_nzones_6.yaml",
    "config/chowilla_global.yaml",  # models path fix
    "config/carlisle_global.yaml",
    "config/carlisle_global_matched13.yaml",
    "config/carlisle_hlsg_budget1.yaml",
    # evaluation JSON
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_global_max_capacity_rerun.json",
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max_capacity_rerun.json",
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_global_matched15_max.json",
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_global_inducing_m2_max.json",
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_inducing_m2_max.json",
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_inducing_m8_max.json",
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_inducing_m28_max.json",
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_nzones2_max.json",
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_nzones6_max.json",
    "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_budget3_max.json",
    "outputs/evaluation/chowilla/nested_crps_scale_cv.json",
    "outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_global_matched18_max.json",
    "outputs/evaluation/burnett/diagnose_hlsg_o2_vs_rmse.json",
    "outputs/evaluation/carlisle/workflow_summary_grp1_wse_ext_global_max_capacity.json",
    "outputs/evaluation/carlisle/workflow_summary_grp1_wse_ext_global_matched13_max.json",
    "outputs/evaluation/carlisle/workflow_summary_grp1_wse_ext_hlsg_budget1_max.json",
    "outputs/evaluation/carlisle/nested_crps_scale_cv.json",
    "outputs/evaluation/carlisle/zone_contiguity_diagnostic.json",
]

OPTIONAL = [
    "outputs/evaluation/pytest_capacity_controls.txt",
    # OA reference papers (CC BY / CC BY-NC) — Elsevier VoR never listed here
    "docs/references/README.md",
    "docs/references/exemplar_conventions.md",
    "docs/references/Fraehr_2022_WRR_Upskilling_LF_Hydrodynamic_LSG.pdf",
    "docs/references/Fraehr_2022_WRR_Upskilling_LF_Hydrodynamic_LSG.md",
    "docs/references/Fraehr_2023_WRR_Fast_Accurate_Hybrid_Floodplain_LSG.pdf",
    "docs/references/Fraehr_2023_WRR_Fast_Accurate_Hybrid_Floodplain_LSG.md",
    "docs/references/Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.pdf",
    "docs/references/Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.md",
    "docs/references/Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.from_pdf.md",
    "scripts/make_figures.py",
    "lsg/figstyle.py",
    "outputs/figures/figure_manifest.json",
]


def main() -> None:
    copied = 0
    missing = []
    for rel in FILES + OPTIONAL:
        src = WS / rel
        dst = ST / rel
        if not src.exists():
            missing.append(rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
        print(f"OK {rel}")
    print(f"copied={copied} missing={len(missing)}")
    for m in missing:
        print(f"MISS {m}")


if __name__ == "__main__":
    main()
