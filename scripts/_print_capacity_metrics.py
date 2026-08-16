import json
from pathlib import Path

files = [
    "workflow_summary_grp1_wse_ext_hlsg_max_capacity_rerun.json",
    "workflow_summary_grp1_wse_ext_global_matched15_max.json",
    "workflow_summary_grp1_wse_ext_hlsg_budget3_max.json",
    "workflow_summary_grp1_wse_ext_global_max_capacity_rerun.json",
]
print("file | CSI | RMSE | O2-O1 | gp_dim")
for f in files:
    d = json.loads(Path("outputs/evaluation/chowilla", f).read_text(encoding="utf-8"))
    wt = d["score_protocol"]["lsg_max"]["wet_train"]
    eb = [r for r in d["lsg_max"]["error_budget"] if r["split"] == "test"][0]
    cap = d["lsg_max"]["capacity"]
    print(
        f,
        round(wt["csi"], 6),
        round(wt["rmse"], 6),
        round(eb["o2_minus_o1"], 6),
        cap.get("gp_input_dim_wse"),
    )
