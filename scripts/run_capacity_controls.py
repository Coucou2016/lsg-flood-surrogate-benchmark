"""Run capacity-control workflows sequentially; log exit/runtime to JSONL."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
LOG = ROOT / "outputs" / "evaluation" / "capacity_controls_runlog.jsonl"


def run(name: str, cmd: list[str]) -> dict:
    print(f"\n=== START {name} ===", flush=True)
    print(" ".join(cmd), flush=True)
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(ROOT))
    wall = time.perf_counter() - t0
    row = {
        "name": name,
        "cmd": cmd,
        "exit": int(proc.returncode),
        "wall_s": float(wall),
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    print(f"=== END {name} exit={proc.returncode} wall_s={wall:.1f} ===", flush=True)
    return row


def main() -> None:
    jobs = [
        (
            "chowilla_hlsg_restore",
            [
                str(PY),
                "scripts/run_lsg_workflow.py",
                "--config",
                "config/chowilla.yaml",
                "--variants",
                "lsg_max",
                "--no-pred-examples",
                "--summary-out",
                "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max_capacity_rerun.json",
            ],
        ),
        (
            "chowilla_global_matched15",
            [
                str(PY),
                "scripts/run_lsg_workflow.py",
                "--config",
                "config/chowilla_global_matched15.yaml",
                "--variants",
                "lsg_max",
                "--no-pred-examples",
                "--summary-out",
                "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_global_matched15_max.json",
            ],
        ),
        (
            "chowilla_hlsg_budget3",
            [
                str(PY),
                "scripts/run_lsg_workflow.py",
                "--config",
                "config/chowilla_hlsg_budget3.yaml",
                "--variants",
                "lsg_max",
                "--no-pred-examples",
                "--summary-out",
                "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_budget3_max.json",
            ],
        ),
        (
            "chowilla_global_baseline_rerun",
            [
                str(PY),
                "scripts/run_lsg_workflow.py",
                "--config",
                "config/chowilla_global.yaml",
                "--variants",
                "lsg_max",
                "--no-pred-examples",
                "--summary-out",
                "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_global_max_capacity_rerun.json",
            ],
        ),
        (
            "chowilla_nzones_2",
            [
                str(PY),
                "scripts/run_lsg_workflow.py",
                "--config",
                "config/chowilla_nzones_2.yaml",
                "--variants",
                "lsg_max",
                "--no-pred-examples",
                "--summary-out",
                "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_nzones2_max.json",
            ],
        ),
        (
            "chowilla_nzones_6",
            [
                str(PY),
                "scripts/run_lsg_workflow.py",
                "--config",
                "config/chowilla_nzones_6.yaml",
                "--variants",
                "lsg_max",
                "--no-pred-examples",
                "--summary-out",
                "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_nzones6_max.json",
            ],
        ),
        (
            "chowilla_inducing_m2",
            [
                str(PY),
                "scripts/run_lsg_workflow.py",
                "--config",
                "config/chowilla_inducing_m2.yaml",
                "--variants",
                "lsg_max",
                "--no-pred-examples",
                "--summary-out",
                "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_inducing_m2_max.json",
            ],
        ),
        (
            "chowilla_inducing_m8",
            [
                str(PY),
                "scripts/run_lsg_workflow.py",
                "--config",
                "config/chowilla_inducing_m8.yaml",
                "--variants",
                "lsg_max",
                "--no-pred-examples",
                "--summary-out",
                "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_inducing_m8_max.json",
            ],
        ),
        (
            "chowilla_inducing_m28",
            [
                str(PY),
                "scripts/run_lsg_workflow.py",
                "--config",
                "config/chowilla_inducing_m28.yaml",
                "--variants",
                "lsg_max",
                "--no-pred-examples",
                "--summary-out",
                "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_inducing_m28_max.json",
            ],
        ),
    ]
    # Optional subset via argv names
    wanted = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    results = []
    for name, cmd in jobs:
        if wanted is not None and name not in wanted:
            continue
        results.append(run(name, cmd))
        if results[-1]["exit"] != 0:
            print(f"STOP after failure: {name}", flush=True)
            break
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
