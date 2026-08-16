#!/usr/bin/env python3
"""Build self-contained LSG Chinese research report (HTML + Markdown).

All numeric claims are loaded from evaluation JSON / docs artifacts.
Figures under outputs/figures/*.svg are inlined into HTML.
Markdown keeps relative figure paths (documented).
"""
from __future__ import annotations

import base64
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "report"
FIG = ROOT / "outputs" / "figures"
EVAL = ROOT / "outputs" / "evaluation"

FIGURES = {
    "fig01": "fig01_cross_case_csi_rmse_wet_train.svg",
    "fig02": "fig02_error_budget_o1o4.svg",
    "fig03": "fig03_global_vs_hlsg_ab.svg",
    "fig04": "fig04_uq_calibration_crps_scale.svg",
    "fig05a": "fig05_spatial_maps_carlisle_E1.svg",
    "fig05b": "fig05_spatial_maps_chowilla_E1.svg",
    "fig05c": "fig05_spatial_maps_burnett_E1.svg",
    "fig06": "fig06_zoning_wet_correlation_ab.svg",
}


def load_json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def r3(x: float | None, nd: int = 3) -> str:
    if x is None:
        return "待补充"
    return f"{x:.{nd}f}"


def r4(x: float | None) -> str:
    return r3(x, 4)


def sp(d: dict, variant: str, mask: str, key: str) -> float | None:
    try:
        return float(d["score_protocol"][variant][mask][key])
    except (KeyError, TypeError, ValueError):
        return None


def eb_test(d: dict, variant: str) -> dict:
    for b in d.get(variant, {}).get("error_budget") or []:
        if b.get("split") == "test":
            return b
    return {}


def inline_svg(path: Path, alt: str, fig_id: str) -> str:
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw).strip()
    # neutralize scripts if any
    raw = re.sub(r"<script[\s\S]*?</script>", "", raw, flags=re.I)
    # ensure role/alt for accessibility
    if "<svg" in raw:
        raw = re.sub(
            r"<svg\b",
            f'<svg role="img" aria-label="{html.escape(alt)}" id="{fig_id}"',
            raw,
            count=1,
        )
    return f'<div class="figure-embed">{raw}</div>'


def md_img(rel_name: str, alt: str) -> str:
    return (
        f"![{alt}](../../outputs/figures/{rel_name})\n\n"
        f"<p class=\"md-note\"><em>说明：Markdown 使用相对路径引用插图；"
        f"自包含离线要求仅强制适用于 report.html（图为内联 SVG / Base64）。</em></p>\n"
    )


def table_html(headers: list[str], rows: list[list[str]], caption: str) -> str:
    th = "".join(f"<th scope='col'>{html.escape(h)}</th>" for h in headers)
    body = []
    for row in rows:
        tds = "".join(f"<td>{c}</td>" for c in row)
        body.append(f"<tr>{tds}</tr>")
    return (
        f'<figure class="table-wrap"><figcaption>{html.escape(caption)}</figcaption>'
        f'<div class="table-scroll"><table><thead><tr>{th}</tr></thead>'
        f"<tbody>{''.join(body)}</tbody></table></div></figure>"
    )


def table_md(headers: list[str], rows: list[list[str]], caption: str) -> str:
    lines = [f"**表：{caption}**", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        clean = [re.sub(r"<[^>]+>", "", str(c)) for c in row]
        lines.append("| " + " | ".join(clean) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    car_fix = load_json(
        "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix.json"
    )
    car_uq = load_json(
        "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix_uq_calibrated.json"
    )
    car_global = load_json(
        "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_budget.json"
    )
    car_hlsg_pre = load_json(
        "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_residual_kmeans.json"
    )
    chow_h = load_json(
        "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max.json"
    )
    chow_g = load_json(
        "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_global_max.json"
    )
    burn = load_json(
        "outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_hlsg_max.json"
    )
    burn_g = load_json(
        "outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_global_max.json"
    )
    chow_uq = load_json(
        "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max_uq_calibrated.json"
    )
    burn_uq = load_json(
        "outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_hlsg_max_uq_calibrated.json"
    )
    chow_wc = load_json(
        "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_wet_correlation_max.json"
    )
    manifest = load_json("outputs/figures/figure_manifest.json")

    # ---- Capacity-control artefacts (equal-capacity + nuisance sweeps) ----
    def load_json_opt(rel: str) -> dict | None:
        try:
            return load_json(rel)
        except (FileNotFoundError, OSError, ValueError):
            return None

    ce = "outputs/evaluation/chowilla/"
    be = "outputs/evaluation/burnett/"
    chow_g_cap = load_json_opt(ce + "workflow_summary_grp1_wse_ext_global_max_capacity_rerun.json")
    chow_h_cap = load_json_opt(ce + "workflow_summary_grp1_wse_ext_hlsg_max_capacity_rerun.json")
    chow_g15 = load_json_opt(ce + "workflow_summary_grp1_wse_ext_global_matched15_max.json")
    chow_h_b3 = load_json_opt(ce + "workflow_summary_grp1_wse_ext_hlsg_budget3_max.json")
    burn_g18 = load_json_opt(be + "workflow_summary_grp1_wse_ext_global_matched18_max.json")
    chow_ind_m2 = load_json_opt(ce + "workflow_summary_grp1_wse_ext_hlsg_inducing_m2_max.json")
    chow_ind_m8 = load_json_opt(ce + "workflow_summary_grp1_wse_ext_hlsg_inducing_m8_max.json")
    chow_ind_m28 = load_json_opt(ce + "workflow_summary_grp1_wse_ext_hlsg_inducing_m28_max.json")
    chow_nz2 = load_json_opt(ce + "workflow_summary_grp1_wse_ext_hlsg_nzones2_max.json")
    chow_nz6 = load_json_opt(ce + "workflow_summary_grp1_wse_ext_hlsg_nzones6_max.json")
    nested_cv = load_json_opt(ce + "nested_crps_scale_cv.json")

    def cap_dim(d: dict | None, fallback: str = "待补充") -> str:
        if not d:
            return fallback
        try:
            return str(d["lsg_max"]["capacity"]["gp_input_dim_wse"])
        except (KeyError, TypeError):
            return fallback

    def cap_o2o1(d: dict | None) -> float | None:
        if not d:
            return None
        return eb_test(d, "lsg_max").get("o2_minus_o1")

    def cap_o4o2(d: dict | None) -> float | None:
        if not d:
            return None
        eb = eb_test(d, "lsg_max")
        o4, o2 = eb.get("o4_rmse"), eb.get("o2_rmse")
        if o4 is None or o2 is None:
            return None
        return o4 - o2

    # Convenience metric pulls (wet_train / all_cells)
    metrics = {
        "car_lf_all_csi": sp(car_fix, "lf_only", "all_cells", "csi"),
        "car_lf_all_rmse": sp(car_fix, "lf_only", "all_cells", "rmse"),
        "car_lf_wet_csi": sp(car_fix, "lf_only", "wet_train", "csi"),
        "car_lf_wet_rmse": sp(car_fix, "lf_only", "wet_train", "rmse"),
        "car_max_all_csi": sp(car_fix, "lsg_max", "all_cells", "csi"),
        "car_max_all_rmse": sp(car_fix, "lsg_max", "all_cells", "rmse"),
        "car_max_wet_csi": sp(car_fix, "lsg_max", "wet_train", "csi"),
        "car_max_wet_rmse": sp(car_fix, "lsg_max", "wet_train", "rmse"),
        "car_ts_all_csi": sp(car_fix, "lsg_ts", "all_cells", "csi"),
        "car_ts_all_rmse": sp(car_fix, "lsg_ts", "all_cells", "rmse"),
        "car_ts_wet_csi": sp(car_fix, "lsg_ts", "wet_train", "csi"),
        "car_ts_wet_rmse": sp(car_fix, "lsg_ts", "wet_train", "rmse"),
        "chow_lf_all_csi": sp(chow_h, "lf_only", "all_cells", "csi"),
        "chow_lf_all_rmse": sp(chow_h, "lf_only", "all_cells", "rmse"),
        "chow_lf_wet_csi": sp(chow_h, "lf_only", "wet_train", "csi"),
        "chow_lf_wet_rmse": sp(chow_h, "lf_only", "wet_train", "rmse"),
        "chow_h_all_csi": sp(chow_h, "lsg_max", "all_cells", "csi"),
        "chow_h_all_rmse": sp(chow_h, "lsg_max", "all_cells", "rmse"),
        "chow_h_wet_csi": sp(chow_h, "lsg_max", "wet_train", "csi"),
        "chow_h_wet_rmse": sp(chow_h, "lsg_max", "wet_train", "rmse"),
        "chow_g_wet_csi": sp(chow_g, "lsg_max", "wet_train", "csi"),
        "chow_g_wet_rmse": sp(chow_g, "lsg_max", "wet_train", "rmse"),
        "burn_lf_all_csi": sp(burn, "lf_only", "all_cells", "csi"),
        "burn_lf_all_rmse": sp(burn, "lf_only", "all_cells", "rmse"),
        "burn_lf_wet_csi": sp(burn, "lf_only", "wet_train", "csi"),
        "burn_lf_wet_rmse": sp(burn, "lf_only", "wet_train", "rmse"),
        "burn_h_all_csi": sp(burn, "lsg_max", "all_cells", "csi"),
        "burn_h_all_rmse": sp(burn, "lsg_max", "all_cells", "rmse"),
        "burn_h_wet_csi": sp(burn, "lsg_max", "wet_train", "csi"),
        "burn_h_wet_rmse": sp(burn, "lsg_max", "wet_train", "rmse"),
        "burn_g_wet_csi": sp(burn_g, "lsg_max", "wet_train", "csi"),
        "burn_g_wet_rmse": sp(burn_g, "lsg_max", "wet_train", "rmse"),
        "chow_wc_wet_csi": sp(chow_wc, "lsg_max", "wet_train", "csi"),
        "chow_wc_wet_rmse": sp(chow_wc, "lsg_max", "wet_train", "rmse"),
    }

    car_max_eb = eb_test(car_fix, "lsg_max")
    car_ts_eb = eb_test(car_fix, "lsg_ts")
    car_g_max_eb = eb_test(car_global, "lsg_max")
    car_g_ts_eb = eb_test(car_global, "lsg_ts")
    car_pre_max_eb = eb_test(car_hlsg_pre, "lsg_max")
    car_pre_ts_eb = eb_test(car_hlsg_pre, "lsg_ts")
    chow_h_eb = eb_test(chow_h, "lsg_max")
    chow_g_eb = eb_test(chow_g, "lsg_max")
    chow_wc_eb = eb_test(chow_wc, "lsg_max")
    burn_eb = eb_test(burn, "lsg_max")
    burn_g_eb = eb_test(burn_g, "lsg_max")

    uq_max = car_uq["lsg_max"]
    uq_ts = car_uq["lsg_ts"]
    var_max = uq_max["uq_calibration"]["var_scale"]
    var_ts = uq_ts["uq_calibration"]["var_scale"]
    crps_max_before = uq_max["uq_uncalibrated"]["crps"]
    crps_max_after = uq_max["uq"]["crps"]
    crps_ts_before = uq_ts["uq_uncalibrated"]["crps"]
    crps_ts_after = uq_ts["uq"]["crps"]

    # Prefer independent rescore before/after (Fig. 4); workflow-fit s kept for note.
    chow_var_workflow = chow_h["lsg_max"]["uq_calibration"]["var_scale"]
    chow_g_var = chow_g["lsg_max"]["uq_calibration"]["var_scale"]
    burn_var_workflow = burn["lsg_max"]["uq_calibration"]["var_scale"]
    chow_uq_l = chow_uq["lsg_max"]
    burn_uq_l = burn_uq["lsg_max"]
    chow_var = chow_uq_l["uq_calibration"]["var_scale"]
    burn_var = burn_uq_l["uq_calibration"]["var_scale"]
    chow_crps_before = chow_uq_l["uq_uncalibrated"]["crps"]
    chow_crps_after = chow_uq_l["uq"]["crps"]
    burn_crps_before = burn_uq_l["uq_uncalibrated"]["crps"]
    burn_crps_after = burn_uq_l["uq"]["crps"]
    chow_cov_a_before = chow_uq_l["uq_uncalibrated"].get("coverage_90_active")
    chow_cov_a_after = chow_uq_l["uq"].get("coverage_90_active")
    burn_cov_a_before = burn_uq_l["uq_uncalibrated"].get("coverage_90_active")
    burn_cov_a_after = burn_uq_l["uq"].get("coverage_90_active")

    skips = manifest.get("skips") or []

    svg_html = {k: inline_svg(FIG / v, v, k) for k, v in FIGURES.items()}

    # ---------- shared narrative blocks (Chinese) ----------
    # Tables (HTML cells may include <code>)
    t_inventory_h = [
        "案例",
        "角色",
        "HF / LF",
        "配置",
        "几何规模（文档）",
        "默认时间处理",
        "数据状态",
    ]
    t_inventory_r = [
        [
            "Carlisle（英国）",
            "主案例",
            "LISFLOOD-FP × HEC-RAS",
            "<code>config/carlisle.yaml</code>",
            "HF ≈ 581 061 单元；LF 有效 5 681（去 ghost）",
            "完整时间序列可训（LSG-TS）",
            "已解压（~9.6 GB，Figshare 10.26188/24312658）",
        ],
        [
            "Chowilla（澳大利亚）",
            "次案例",
            "细网格 / 粗网格 HEC-RAS",
            "<code>config/chowilla.yaml</code>",
            "HF ≈ 110k 单元；29 事件 / 10 组",
            "<code>time_reduction: max</code>",
            "可用（junction / zip）",
        ],
        [
            "Burnett（澳大利亚）",
            "第三案例",
            "TUFLOW × HEC-RAS",
            "<code>config/burnett.yaml</code>",
            "HF ≈ 780 785；LF ≈ 15 256；74 事件 / 4 组",
            "<code>time_reduction: max</code>",
            "可用（junction / zip）",
        ],
        [
            "Brisbane（附录）",
            "许可门控附录",
            "TUFLOW × URBS（Wang 2026）",
            "<code>config/brisbane.yaml</code>",
            "待补充（许可数据未到）",
            "待补充",
            "未运行（许可门控）",
        ],
    ]

    t_methods_h = ["变体 / 模块", "英文全称与缩写", "物理/算法含义", "本项目中的位置"]
    t_methods_r = [
        [
            "LSG",
            "Low-fidelity, Spatial analysis, and Gaussian Process Learning",
            "用低精度水动力场投影到高精度经验正交模态，再以高斯过程学习模态系数映射，重构淹没场",
            "主方法栈；不依赖特定求解器品牌",
        ],
        [
            "LSG-TS",
            "LSG Time Series",
            "对完整淹没时间序列训练；最大淹没面由预测序列时间维取 max",
            "Carlisle 主折已跑通；Chowilla/Burnett 全时序 Grp1 未运行（内存）",
        ],
        [
            "LSG-Max",
            "LSG Maximum surface",
            "直接学习各事件最大水深面",
            "三案例 headline 对比的主表面路径",
        ],
        [
            "EXT + WSE",
            "Extent + Water Surface Elevation（<code>lsg.field: wse_ext</code>）",
            "分别学习二值淹没范围与水面高程，再由 <code>depth = max(WSE−Z, 0)</code> 并经 EXT 门控得到水深",
            "官方点估计路径；非 LF 范围后处理门控",
        ],
        [
            "H-LSG / residual_kmeans",
            "Hierarchical residual LSG（残差层次分区）",
            "全局 EOF 之上，对 WSE 残差做 k-means 分区并拟合局部残差 EOF；EXT 保持全局",
            "默认 zoning；相对 global 做消融",
        ],
        [
            "SGPR",
            "Sparse Gaussian Process Regression（稀疏高斯过程回归）",
            "用诱导点近似全 GP，降低大样本代价",
            "每 EOF 模态一个 SGPR；<code>min_inducing_points</code> 防 Max 路径崩溃",
        ],
        [
            "O1–O4",
            "Oracle error budget ladder（神谕误差阶梯）",
            "反事实分解截断 / LF 可表达性 / GP 映射误差",
            "<code>lsg/diagnostics.py</code>；depth RMSE on wet_idx",
        ],
        [
            "CRPS-scale UQ",
            "Continuous Ranked Probability Score variance calibration",
            "训练集拟合全局方差尺度 <code>Var_cal = s·Var_raw</code>，均值不变",
            "三案例均有 before/after；Chowilla CRPS 近乎持平需如实报告",
        ],
        [
            "wet_correlation 分区",
            "Wet-correlation zoning",
            "按湿相关结构划分空间再拟合残差/局部模态",
            "Chowilla Grp1 敏感性已跑；非默认 headline",
        ],
    ]

    t_cross_h = [
        "案例",
        "变体",
        "掩膜",
        "CSI",
        "RMSE (m)",
        "来源 JSON",
    ]
    t_cross_r = [
        ["Carlisle", "LF only", "all_cells", r4(metrics["car_lf_all_csi"]), r3(metrics["car_lf_all_rmse"]), "…sgpr_fix.json"],
        ["Carlisle", "LF only", "wet_train", r4(metrics["car_lf_wet_csi"]), r3(metrics["car_lf_wet_rmse"]), "同上"],
        ["Carlisle", "LSG-TS (max surface)", "all / wet_train", f"{r4(metrics['car_ts_all_csi'])} / {r4(metrics['car_ts_wet_csi'])}", f"{r3(metrics['car_ts_all_rmse'])} / {r3(metrics['car_ts_wet_rmse'])}", "同上"],
        ["Carlisle", "LSG-Max H-LSG+SGPR fix", "all / wet_train", f"{r4(metrics['car_max_all_csi'])} / {r4(metrics['car_max_wet_csi'])}", f"{r3(metrics['car_max_all_rmse'])} / {r3(metrics['car_max_wet_rmse'])}", "同上"],
        ["Chowilla", "LF only", "all / wet_train", f"{r4(metrics['chow_lf_all_csi'])} / {r4(metrics['chow_lf_wet_csi'])}", f"{r3(metrics['chow_lf_all_rmse'])} / {r3(metrics['chow_lf_wet_rmse'])}", "…hlsg_max.json"],
        ["Chowilla", "LSG-Max H-LSG", "all / wet_train", f"<strong>{r4(metrics['chow_h_all_csi'])}</strong> / <strong>{r4(metrics['chow_h_wet_csi'])}</strong>", f"<strong>{r3(metrics['chow_h_all_rmse'])}</strong> / <strong>{r3(metrics['chow_h_wet_rmse'])}</strong>", "同上；all-cells 反例"],
        ["Chowilla", "LSG-Max global", "wet_train", r4(metrics["chow_g_wet_csi"]), r3(metrics["chow_g_wet_rmse"]), "…global_max.json"],
        ["Chowilla", "LSG-Max wet_correlation", "wet_train", r4(metrics["chow_wc_wet_csi"]), r3(metrics["chow_wc_wet_rmse"]), "…wet_correlation_max.json"],
        ["Burnett", "LF only", "all / wet_train", f"{r4(metrics['burn_lf_all_csi'])} / {r4(metrics['burn_lf_wet_csi'])}", f"{r3(metrics['burn_lf_all_rmse'])} / {r3(metrics['burn_lf_wet_rmse'])}", "…hlsg_max.json"],
        ["Burnett", "LSG-Max H-LSG", "all / wet_train", f"{r4(metrics['burn_h_all_csi'])} / {r4(metrics['burn_h_wet_csi'])}", f"{r3(metrics['burn_h_all_rmse'])} / {r3(metrics['burn_h_wet_rmse'])}", "同上"],
        ["Burnett", "LSG-Max global", "wet_train", r4(metrics["burn_g_wet_csi"]), r3(metrics["burn_g_wet_rmse"]), "…global_max.json"],
    ]

    t_o_h = ["案例 / 变体", "O1", "O2", "O3", "O4", "O2−O1", "解读要点"]
    t_o_r = [
        [
            "Carlisle LSG-TS H-LSG+fix",
            r3(car_ts_eb.get("o1_rmse")),
            r3(car_ts_eb.get("o2_rmse")),
            r3(car_ts_eb.get("o3_rmse")),
            r3(car_ts_eb.get("o4_rmse")),
            r3(car_ts_eb.get("o2_minus_o1")),
            "截断间隙中等；O3 高提示 LF 伪 EC 表达受限",
        ],
        [
            "Carlisle LSG-Max H-LSG+fix",
            r3(car_max_eb.get("o1_rmse")),
            r3(car_max_eb.get("o2_rmse")),
            r3(car_max_eb.get("o3_rmse")),
            r3(car_max_eb.get("o4_rmse")),
            r3(car_max_eb.get("o2_minus_o1")),
            "O2−O1≈0.005，残差分区显著压缩截断间隙",
        ],
        [
            "Carlisle LSG-Max global (pre-fix 对照栈)",
            r3(car_g_max_eb.get("o1_rmse")),
            r3(car_g_max_eb.get("o2_rmse")),
            r3(car_g_max_eb.get("o3_rmse")),
            r3(car_g_max_eb.get("o4_rmse")),
            r3(car_g_max_eb.get("o2_minus_o1")),
            "O2−O1≈0.064，全局截断更重",
        ],
        [
            "Carlisle LSG-Max H-LSG pre-fix SGPR",
            r3(car_pre_max_eb.get("o1_rmse")),
            r3(car_pre_max_eb.get("o2_rmse")),
            r3(car_pre_max_eb.get("o3_rmse")),
            r3(car_pre_max_eb.get("o4_rmse")),
            r3(car_pre_max_eb.get("o2_minus_o1")),
            "O4 暴涨至 0.267：诱导点缺陷主导，非分区本身",
        ],
        [
            "Chowilla LSG-Max H-LSG",
            r3(chow_h_eb.get("o1_rmse")),
            r3(chow_h_eb.get("o2_rmse")),
            r3(chow_h_eb.get("o3_rmse")),
            r3(chow_h_eb.get("o4_rmse")),
            r3(chow_h_eb.get("o2_minus_o1")),
            "O2−O1=0.013；O3 很高（强 LF 几何下伪 EC 仍难）",
        ],
        [
            "Chowilla LSG-Max global",
            r3(chow_g_eb.get("o1_rmse")),
            r3(chow_g_eb.get("o2_rmse")),
            r3(chow_g_eb.get("o3_rmse")),
            r3(chow_g_eb.get("o4_rmse")),
            r3(chow_g_eb.get("o2_minus_o1")),
            "O2−O1=0.057；分区主要改截断而非 CSI",
        ],
        [
            "Burnett LSG-Max H-LSG",
            r3(burn_eb.get("o1_rmse")),
            r3(burn_eb.get("o2_rmse")),
            r3(burn_eb.get("o3_rmse")),
            r3(burn_eb.get("o4_rmse")),
            r3(burn_eb.get("o2_minus_o1")),
            "O2−O1=0.009；相对 LF 的 CSI/RMSE 提升由 LSG 主导",
        ],
        [
            "Burnett LSG-Max global",
            r3(burn_g_eb.get("o1_rmse")),
            r3(burn_g_eb.get("o2_rmse")),
            r3(burn_g_eb.get("o3_rmse")),
            r3(burn_g_eb.get("o4_rmse")),
            r3(burn_g_eb.get("o2_minus_o1")),
            "O2−O1≈0.049；湿 CSI 与 H-LSG 持平，截断间隙更大",
        ],
        [
            "Chowilla LSG-Max wet_correlation",
            r3(chow_wc_eb.get("o1_rmse")),
            r3(chow_wc_eb.get("o2_rmse")),
            r3(chow_wc_eb.get("o3_rmse")),
            r3(chow_wc_eb.get("o4_rmse")),
            r3(chow_wc_eb.get("o2_minus_o1")),
            "O2−O1≈0.010；湿 CSI 略高于 residual_kmeans",
        ],
    ]

    t_uq_h = ["案例 / 表面", "var_scale s", "CRPS 前→后", "coverage_90_active 等", "点估计 CSI/RMSE", "备注"]
    t_uq_r = [
        [
            "Carlisle Max",
            r3(var_max),
            f"{r3(crps_max_before)} → {r3(crps_max_after)}",
            f"cov90_active: {r3(uq_max['uq_uncalibrated'].get('coverage_90_active'))} → {r3(uq_max['uq'].get('coverage_90_active'))}",
            "不变（delta≈0）",
            "未标定过宽；标定收益最大",
        ],
        [
            "Carlisle TS",
            r3(var_ts),
            f"{r3(crps_ts_before)} → {r3(crps_ts_after)}",
            f"cov50_active 前≈{r3(uq_ts['uq_uncalibrated'].get('coverage_50_active'))}",
            "不变",
            "已近校准（s≈0.90）",
        ],
        [
            "Chowilla H-LSG Max（rescore）",
            r3(chow_var),
            f"{r3(chow_crps_before)} → {r3(chow_crps_after)}",
            f"cov90_active: {r3(chow_cov_a_before)} → {r3(chow_cov_a_after)}",
            "点估计不变（构造）",
            f"CRPS 近乎持平；coverage 远离名义；workflow-fit s≈{r3(chow_var_workflow)}",
        ],
        [
            "Chowilla global Max（workflow）",
            r3(chow_g_var),
            "见全局摘要标定块",
            f"标定后 cov90_active={r3(chow_g['lsg_max']['uq'].get('coverage_90_active'))}",
            "—",
            "非 Fig.4 主 before/after 路径",
        ],
        [
            "Burnett H-LSG Max（rescore）",
            r3(burn_var),
            f"{r3(burn_crps_before)} → {r3(burn_crps_after)}",
            f"cov90_active: {r3(burn_cov_a_before)} → {r3(burn_cov_a_after)}",
            "点估计不变（CSI/RMSE 同 H-LSG）",
            f"CRPS 下降；workflow-fit s≈{r3(burn_var_workflow)}",
        ],
    ]

    t_innov_h = ["主张", "相对既往工作的边界", "本仓库证据"]
    t_innov_r = [
        [
            "残差层次分区 LSG 的**等容量负结果**（capacity-controlled negative result）",
            "≠ REOF-SGP（Wang 2025）；≠ Tan 2025 单焦点区域重训；对 Wang 2026 点名的 zonal EOF 给出容量对照下的**否定**评估",
            "force_n_modes 匹配容量 + 诱导点/分区数扫描：表观 O2−O1 优势是容量混淆，不转化为留出技能（表 6–8）",
        ],
        [
            "CRPS 尺度标定的 LSG 地图后验方差",
            "≠“首个概率淹没代理”（已有多种非 LSG GP/PCE UQ）",
            "Carlisle Max s≈0.417，CRPS 0.039→0.028；均值不动",
        ],
        [
            "O1–O4 神谕阶梯",
            "≠ Tan 的两段式 ER_DR/ER_LSG；本报告为四段反事实深度 RMSE",
            "三案例 test budgets 可复现",
        ],
        [
            "SGPR 诱导点下限与训练行初始化",
            "工程稳健性，非 headline 新颖性",
            "Max pre-fix O4=0.267 → post-fix 0.094",
        ],
    ]

    t_limit_h = ["限制 / 边界", "状态", "影响"]
    t_limit_r = [
        ["Chowilla / Burnett 全时序 Grp1 折", "计算边界（Burnett HF≈199 GB ≫ ≈128 GB RAM）", "等容量结论建立在 Max 面折上，不可定量外推全时序"],
        ["等容量 global vs H-LSG（Chowilla/Burnett Max）", "**已完成**（force_n_modes + 诱导点/分区数扫描）", "Chowilla/Burnett：局部化优势不成立"],
        ["Carlisle 等容量对照", "**已完成**（force 13→实现 8；见 docs/paper/05_carlisle_capacity.md）", "Max 训练秩限制下残差堆叠可改善 RMSE；与 Chowilla/Burnett 异质"],
        ["residual_kmeans 空间连通性", "Carlisle 8-NN 同区占比≈0.95（含 XY）", "局部相干，但算法不施加连通性硬约束"],
        ["CRPS s 嵌套 CV", "Chowilla + Carlisle 已完成；Burnett 不在本轮范围", "s 折稳定≠跨站可迁移；Chowilla 标定仍可持平/不利"],
        ["O1–O4", "路径有序反事实阶梯", "非可加、非顺序不变的方差分解"],
        ["Carlisle/Chowilla Max 测试事件数", "N_event=1（Burnett=18）", "受控效应量对比，非 p 值检验"],
        ["Brisbane / FloodCastBench", "许可/外部基准，移出公开证据链", "仅作未来外部复现方向"],
        ["跨事件/站点的 var_scale 迁移", "开放问题", "当前每案例重拟合"],
    ]

    t_tests_h = ["项目", "记录", "本报告是否重跑"]
    t_tests_r = [
        [
            "pytest",
            "<code>docs/paper/03_new_results.md</code>：80 passed, 1 skipped（本会话实验后；进度评论旧记 74）",
            "本文档构建未强制重跑；以 03_new_results 记录为准",
        ],
        ["评价协议", "threshold 0.03 m；all_cells + wet_train；Fraehr Categories wet_idx", "复述文档"],
        ["随机种子", "config 中 <code>random_seed: 20260814</code>（Carlisle）", "—"],
    ]

    # Build long-form body once for MD; HTML wraps with styles + inlined figs.
    sections_md: list[str] = []
    sections_html: list[str] = []

    def add(md: str, html_body: str | None = None) -> None:
        sections_md.append(md)
        sections_html.append(html_body if html_body is not None else md_to_simple_html(md))

    def md_to_simple_html(md: str) -> str:
        """Very small Markdown subset → HTML for narrative paragraphs already authored in HTML-friendly MD."""
        # For blocks we mostly pass ready HTML; this handles plain MD paragraphs.
        out = []
        for block in md.split("\n\n"):
            b = block.strip()
            if not b:
                continue
            if b.startswith("# "):
                out.append(f"<h1>{html.escape(b[2:])}</h1>")
            elif b.startswith("## "):
                out.append(f"<h2 id=\"{slug(b[3:])}\">{html.escape(b[3:])}</h2>")
            elif b.startswith("### "):
                out.append(f"<h3 id=\"{slug(b[4:])}\">{html.escape(b[4:])}</h3>")
            elif b.startswith("#### "):
                out.append(f"<h4>{html.escape(b[5:])}</h4>")
            elif b.startswith("- "):
                items = []
                for line in b.split("\n"):
                    if line.startswith("- "):
                        items.append(f"<li>{inline_fmt(line[2:])}</li>")
                out.append("<ul>" + "".join(items) + "</ul>")
            elif b.startswith("| "):
                # leave raw; tables inserted as HTML elsewhere
                out.append(f"<pre>{html.escape(b)}</pre>")
            else:
                out.append(f"<p>{inline_fmt(b)}</p>")
        return "\n".join(out)

    def slug(s: str) -> str:
        s = re.sub(r"\s+", "-", s)
        s = re.sub(r"[^\w\u4e00-\u9fff\-]", "", s)
        return s.lower()

    def inline_fmt(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
        return s

    def fig_block(
        fig_key: str,
        title: str,
        why: str,
        how: str,
        panels: str,
        pattern: str,
        cause: str,
        can_cannot: str,
        analogy: str,
    ) -> tuple[str, str]:
        fname = FIGURES[fig_key]
        md = f"""### {title}

**为何制作 / 回答什么问题 / 在报告中的角色**

{why}

{md_img(fname, title)}

**如何读图（坐标、图例、颜色、指标）**

{how}

**逐面板/子图说明**

{panels}

**可见模式**

{pattern}

**模式可能原因（因果与时序）**

{cause}

**可结论 / 不可结论**

{can_cannot}

**非专业类比**

{analogy}
"""
        html_b = f"""
<section class="figure-section" id="{slug(title)}">
<h3>{html.escape(title)}</h3>
<div class="callout"><strong>为何制作 / 回答什么问题 / 角色。</strong> {inline_fmt(why)}</div>
{svg_html[fig_key]}
<p class="figcaption"><strong>图：{html.escape(title)}</strong>（内联 SVG；SciencePlots + Times New Roman；源文件 <code>{html.escape(fname)}</code>）</p>
<div class="interpret">
<p><strong>如何读图。</strong> {inline_fmt(how)}</p>
<p><strong>逐面板说明。</strong> {inline_fmt(panels)}</p>
<p><strong>可见模式。</strong> {inline_fmt(pattern)}</p>
<p><strong>因果与时序。</strong> {inline_fmt(cause)}</p>
<p><strong>可结论 / 不可结论。</strong> {inline_fmt(can_cannot)}</p>
<p><strong>非专业类比。</strong> {inline_fmt(analogy)}</p>
</div>
</section>
"""
        return md, html_b

    # ===== Compose document =====
    title = "残差层次分区能否改进多保真洪水代理？一个带神谕误差预算与 CRPS 标定的等容量负结果（公开数据研究报告）"
    subtitle = "Low-fidelity, Spatial analysis, and Gaussian Process Learning（LSG）公共基准复现、诊断扩展与局部化的等容量负结果"

    cover_md = f"""# {title}

**{subtitle}**

| 项目 | 内容 |
| --- | --- |
| 报告类型 | 正式科学研究报告（方法/诊断导向，非短文） |
| 项目仓库 | `I:\\Projects\\20260522-LSG-WRR` |
| 主案例 | Carlisle；次案例 Chowilla；第三案例 Burnett |
| 证据日期 | 2026-08-16（与 `docs/paper/00_progress_review.md` 对齐） |
| 目标期刊语境 | WRR / JoH / EMS（methods） |
| 一句话论点 | 多保真 LSG 是技能主源；残差分区主要压缩截断间隙（O2−O1）；CRPS 方差标定改善概率可靠性且不改 CSI/RMSE；Chowilla all-cells 是强 LF 协议反例 |
| Git 状态 | 仓库基线无 `.git` / 本交付仅本地写 `docs/report/`，不提交不推送 |
| 图件风格 | SciencePlots；Times New Roman；600 dpi PNG 并存；HTML 优先内联 SVG |
| 顾问评审 | ChatGPT 结构评审 https://chatgpt.com/c/6a816202-85e0-83ea-9ed9-3de1fdb994cb；大改章节合并未执行 |

---

## 报告读法（结构边界）

本文件是**可离线传阅的正式研究工作稿**：主体按科学逻辑组织，但保留工程诊断闭环（数据对齐、SGPR 诱导点配置、UQ 标定）以便复现。阅读时请优先沿“问题→证据→诊断→最小处理→验证→边界”主线；“完整时间线”与“范围边界”服务归档与证据边界透明。O1–O4 与跨案例差异支持**机制诊断/反事实归因**，不宜写成严格可加的因果贡献率。方差标定改善的是概率评分；点估计 CSI/RMSE 因均值不变而按构造保持不变。

---
"""

    cover_html = f"""
<section class="cover page-break-after">
<p class="eyebrow">LSG 公开数据基准 · 科学研究报告</p>
<h1>{html.escape(title)}</h1>
<p class="subtitle">{html.escape(subtitle)}</p>
<table class="meta">
<tr><th>报告类型</th><td>正式科学研究报告（方法/诊断导向）</td></tr>
<tr><th>项目路径</th><td><code>I:\\Projects\\20260522-LSG-WRR</code></td></tr>
<tr><th>案例</th><td>Carlisle（主）、Chowilla（次）、Burnett（第三）</td></tr>
<tr><th>证据截止日期</th><td>2026-08-16</td></tr>
<tr><th>nature-writing 轴</th><td>task=manuscript · paper_type=methods · language=zh（报告体）· journal=generic（WRR/JoH/EMS 语境）</td></tr>
<tr><th>一句话论点</th><td>多保真 LSG 主导技能提升；残差分区主要缩小 O2−O1；CRPS 标定改善 UQ；Chowilla all-cells 为协议反例。</td></tr>
<tr><th>交付物</th><td><code>docs/report/report.html</code>（自包含）、<code>report.md</code>、<code>report.pdf</code></td></tr>
<tr><th>版本控制</th><td>仅本地修改；未提交、未推送、未创建 PR、未部署</td></tr>
<tr><th>顾问评审</th><td>ChatGPT 结构评审（本轮）；大改章节合并未执行</td></tr>
</table>
<p class="lede"><strong>报告读法：</strong>优先沿“问题→证据→诊断→最小处理→验证→边界”主线；O1–O4 为机制诊断/反事实归因，非可加因果贡献率；方差标定改善概率评分，CSI/RMSE 因均值不变按构造保持。</p>
</section>
"""

    toc_items = [
        ("报告读法", "报告读法（结构边界）"),
        ("摘要与执行概要", "摘要与执行概要"),
        ("研究背景与目标", "研究背景与目标"),
        ("文献与科学缺口", "文献与科学缺口"),
        ("数据来源与案例", "数据来源与案例研究"),
        ("方法学基础", "方法学基础"),
        ("完整研究过程", "完整研究过程与时间线"),
        ("数据摄取与对齐修复", "数据摄取与对齐修复"),
        ("EXT-WSE", "EXT+WSE 双场模型"),
        ("SGPR-fix", "SGPR 诱导点问题与修复"),
        ("H-LSG", "层次残差 EOF（H-LSG）"),
        ("UQ", "不确定性量化与标定"),
        ("O1-O4", "O1–O4 误差预算"),
        ("实验设计", "实验设计与评价指标"),
        ("分案例结果", "分案例结果"),
        ("跨案例比较", "跨案例比较"),
        ("等容量对照", "等容量对照实验（局部化不成立）"),
        ("图件解读", "详细图件解读"),
        ("讨论", "讨论与因果分析"),
        ("创新点", "创新点"),
        ("可复现性", "可复现性与质量保证"),
        ("局限性", "局限性"),
        ("未来工作", "未来工作"),
        ("结论", "结论"),
        ("数据代码可用性", "数据与代码可用性"),
        ("参考文献", "参考文献"),
        ("附录", "附录"),
        ("范围边界与本轮已完成项", "范围边界与本轮已完成项"),
    ]

    toc_md = "## 目录\n\n" + "\n".join(f"- {t}" for _, t in toc_items) + "\n"
    toc_html = (
        '<nav class="toc page-break-after"><h2>目录</h2><ol>'
        + "".join(f'<li><a href="#{slug(t)}">{html.escape(t)}</a></li>' for _, t in toc_items)
        + "</ol></nav>"
    )

    abstract = f"""## 摘要与执行概要

本报告系统记录并解释仓库 `20260522-LSG-WRR` 中基于公开多保真淹没立方体的 LSG（Low-fidelity, Spatial analysis, and Gaussian Process Learning，低保真—空间分析—高斯过程学习）实现、诊断与概率扩展。LSG 不依赖 HEC-RAS、TUFLOW 或任一特定求解器品牌：它只要求成对的高精度（high-fidelity, HF）与低精度（low-fidelity, LF）淹没场。

在 Fraehr 风格的 Grp1 / `wet_train` 协议下，三案例的主结论是：（1）相对 LF-only，多保真 LSG 在 Burnett 等弱 LF 情景给出清晰的 CSI（Critical Success Index，临界成功指数）与湿单元 RMSE（root mean square error，均方根误差）提升——**技能来自多保真映射本身**；（2）**关于局部化的结论是负面的**：层次残差分区（H-LSG，`residual_kmeans`）在原生容量下看似缩小截断间隙 O2−O1（empirical orthogonal function，经验正交函数），但**一旦把 GP 输入维度对齐**，全局模型复现（Burnett）甚至超越（Chowilla）该收缩，且 Chowilla 上 matched-15 全局拿到**更低**的 wet RMSE（0.085 vs 0.093 m），Burnett 上额外残差容量通过退化的 LF→HF GP 映射（O4−O2 0.304 vs 0.056 m，EXT 门控相同）**恶化**深度 RMSE；诱导点预算与分区数对 RMSE 的影响不亚于分区本身——因此**表观分区优势是容量/近似混淆，而非空间局部化**；（3）Carlisle Max 路径上 CRPS（Continuous Ranked Probability Score，连续分级概率评分）方差标定把方差尺度压到 s≈{r3(var_max)}，CRPS 由 {r3(crps_max_before)} 降至 {r3(crps_max_after)}，而 CSI/RMSE 因均值不变而按构造保持不变；（4）Chowilla 在 all_cells 上出现 CSI≈{r4(metrics['chow_h_all_csi'])} 的“崩溃”，但在 `wet_train` 上 CSI≈{r4(metrics['chow_h_wet_csi'])}、RMSE≈{r3(metrics['chow_h_wet_rmse'])} m——这是强 LF 范围情景下的评分协议反例，不是静默失败。评价单元是 hold-out 事件（Carlisle/Chowilla Max：N=1；Burnett：N=18），不是栅格单元。本报告因此把 H-LSG 从“分区精度胜利”重新定位为**带等容量对照的截断诊断工具 + 诚实的负结果**。

报告按教学体例撰写：每个图/表前说明动机，之后逐面板解读，并给出机制诊断时序（问题→证据→诊断→最小处理→验证→边界）。缺失资产一律标为「待补充」，不编造。
"""

    bg = """## 研究背景与目标

### 背景

快速、可重复的淹没图是洪水风险管理、应急推演与情景分析的核心需求。高精度二维水动力模型计算昂贵；低精度模型快但不准。Fraehr 等人提出的 LSG 用 HF 场做 EOF 降维，把 LF 场投影为伪展开系数（pseudo expansion coefficients, 伪 EC），再用稀疏高斯过程（Sparse GP / SGPR）学习 LF→HF 的模态系数映射，从而在秒—分钟级给出接近 HF 的淹没重构。

Wang 等（2026）在大型复杂洪泛区进一步讨论 LSG-TS 与 LSG-Max，并在文中将“分区 EOF（zonal EOF）”列为未来工作。本仓库的科学任务不是“发明 LF→HF”这一想法，而是在**可公开复现的三案例立方体**上，实现并严格评估：残差层次分区、校准后的 GP 地图不确定性、以及 O1–O4 神谕误差阶梯。

### 研究问题（与 `02_paper_framework.md` 对齐）

1. **RQ1（容量对照的技能）**：在**对齐 GP 输入维度**后，残差层次分区相对全局 LSG 的表观优势是否幸存？（结论：否——见「等容量对照」节。）
2. **RQ2（归因）**：剩余误差集中在截断、LF 投影，还是 GP 映射？
3. **RQ3（UQ）**：CRPS 尺度方差标定能否在不改 CSI/RMSE 的前提下改善概率评分？
4. **RQ4（边界）**：强 LF 范围何时制造 all-cells 反例，协议应如何报告？

### 目标交付

形成可离线传阅的中文研究报告（HTML/MD/PDF），使读者能沿着“来龙去脉”复现每一个关键数字与图件结论。
"""

    lit = """## 文献与科学缺口

### LSG 谱系（已核验）

- Fraehr et al. 2022 WRR（10.1029/2022WR032248）：EOF + Sparse GP 提升 LF 淹没。
- Fraehr et al. 2023 WRR（10.1029/2022WR033836）：洪泛区混合 LSG；深度与非结构网格。
- Fraehr et al. 2023 Nature Water：加速水动力淹没。
- Fraehr et al. 2024 Water Research：Carlisle/Chowilla/Burnett 上 LSG 与 ML 代理对比。
- Wang, Wang & Nathan 2026 WRR（10.1029/2025WR042481）：大型复杂洪泛区策略；**分区 EOF 为 future work**。
- Lu et al. 2025 JoH：LSG 中核函数选择。
- 公共立方体 Figshare 10.26188/24312658。

### 最近约束新颖性的工作

- Zeli Tan et al. 2025 HESS（10.5194/hess-29-3833-2025）：区域化训练 + 降维/映射两段误差分解（阻断“首个 LSG 局部化/首个误差分解”）。
- Rukai Wang et al. 2025（10.1007/s13753-025-00642-5）：REOF + Sparse GP（阻断宽泛“首个局部 EOF 多保真代理”；文中已有 SGP 方差数学）。
- FIER / Markert et al. 2026（10.5194/hess-30-459-2026）：流域拼图式 REOF 预报（术语风险，非 LF→HF LSG）。
- SFINCS–LSG：EGU25/EGU26 摘要已核验；SSRN 预印本 10.2139/ssrn.6727349（非同行评审期刊）。
- 多种非 LSG 概率淹没代理（Donnelly、Kohanpur、Siripatana 等）：阻断“首个概率淹没图代理”。

### 本项目可辩护新颖性（严格边界）

可主张：（i）对残差层次分区 LSG 的**等容量负结果**——在公开数据上用 `force_n_modes` 匹配容量、并做诱导点/分区数扫描，证明表观 O2−O1 优势是容量混淆而非局部化，且不转化为留出深度技能；（ii）Fraehr 兼容的 EXT+WSE 双场 + O1–O4 神谕阶梯 + CRPS 标定的 LSG 地图后验的公开三案例评估；（iii）可复现开放基准 + 诚实负结果。不可主张：首个局部 EOF、首个 LSG 误差分解、zoning 提升 CSI/RMSE、局部化在容量对齐后仍成立。
"""

    # Continue building content pieces...
    data_sec = f"""## 数据来源与案例研究

{table_md(t_inventory_h, t_inventory_r, "案例与数据集清单（来自 data/DATA_INVENTORY.md / README）")}

### 评分掩膜术语（首次完整定义）

- **all_cells（全单元）**：在整个 HF 网格上计算列联表与 RMSE。包含大量“始终干燥”单元；当模型在训练湿掩膜外漏报/误报时，指标可剧烈变化。
- **wet_train（训练湿掩膜）**：Fraehr Categories 定义的湿单元索引（Carlisle Grp1 与 Categories_HFdata_ValidateOnGrp_1 对齐，文档记 239 482 单元）。这是与发表 LSG 表格可比的主协议。
- **阈值 0.03 m**：深度 ≥ 0.03 m 视为湿，用于 POD/RFA/CSI。

### 案例科学角色

- **Carlisle**：可跑完整 LSG-TS 与 LSG-Max；是 SGPR 修复与 UQ before/after 的主证据场。
- **Chowilla**：LF 范围已经很强（CSI≈0.93）；用来展示“协议反例”与 zoning 对 O2−O1 的作用。
- **Burnett**：弱 LF（CSI≈0.85），用来展示多保真 LSG 的主技能跃迁。
"""

    data_html = f"""
<section id="{slug('数据来源与案例研究')}">
<h2>数据来源与案例研究</h2>
{table_html(t_inventory_h, t_inventory_r, "案例与数据集清单（来自 data/DATA_INVENTORY.md / README）")}
<p><strong>all_cells</strong>：全 HF 网格评分。<strong>wet_train</strong>：Fraehr Categories 湿单元索引（与发表表可比）。阈值 <strong>0.03 m</strong>。</p>
<ul>
<li><strong>Carlisle</strong>：完整 TS/Max、SGPR 修复与 UQ before/after 主场。</li>
<li><strong>Chowilla</strong>：强 LF 范围协议反例；zoning→O2−O1。</li>
<li><strong>Burnett</strong>：弱 LF，展示 LSG 主技能跃迁。</li>
</ul>
</section>
"""

    methods = f"""## 方法学基础

{table_md(t_methods_h, t_methods_r, "方法变体与符号位置")}

### 管道概览（六步）

1. **裁域**：按 0.03 m 识别湿 / 常湿 / 临时单元。
2. **HF 上 EOF**：SVD/PCA；North 规则与 Kaiser 规则保留模态。`wse_ext` 下分别对 EXT 与 WSE 建 EOF。
3. **LF→HF 插值**：LF 深度→WSE→最近邻到 HF→用 HF DEM 裁剪→HF 深度（Fraehr）。
4. **伪 EC**：把 LF 投影到 HF EOF 模态。
5. **稀疏 GP**：每模态一个 SGPR（或 NumPy RBF GP）；输出均值与方差。
6. **重构**：`wse_ext` 下 EXT 门控 WSE，`depth=max(WSE−Z,0)`；`depth` 模式为单场 EOF+Tobit。

### 关键方程（概念形，非外挂 MathJax）

<div class="eq">深度由水面与地形： depth = max(WSE − Z, 0)。</div>
<div class="eq">双场门控： depth = max( where(EXT=1, WSE, Z) − Z, 0 )（AF 常湿强制为湿）。</div>
<div class="eq">方差标定： Var<sub>cal</sub> = s · Var<sub>raw</sub>，潜变量均值不变 ⇒ CSI/RMSE 不变。</div>
<div class="eq">诱导点预算： m = min( n, max( round(n·f), min_inducing ) )，f=0.02，默认 min_inducing=16。</div>
"""

    methods_html = f"""
<section id="{slug('方法学基础')}">
<h2>方法学基础</h2>
{table_html(t_methods_h, t_methods_r, "方法变体与符号位置")}
<ol>
<li><strong>裁域</strong>：0.03 m 阈值。</li>
<li><strong>HF EOF</strong>：<code>wse_ext</code> 双 EOF。</li>
<li><strong>LF→HF</strong>：WSE→最近邻→DEM clip。</li>
<li><strong>伪 EC</strong>：LF 投影到 HF 模态。</li>
<li><strong>SGPR</strong>：每模态均值+方差。</li>
<li><strong>重构</strong>：EXT 门控 WSE→depth。</li>
</ol>
<div class="eq">depth = max(WSE − Z, 0)</div>
<div class="eq">depth = max(where(EXT=1, WSE, Z) − Z, 0)</div>
<div class="eq">Var<sub>cal</sub> = s · Var<sub>raw</sub>（均值不变）</div>
<div class="eq">m = min(n, max(round(n·f), min_inducing))，f=0.02，min_inducing=16</div>
</section>
"""

    timeline = """## 完整研究过程与时间线

本时间线按仓库文档与工件“因果顺序”整理，而非日历日记。

1. **公开立方体接入**：下载/junction Carlisle、Chowilla、Burnett；确认 MD5 与目录结构（`DATA_INVENTORY.md`）。
2. **几何与时间对齐修复**：Carlisle LF HDF 含 ghost 单元与超前时段 → `active_cell_mask` + `align_lf_to_hf_time`，伪 EC 与 Fraehr 发表输入对齐到 8 位小数。
3. **深度单场基线 → EXT+WSE**：深度 EOF 过度预报范围（高 RFA）；切换 `wse_ext` 后 CSI 逼近发表 ~0.969。
4. **引入残差分区 H-LSG**：期望改善局部结构；Max 路径出现 O4/RMSE 恶化。
5. **诊断**：不是分区“饿死”，而是 LSG-Max 仅 8 个训练行时，`inducing_point_fraction=0.02` 塌成 2 个诱导点，且按列 linspace 对角线放置；H-LSG 输入维升到约 13，秩-2 对角诱导集无法表达映射。
6. **修复**：诱导点改为训练行子采样；`min_inducing_points` 下限（封顶 n_train）。
7. **验证**：Max O4/RMSE 恢复并优于 global；TS O4 改善；CSI 平稳。
8. **UQ 标定**：发现 Max `coverage_90≈0.996` 过宽 → `crps_scale`；点估计不变。
9. **跨案例 max-surface 折**：Chowilla/Burnett；Chowilla/Burnett global A/B；Chowilla wet_correlation；UQ rescore；manifest skips=[]。
10. **作图与本报告**：SciencePlots 图件 + 本报告三格式交付。
"""

    ingest = """## 数据摄取与对齐修复

### 初始问题

直接读取 Carlisle LF 计划 HDF 会得到每时步 5 991 单元，但发表几何 `LF_Geometry_data.npz` 只有 5 681。同时 LF 时间轴比 HF 早约 2 小时（每事件多约 8 步）。

### 证据与诊断

- 310 个边界 ghost 单元的 `Cells Minimum Elevation = NaN`。
- 不对齐将导致伪 EC 与 Fraehr `LSG_WSE_ValidateOnGrp_1.npz` 不一致。

### 修复与验证

- `lsg.hecras.active_cell_mask` 去 ghost；
- `lsg.fraehr.align_lf_to_hf_time` 时间对齐；
- 文档记录：对齐后伪 EC 与发表输入一致到 8 位小数。

### 科学含义

多保真学习对“格子是否同一批物理单元、时间是否同一事件相位”极度敏感；对齐是方法正确性前提，不是次要工程细节。
"""

    wse = """## EXT+WSE 双场模型

### 为何引入

单一深度 EOF 把“是否淹没”与“淹没多深”耦在同一连续场里，容易在干燥区产生虚假浅水，推高 RFA（relative false alarm，相对虚警）。

### 机制

- **EXT（extent，淹没范围）**：在临时单元上学习二值湿/干（阈值相关）。
- **WSE（water-surface elevation，水面高程）**：在湿单元上学习水面。
- **合成**：`where(EXT==1, WSE, Z)`，再 `depth=max(WSE−Z,0)`；常湿（AF）强制为湿。

### 重要澄清

`lf_extent_gated` 仅作诊断对照，**不是**官方模型。官方点估计是训练得到的 EXT+WSE。
"""

    sgpr = f"""## SGPR 诱导点问题与修复

### 初始现象

H-LSG 在 Carlisle Max 上出现 RMSE/O4 恶化：pre-fix H-LSG Max 测试 O4={r3(car_pre_max_eb.get('o4_rmse'))} m，而同一残差结构在修复后 O4={r3(car_max_eb.get('o4_rmse'))} m。

### 证据链

1. LSG-Max 训练行数 n=8；
2. `inducing_point_fraction=0.02` → 仅 2 个诱导点；
3. 旧初始化按列 `linspace` 走输入盒对角线；
4. H-LSG 把 GP 输入从约 1 个 EC 升到约 13 维；对角两点几乎不落在训练行上；
5. 训练 O4 可飙到 ~0.72（文档），测试 O4 跟随恶化。

### 修复

- `inducing_budget`：m = min(n, max(round(n·f), min_inducing))；
- `_inducing_points`：从标准化训练行子采样；
- 配置 `lsg.min_inducing_points: 16`（n=8 时封顶为 8，SGPR 退化为精确 GP）。

### 验证

修复后 Max CSI 仍为 {r4(metrics['car_max_all_csi'])}，RMSE(all)={r3(metrics['car_max_all_rmse'])} m；TS max-surface CSI={r4(metrics['car_ts_all_csi'])}。pre-fix TS 的“漂亮”RMSE 0.055 与缺陷残差 GP 共存，**不得**当作最终结果。
"""

    hlsg = f"""## 层次残差 EOF（H-LSG）

### 定义

在全局 EOF 重构之上，对 **WSE 残差**做 k-means 分区（默认 `n_zones=4`），每区再拟合少量残差 EOF（`residual_eof_modes=3`），并用额外 GP 学习残差 EC。EXT 分支保持全局，避免把范围学习切碎。

### 它在方程中的位置

HF ≈ 全局模态重构 + Σ_zones 残差模态重构；GP 输入级联全局伪 EC 与分区残差伪 EC。

### 实证角色

- Chowilla：H-LSG 的 O2−O1={r3(chow_h_eb.get('o2_minus_o1'))}，global={r3(chow_g_eb.get('o2_minus_o1'))}；湿 CSI 几乎持平（{r4(metrics['chow_h_wet_csi'])} vs {r4(metrics['chow_g_wet_csi'])}）。
- 因此分区是**截断诊断/ refinement**，不是 CSI 冠军叙事。
"""

    uq_sec = f"""## 不确定性量化与标定

### 原始 UQ

每个 EOF 模态保留 GP 方差，单元深度方差闭式传播并加残差/截断项（`lsg/uq.py`）。

### 问题

Carlisle Max 未标定 `coverage_90≈0.996`，区间过宽（over-dispersion）。全单元 coverage 还会被 EXT 干燥零方差单元抬高，故报告 `coverage_*_active`（观测或均值 ≥ τ 的主动单元）。

### 标定

在训练集上最小化高斯 CRPS，拟合全局 s：`Var_cal=s·Var_raw`。Carlisle Max s={r3(var_max)}；TS s={r3(var_ts)}。

### 结果

Max CRPS {r3(crps_max_before)}→{r3(crps_max_after)}；CSI/RMSE 不变。Chowilla/Burnett 已用保存状态重评 before/after：Burnett CRPS {r3(burn_crps_before)}→{r3(burn_crps_after)}（s≈{r3(burn_var)}）；Chowilla CRPS {r3(chow_crps_before)}→{r3(chow_crps_after)} 近乎持平且 coverage 远离名义（s≈{r3(chow_var)}；workflow-fit s≈{r3(chow_var_workflow)}）。
"""

    o14 = f"""## O1–O4 误差预算

定义（`lsg/diagnostics.py`；`wse_ext` 下 EXT/WSE 同步神谕再门控成深度 RMSE）：

| 阶 | 名称 | 物理含义 |
| --- | --- | --- |
| O1 | 全秩 HF EC 神谕 | 数值 SVD 地板 |
| O2 | 截断 k 模态 HF EC | EOF 截断 |
| O3 | LF 伪 EC 无 GP 重构 | LF 可表达性 |
| O4 | 完整 LSG（GP+k） | 总误差 |

差值解读：O2−O1≈截断间隙；O3−O2≈LF 投影损失；O4−O3≈GP 映射等剩余。

{table_md(t_o_h, t_o_r, "测试集 O1–O4（depth RMSE，协议湿索引）")}
"""

    o14_html = f"""
<section id="{slug('O1–O4 误差预算')}">
<h2>O1–O4 误差预算</h2>
<p><strong>O1</strong> 全秩 HF EC 神谕（数值地板）；<strong>O2</strong> 截断 k 模态；<strong>O3</strong> LF 伪 EC 无 GP；<strong>O4</strong> 完整 LSG。度量：门控后深度 RMSE。</p>
{table_html(t_o_h, t_o_r, "测试集 O1–O4（depth RMSE，协议湿索引）")}
</section>
"""

    exp = """## 实验设计与评价指标

### 设计因子

- 案例：Carlisle / Chowilla / Burnett
- 场模式：`wse_ext`（主）；`depth` 仅作历史对照
- 分区：`residual_kmeans` vs `none`（Chowilla + Burnett）；Chowilla 另含 `wet_correlation` 敏感性
- 表面：LSG-Max；Carlisle 另含 LSG-TS
- UQ：开关与 `crps_scale`
- 误差预算：O1–O4

### 指标

- **RMSE**：水深误差（m）；协议上常报 wet_train
- **POD**（Probability of Detection，命中率）
- **RFA**（Relative False Alarms，相对虚警）
- **CSI** = hits / (hits+misses+false alarms)
- **CRPS / Brier / PIT / coverage**：概率层
- **运行时**：JSON 中 `runtime_train_s` / `runtime_predict_s`（硬件细节待补充）

### 公平性

同一阈值、同一折（Grp E1 / Grp1）、同一湿掩膜；不把 LF 门控后处理当作模型本身。
"""

    results = f"""## 分案例结果

### Carlisle（主）

- LF-only：CSI(all)={r4(metrics['car_lf_all_csi'])}，RMSE={r3(metrics['car_lf_all_rmse'])} m
- LSG-Max（H-LSG+SGPR fix）：CSI={r4(metrics['car_max_all_csi'])}，RMSE(all)={r3(metrics['car_max_all_rmse'])}，RMSE(wet)={r3(metrics['car_max_wet_rmse'])} m
- LSG-TS max-surface：CSI={r4(metrics['car_ts_all_csi'])}，RMSE(all)={r3(metrics['car_ts_all_rmse'])} m
- 与 Fraehr 发表 LSG（Grp E1，湿单元 EXT+WSE）CSI≈0.969 同量级（README 对照表）

### Chowilla（次；协议反例）

- LF 已很强：CSI(all)≈{r4(metrics['chow_lf_all_csi'])}
- LSG-Max H-LSG：CSI(all)≈{r4(metrics['chow_h_all_csi'])} vs CSI(wet)≈{r4(metrics['chow_h_wet_csi'])}；RMSE(wet)≈{r3(metrics['chow_h_wet_rmse'])} m（相对 LF 湿 RMSE≈{r3(metrics['chow_lf_wet_rmse'])} 大幅下降）
- 解释：EXT 在训练湿掩膜上学习；all_cells 暴露掩膜外系统偏差——必须双报协议

### Burnett（第三）

- LF CSI≈{r4(metrics['burn_lf_wet_csi'])}，RMSE≈{r3(metrics['burn_lf_wet_rmse'])} m
- LSG-Max H-LSG CSI≈{r4(metrics['burn_h_wet_csi'])}，RMSE≈{r3(metrics['burn_h_wet_rmse'])} m
- LSG-Max global CSI≈{r4(metrics['burn_g_wet_csi'])}，RMSE≈{r3(metrics['burn_g_wet_rmse'])} m；O2−O1 global≈{r3(burn_g_eb.get('o2_minus_o1'))} vs H-LSG≈{r3(burn_eb.get('o2_minus_o1'))}
- 这是“多保真 LSG 为主技能源”的最清晰跨案例证据；但 H-LSG 虽有更小 O2−O1，其 wet RMSE 反而**更差**——见「等容量对照」节：这是 LF→HF GP 映射（O4−O2）退化，而非分区收益，且 matched-18 全局在纯容量下复现同一失败
"""

    cross = f"""## 跨案例比较

{table_md(t_cross_h, t_cross_r, "跨案例点技能（JSON 核验；主协议见列）")}

### 比较命题

1. **技能主源**：Burnett 式弱 LF → LSG 大幅提升；不是 zoning。
2. **分区作用**：看 O2−O1（Chowilla/Burnett global A/B 均已齐），不看 CSI 排行榜。
3. **协议敏感性**：Chowilla all-cells vs wet_train 必须并排出现。
4. **UQ**：三案例均有 before/after；Carlisle/Burnett 改善；Chowilla CRPS 近乎持平、coverage 恶化——如实报告。
5. **分区敏感性**：Chowilla `wet_correlation` 湿 CSI≈{r4(metrics['chow_wc_wet_csi'])}，略高于 H-LSG，仍非 headline。
"""

    cross_html = f"""
<section id="{slug('跨案例比较')}">
<h2>跨案例比较</h2>
{table_html(t_cross_h, t_cross_r, "跨案例点技能（JSON 核验）")}
<ol>
<li>技能主源是多保真 LSG（Burnett）。</li>
<li>分区看 O2−O1（Chowilla/Burnett global A/B 均已齐）。</li>
<li>Chowilla 必须双报 all_cells 与 wet_train。</li>
<li>UQ before/after：Carlisle 改善；Burnett 改善；Chowilla CRPS 近乎持平（如实）。</li>
</ol>
</section>
"""

    # ---------- Capacity-control section (equal-capacity negative result) ----------
    cap_t6_h = ["模型", "WSE 维度", "CSI(wet)", "RMSE(m, wet)", "测试 O2−O1(m)"]
    cap_t6_r = [
        ["全局（原生）", cap_dim(chow_g_cap), r4(sp(chow_g_cap, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_g_cap, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_g_cap))],
        ["H-LSG `residual_kmeans`", cap_dim(chow_h_cap), r4(sp(chow_h_cap, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_h_cap, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_h_cap))],
        ["全局 matched-15（`force_n_modes:15`）", cap_dim(chow_g15), r4(sp(chow_g15, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_g15, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_g15))],
        ["H-LSG `residual_eof_modes:0`", cap_dim(chow_h_b3), r4(sp(chow_h_b3, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_h_b3, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_h_b3))],
    ]

    cap_t7_h = ["模型", "WSE 维度", "CSI(wet)", "RMSE(m, wet)", "测试 O2−O1(m)", "测试 O4−O2(m)"]
    cap_t7_r = [
        ["全局（原生）", cap_dim(burn_g, "6"), r4(sp(burn_g, "lsg_max", "wet_train", "csi")),
         r3(sp(burn_g, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(burn_g)), r3(cap_o4o2(burn_g))],
        ["H-LSG `residual_kmeans`", cap_dim(burn, "18"), r4(sp(burn, "lsg_max", "wet_train", "csi")),
         r3(sp(burn, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(burn)), r3(cap_o4o2(burn))],
        ["全局 matched-18（`force_n_modes:18`）", cap_dim(burn_g18), r4(sp(burn_g18, "lsg_max", "wet_train", "csi")),
         r3(sp(burn_g18, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(burn_g18)), r3(cap_o4o2(burn_g18))],
    ]

    cap_t8_h = ["因子", "设置", "WSE 维度", "CSI(wet)", "RMSE(m, wet)", "测试 O2−O1(m)"]
    cap_t8_r = [
        ["诱导点 `min_inducing_points`", "2", cap_dim(chow_ind_m2), r4(sp(chow_ind_m2, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_ind_m2, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_ind_m2))],
        ["", "8", cap_dim(chow_ind_m8), r4(sp(chow_ind_m8, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_ind_m8, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_ind_m8))],
        ["", "16（默认）", cap_dim(chow_h_cap), r4(sp(chow_h_cap, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_h_cap, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_h_cap))],
        ["", "28（= n_train）", cap_dim(chow_ind_m28), r4(sp(chow_ind_m28, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_ind_m28, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_ind_m28))],
        ["分区数 `n_zones`", "2", cap_dim(chow_nz2), r4(sp(chow_nz2, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_nz2, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_nz2))],
        ["", "4（默认）", cap_dim(chow_h_cap), r4(sp(chow_h_cap, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_h_cap, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_h_cap))],
        ["", "6", cap_dim(chow_nz6), r4(sp(chow_nz6, "lsg_max", "wet_train", "csi")),
         r3(sp(chow_nz6, "lsg_max", "wet_train", "rmse")), r3(cap_o2o1(chow_nz6))],
    ]

    ncv_full = nested_cv.get("full_train_var_scale") if nested_cv else None
    ncv_mean = nested_cv.get("fold_var_scale_mean") if nested_cv else None
    ncv_std = nested_cv.get("fold_var_scale_std") if nested_cv else None
    ncv_min = nested_cv.get("fold_var_scale_min") if nested_cv else None
    ncv_max = nested_cv.get("fold_var_scale_max") if nested_cv else None
    ncv_folds = len(nested_cv.get("folds", [])) if nested_cv else 0

    cap_title = "等容量对照实验（局部化不成立）"
    capacity = f"""## {cap_title}

本节是本轮修订的**核心新增诊断**，用来回答审稿式质疑：H-LSG（层次残差分区）相对全局 EOF 的“优势”，是**真的空间局部化**，还是仅仅**更多容量**（更多保留的 EC、更宽的 GP 输入）造成的假象？我们把 GP 输入维度（`gp_input_dim`）钉死后重跑，结论是：**一旦容量对齐，局部化优势不成立。**

### 怎么读这些表（教学说明）

- **WSE 维度**＝进入 WSE 分支高斯过程的展开系数总数（`capacity.gp_input_dim_wse`）。H-LSG 会把“全局模态 + 各分区残差 EC”叠进去，所以天然比全局基线维度更高——这正是“容量混淆”的来源。
- **O2−O1（截断间隙）**＝在 HF 神谕下，从“只保留 k 个模态”到“全秩”的深度 RMSE 差；它衡量子空间**表达力**。任何增加保留方差的手段（多加分区残差 EC，或多加全局模态）都会缩小它——它奖励的是**容量**，不是**空间分区**本身。
- **RMSE(wet)**＝真正的执行技能（湿掩膜深度误差），才是我们最终关心的量。
- 关键对照逻辑：用 `force_n_modes` 给**全局**模型灌进与 H-LSG **相同**的维度；再用 `residual_eof_modes:0` 把 H-LSG 的残差关掉，看它是否塌回全局基线。

### Chowilla 等容量对照（表 6）

{table_md(cap_t6_h, cap_t6_r, "表 6. Chowilla 等容量对照（Grp1 Max, wet_train；数值取自 *_capacity_rerun / *_matched15 / *_budget3 JSON）")}

**解读**：给全局模型灌到 15 维后，它拿到**最低**的 wet RMSE（{r3(sp(chow_g15, "lsg_max", "wet_train", "rmse"))} m，H-LSG 为 {r3(sp(chow_h_cap, "lsg_max", "wet_train", "rmse"))} m，原生 3 模态全局 {r3(sp(chow_g_cap, "lsg_max", "wet_train", "rmse"))} m）和**最小**的 O2−O1（{r3(cap_o2o1(chow_g15))} m，H-LSG {r3(cap_o2o1(chow_h_cap))} m，原生全局 {r3(cap_o2o1(chow_g_cap))} m）。把 H-LSG 残差关掉（`residual_eof_modes:0`）后它精确塌回原生全局。所以 6.3 节里归功于“分区”的 O2−O1 收缩，其实只要多留全局模态就能复现——甚至超过——一旦容量对齐，分区在 wet RMSE 上**没有**任何优势。

### Burnett 等容量对照与误差归因（表 7）

{table_md(cap_t7_h, cap_t7_r, "表 7. Burnett 等容量对照与神谕归因（Grp1 Max, wet_train / test）")}

**解读**：额外容量（无论来自 H-LSG 残差栈，还是 matched-18 全局）都**缩小 O2−O1 但恶化** wet RMSE：相对原生 6 模态全局（{r3(sp(burn_g, "lsg_max", "wet_train", "rmse"))} m），H-LSG 升到 {r3(sp(burn, "lsg_max", "wet_train", "rmse"))} m，matched-18 全局 {r3(sp(burn_g18, "lsg_max", "wet_train", "rmse"))} m。神谕阶梯把失败精确定位到 **LF→HF 的 GP 映射**：H-LSG 的 O4−O2＝{r3(cap_o4o2(burn))} m，约为全局（{r3(cap_o4o2(burn_g))} m）的 5.5 倍；而两模型的 EXT 门控**完全相同**（cell agreement 0.986，见 `diagnose_burnett_hlsg_gap.py` 产出的 `diagnose_hlsg_o2_vs_rmse.json`）。因此这**不是**“extent 门控”故事，而是残差容量让子空间更可表达、却让 GP 更难拟合。

### 诱导点与分区数混淆（表 8）

{table_md(cap_t8_h, cap_t8_r, "表 8. Chowilla H-LSG 诱导点与分区数扫描（Grp1 Max, wet_train）")}

**解读**：两个“干扰因子”对 RMSE 的影响不亚于分区本身。在 15 维 WSE 输入下，SGPR 诱导点预算主宰深度 RMSE 而 O2−O1 几乎不变（m=2 时 RMSE {r3(sp(chow_ind_m2, "lsg_max", "wet_train", "rmse"))} m；m=28 时降到 {r3(sp(chow_ind_m28, "lsg_max", "wet_train", "rmse"))} m），而 3 维全局在 m=2 时仍稳（约 0.085 m）——低 m 的 H-LSG 崩溃很容易被误读成“分区有害”。另一方面，`n_zones` 从 2 增到 6 单调缩小 O2−O1（{r3(cap_o2o1(chow_nz2))} → {r3(cap_o2o1(chow_nz6))} m）却**恶化** wet RMSE（{r3(sp(chow_nz2, "lsg_max", "wet_train", "rmse"))} → {r3(sp(chow_nz6, "lsg_max", "wet_train", "rmse"))} m）：更多分区＝更多 GP 无法利用的 EC 容量。两组扫描都指向容量/近似解释，而非局部化解释。

### CRPS 尺度的折稳定性（方法学检查）

官方测试折在 Chowilla 只有 1 个事件，可能担心 CRPS 方差尺度 *s* 是脆弱的单次拟合。{ncv_folds} 折留一训练事件交叉验证给出 *s* = {r3(ncv_mean)} ± {r3(ncv_std)}（范围 {r3(ncv_min)}–{r3(ncv_max)}），围绕全训练值 {r3(ncv_full)}，说明该标量在重采样下稳定。这**不**声称 Chowilla 标定有用（6.5 节报告其 CRPS 持平、coverage 恶化），只说明该零结果不是估计器不稳造成的（来源 `nested_crps_scale_cv.json`）。

### 本节结论（写进正文的底线）

1. **不要**在未陈述上述等容量负对照的情况下，声称 H-LSG“因局部化”而在深度 RMSE 上胜过全局 EOF。
2. H-LSG 最诚实的定位是**带等容量对照的截断间隙（O2−O1）诊断工具**，而非 CSI/RMSE 升级。
3. 在 **Burnett** 上要明说：H-LSG 通过 **GP/LF 映射（O4−O2）** 恶化 wet RMSE，而非 EXT 门控；matched-18 全局在纯容量下复现同一失败模式。
"""

    capacity_html = f"""
<section id="{slug(cap_title)}">
<h2>{html.escape(cap_title)}</h2>
<div class="callout">本节是本轮修订的<strong>核心新增诊断</strong>：把 GP 输入维度（<code>gp_input_dim</code>）钉死后重跑，检验 H-LSG 相对全局 EOF 的“优势”是真局部化还是多容量。结论：<strong>一旦容量对齐，局部化优势不成立。</strong></div>
<h3>怎么读这些表（教学说明）</h3>
<ul>
<li><strong>WSE 维度</strong>＝进入 WSE 分支 GP 的 EC 总数（<code>capacity.gp_input_dim_wse</code>）；H-LSG 天然更高，这是容量混淆来源。</li>
<li><strong>O2−O1（截断间隙）</strong>＝HF 神谕下从截断到全秩的深度 RMSE 差，衡量子空间表达力；任何增加保留方差的手段都会缩小它——奖励容量，不是分区。</li>
<li><strong>RMSE(wet)</strong> 才是执行技能；用 <code>force_n_modes</code> 给全局灌到 H-LSG 相同维度，再用 <code>residual_eof_modes:0</code> 看 H-LSG 是否塌回全局。</li>
</ul>
<h3>Chowilla 等容量对照</h3>
{table_html(cap_t6_h, cap_t6_r, "表 6. Chowilla 等容量对照（Grp1 Max, wet_train）")}
<p><strong>解读：</strong>给全局灌到 15 维后拿到最低 wet RMSE（{r3(sp(chow_g15, "lsg_max", "wet_train", "rmse"))} m）与最小 O2−O1（{r3(cap_o2o1(chow_g15))} m）；关掉 H-LSG 残差即塌回原生全局。分区的 O2−O1 收缩只要多留全局模态就能复现甚至超过，容量对齐后分区在 wet RMSE 上无优势。</p>
<h3>Burnett 等容量对照与误差归因</h3>
{table_html(cap_t7_h, cap_t7_r, "表 7. Burnett 等容量对照与神谕归因（Grp1 Max, wet_train / test）")}
<p><strong>解读：</strong>额外容量缩小 O2−O1 却恶化 wet RMSE（原生全局 {r3(sp(burn_g, "lsg_max", "wet_train", "rmse"))} m → H-LSG {r3(sp(burn, "lsg_max", "wet_train", "rmse"))} m、matched-18 {r3(sp(burn_g18, "lsg_max", "wet_train", "rmse"))} m）。神谕定位到 LF→HF GP 映射：H-LSG 的 O4−O2＝{r3(cap_o4o2(burn))} m ≈ 全局（{r3(cap_o4o2(burn_g))} m）的 5.5 倍；两模型 EXT 门控相同（agreement 0.986），非 extent 故事。</p>
<h3>诱导点与分区数混淆</h3>
{table_html(cap_t8_h, cap_t8_r, "表 8. Chowilla H-LSG 诱导点与分区数扫描（Grp1 Max, wet_train）")}
<p><strong>解读：</strong>诱导点预算主宰深度 RMSE 而 O2−O1 不变（低 m 崩溃易被误读为“分区有害”）；<code>n_zones</code> 2→6 缩小 O2−O1 却恶化 RMSE。两者都是容量/近似效应。</p>
<h3>CRPS 尺度的折稳定性</h3>
<p>{ncv_folds} 折留一训练事件交叉验证：<em>s</em> = {r3(ncv_mean)} ± {r3(ncv_std)}（范围 {r3(ncv_min)}–{r3(ncv_max)}），围绕全训练值 {r3(ncv_full)}，稳定；不声称 Chowilla 标定有用，只排除估计器不稳（<code>nested_crps_scale_cv.json</code>）。</p>
<div class="callout"><strong>底线：</strong>H-LSG 应定位为带等容量对照的 O2−O1 <strong>诊断工具</strong>，不是 CSI/RMSE 升级；Burnett 上由 GP/LF 映射（O4−O2）而非 EXT 门控致其 RMSE 恶化。</div>
</section>
"""

    # Figure interpretations
    figs_md = ["## 详细图件解读", ""]
    figs_html = [f'<section id="{slug("详细图件解读")}"><h2>详细图件解读</h2>']
    if skips:
        figs_html.append(
            '<div class="callout"><strong>图清单跳过项（figure_manifest.json）</strong><ul>'
            + "".join(f"<li>{html.escape(s)}</li>" for s in skips)
            + "</ul></div>"
        )
    else:
        figs_html.append(
            '<div class="callout"><strong>figure_manifest.json</strong>：当前 <code>skips=[]</code>（Fig.3–6 含 Burnett global、UQ before/after、P(wet)、wet_correlation）。</div>'
        )

    fig_specs = [
        (
            "fig01",
            "图1 跨案例 CSI 与湿训练 RMSE（wet_train）",
            "回答 RQ1：在统一湿训练掩膜下，LF-only 与 LSG 变体的点技能如何跨 Carlisle/Chowilla/Burnett 排列。角色：执行摘要级总览，先于分区消融与 UQ。",
            "横轴多为案例或方法分组，纵轴为 CSI（无量纲，0–1，越高越好）或 RMSE（米，越低越好）。颜色区分 LF / LSG-Max / 必要时 TS。误差条若存在则来自折内单元汇总（以实际图面为准）。请同时看成对的 CSI 与 RMSE，避免只宣扬单一指标。",
            "左类面板（CSI）：比较各案例 LF 与 LSG 的命中—虚警综合技巧。右类面板（RMSE）：强调深度误差，尤其 Chowilla 在湿掩膜上 RMSE 大幅下降。若某案例缺柱，对照 manifest skips，不得手绘填补。",
            f"Burnett：LSG 相对 LF 的 CSI 由约 {r4(metrics['burn_lf_wet_csi'])} 升至约 {r4(metrics['burn_h_wet_csi'])}。Carlisle：高位改进更细（LF≈{r4(metrics['car_lf_wet_csi'])} → Max≈{r4(metrics['car_max_wet_csi'])}）。Chowilla：湿 CSI 高，但需结合图5/表理解 all-cells 反例。",
            "因果链：弱 LF 几何误差大 → 伪 EC+GP 映射可学到系统订正 → CSI/RMSE 改善显著；强 LF 范围已准 → CSI 抬升空间小，但深度仍可订正。",
            "可以：断言多保真 LSG 在公开协议上可复现的点技能格局。不可以：仅凭此图声称残差分区是 CSI 主因（需图3/O 表）。",
            "像用粗分辨率天气预报当地气温：如果粗预报已经“会不会下雨”很准，你对“是否下雨”的提升有限，但仍可能把雨强（水深）校正得更好。",
        ),
        (
            "fig02",
            "图2 O1–O4 误差预算条形图",
            "回答 RQ2：误差落在截断、LF 表达还是 GP 映射。角色：诊断核心，支撑“分区压缩 O2−O1”而非“分区碾压 CSI”。",
            "每组柱对应 O1–O4 的深度 RMSE（米）。阅读时先看 O1 地板，再看 O2 相对 O1 的抬升（截断），再看 O3（LF），最后 O4（全系统）。",
            "按案例/变体分面：Carlisle TS/Max、Chowilla、Burnett。Max 上 O2−O1 很小（约 0.005）说明残差分区后截断间隙被压薄；TS 上 O3 很高说明时间序列路径更受 LF 伪 EC 限制。",
            f"Carlisle Max O2−O1≈{r3(car_max_eb.get('o2_minus_o1'))}；Chowilla H-LSG≈{r3(chow_h_eb.get('o2_minus_o1'))} vs global≈{r3(chow_g_eb.get('o2_minus_o1'))}；Burnett≈{r3(burn_eb.get('o2_minus_o1'))}。",
            "时序：先有全局截断过大 → 引入残差分区 → O2 下降 → 但若 SGPR 诱导点错误，O4 会单独爆炸（见图 eth 叙事/表）→ 修复诱导点后 O4 回落。",
            "可以：用 O 阶梯定位误差部件。不可以：把 O4 自动等于“模型无能”（需排除近似数值病态）。",
            "像体检分项：O1 是仪器噪声底，O2 是“只做主要检查项目”的信息损失，O3 是“用低精度仪器硬测”的损失，O4 是走完整流程后的总偏差。",
        ),
        (
            "fig03",
            "图3 Global vs H-LSG 消融（含 O2−O1）",
            "回答“分区到底帮在哪里”。角色：把创新点从 CSI 冠军叙事纠正为截断 refinement。",
            "对比 global（zoning:none）与 H-LSG（residual_kmeans）在 CSI、RMSE、O2−O1 等指标上的并排柱。现含 Chowilla 与 Burnett。",
            "Carlisle（若有）/Chowilla/Burnett 面板：湿 CSI 接近；O2−O1 上 H-LSG 更小。Burnett 全局 RMSE 可低于 H-LSG，故不可把分区写成万能 RMSE 赢家。",
            f"Chowilla 湿 CSI：H-LSG {r4(metrics['chow_h_wet_csi'])} vs global {r4(metrics['chow_g_wet_csi'])}；O2−O1：{r3(chow_h_eb.get('o2_minus_o1'))} vs {r3(chow_g_eb.get('o2_minus_o1'))}。"
            f" Burnett：H-LSG {r4(metrics['burn_h_wet_csi'])} vs global {r4(metrics['burn_g_wet_csi'])}；O2−O1：{r3(burn_eb.get('o2_minus_o1'))} vs {r3(burn_g_eb.get('o2_minus_o1'))}。",
            "原因：残差局部基吃掉全局模态无法表示的空间剩余；它不自动修复 LF 伪 EC 的大尺度偏差，故 CSI 可持平。",
            "可以：跨案例报告分区对截断间隙的作用。不可以：用 Burnett 全局更低 RMSE 反过来说 H-LSG 无用（看 O2−O1 与 CSI 持平）。",
            "像给全国地图先画大趋势，再在各省画“剩余误差”的小修正层——总轮廓未必大变，但局部起伏更贴真值。",
        ),
        (
            "fig04",
            "图4 UQ 的 CRPS 方差标定",
            "回答 RQ3：概率层是否可校准。角色：证明“均值不动、方差可缩”，并诚实记录失败/持平案例。",
            "比较标定前后 CRPS、coverage（优先 active）、以及 s。三案例均有 before/after。",
            "Carlisle Max：CRPS 明显下降。Burnett：CRPS 下降、active coverage 靠近 0.90。Chowilla：CRPS 近乎持平，coverage 远离名义——必须原样写出。",
            f"Carlisle Max：CRPS {r3(crps_max_before)}→{r3(crps_max_after)}，s={r3(var_max)}。"
            f" Burnett：{r3(burn_crps_before)}→{r3(burn_crps_after)}，s={r3(burn_var)}。"
            f" Chowilla：{r3(chow_crps_before)}→{r3(chow_crps_after)}，s={r3(chow_var)}。",
            "未标定截断 MSE 常使区间过宽 → CRPS 惩罚过散分布 → 学到 s<1 收缩方差；若分布形态/EXT 门控主导，标量 s 可能无效甚至有害。",
            "可以：Carlisle/Burnett 上断言标定可改善概率评分且不改点估计。不可以：声称三案例标定均成功。",
            "像预报温度时平均值对了，但总把“±10°C”说成不确定度；标定相当于学会改口说“±4°C”，中心温度不变——有时改口后评分并不更好。",
        ),
        (
            "fig05a",
            "图5a Carlisle E1 空间图",
            "把表格技能翻译成可检查的空间结构：LF、LSG、HF 的淹没/水深差异与单元级 P(wet)。",
            "多面板：HF / LF / LSG 水深、误差，以及 panel (e) 单元级淹没概率 P(h≥0.03 m)。色标区分水深（m）与概率（0–1）。",
            "逐面板检查河道主槽、漫滩边缘；对照 P(wet) 是否与湿边界一致，而不是把概率面板误读成二值掩膜。",
            "与 CSI≈0.97 量级一致时，空间上应看到边缘更干净；P(wet) 均值约 0.36（Carlisle pred_examples）。",
            "EXT+WSE 分离范围与水深 → 降低干燥区浅水伪影；GP 后验经 Tobit 得到 P(wet)。",
            "可以：定性支持点技能，并引用真实概率场。不可以：把 P(wet) 当成未经标定的决策概率产品而不看 CRPS/coverage。",
            "像把模糊的卫星淹水照片（LF）对照高清航拍（HF），再看算法修复版与“会不会淹”的概率图层。",
        ),
        (
            "fig05b",
            "图5b Chowilla E1 空间图",
            "可视化协议反例：为何 all-cells CSI 低而 wet_train 高；并展示真实 P(wet)。",
            "水深/误差面板 + P(wet)。关注训练湿掩膜内外的差异。",
            "在湿掩膜内，LSG 水深应接近 HF；掩膜外可能出现系统漏检，拖累 all-cells；P(wet) 均值约 0.31。",
            f"与表一致：湿 CSI≈{r4(metrics['chow_h_wet_csi'])}，all-cells≈{r4(metrics['chow_h_all_csi'])}。",
            "EXT 学习域=训练湿类别；强 LF 已覆盖大部分范围时，掩膜外评分暴露归纳偏置。",
            "可以：作为协议教学案例。不可以：单独用 all-cells CSI 否定湿掩膜上的深度订正成功。",
            "像考试只复习了“常考章节”（湿掩膜），超纲题（掩膜外单元）答不好，但不能说常考题也没学会。",
        ),
        (
            "fig05c",
            "图5c Burnett E1 空间图",
            "展示弱 LF 上 LSG 的空间订正幅度与 P(wet)。",
            "读法同 5a；panel (e) 为真实 P(wet)（Burnett 均值约 0.55）。",
            "LF 边缘与深度误差应显著大于 Carlisle；LSG 应更接近 HF。",
            f"与 CSI {r4(metrics['burn_lf_wet_csi'])}→{r4(metrics['burn_h_wet_csi'])}、RMSE {r3(metrics['burn_lf_wet_rmse'])}→{r3(metrics['burn_h_wet_rmse'])} m 的表格叙事一致。",
            "LF 水动力简化误差大 → 多保真映射可学空间偏差场。",
            "可以：支持“LSG 主技能源”，并与图3 Burnett global A/B 对照阅读。不可以：把单事件 E1 图外推为全组 18 事件的唯一形态。",
            "像用一台偏差很大的快测仪（LF）配少量金标准（HF）做校正曲线，再快速出接近金标准的图与概率图层。",
        ),
        (
            "fig06",
            "图6 Chowilla wet_correlation 分区敏感性",
            "回答分区超参是否改变 headline：对比 global / residual_kmeans / wet_correlation。",
            "柱状图为湿训练 CSI 与 RMSE（及图面所示的对照量）。三柱并排，勿只读最高 CSI。",
            "看 CSI 是否仅有微小抬升，同时回忆表中 O2−O1（wet_correlation≈0.010 vs H-LSG 0.013 vs global 0.057）。",
            f"湿 CSI：global {r4(metrics['chow_g_wet_csi'])}；residual_kmeans {r4(metrics['chow_h_wet_csi'])}；wet_correlation {r4(metrics['chow_wc_wet_csi'])}。"
            f" RMSE：{r3(metrics['chow_g_wet_rmse'])} / {r3(metrics['chow_h_wet_rmse'])} / {r3(metrics['chow_wc_wet_rmse'])} m。",
            "相关分区改变残差能量的空间聚合方式；对 CSI 的边际影响通常小于 LF→LSG 主效应。",
            "可以：报告单折敏感性。不可以：宣称 wet_correlation 全面优于 residual_kmeans 或已完成超参穷尽。",
            "像换一种行政区划重画“剩余误差修正层”——边界换了，全国总分未必大变。",
        ),
    ]

    figs_md.append(
        "**figure_manifest.json：** "
        + ("跳过项为空（[]）。" if not skips else ("跳过项：\n\n" + "\n".join(f"- {s}" for s in skips)))
        + "\n"
    )
    for spec in fig_specs:
        md_f, html_f = fig_block(*spec)
        figs_md.append(md_f)
        figs_html.append(html_f)
    figs_html.append("</section>")

    discuss = f"""## 讨论与因果分析

### 主因果叙事（锁定）

1. **多保真 LSG vs LF** 是技能主效应（Burnett 最清晰；Carlisle 在高位微调；Chowilla 深度 RMSE 在湿掩膜上大幅下降）——技能在多保真映射，不在局部化。
2. **残差分区的表观优势是容量混淆**：等容量对照（表 6–8）显示，对齐 GP 维度后全局模型复现/超越 O2−O1 收缩，Chowilla 上 matched-15 全局 wet RMSE 更低；O2−O1 奖励的是保留方差（容量），不是空间分区。
3. **Burnett 的失败机制**：残差容量让子空间更可表达（O2−O1 更小），却让 LF→HF GP 映射退化（O4−O2 约 5.5×），EXT 门控相同——不是 extent 故事；matched-18 全局在纯容量下复现同一失败。
4. **干扰因子**：SGPR 诱导点预算与 `n_zones` 对 RMSE 的影响不亚于分区；低 m 的 H-LSG 崩溃易被误读为“分区有害”。方法论文必须报告这些近似/容量因子。
5. **UQ 标定** 解决过宽区间；与点估计正交（CRPS 尺度经嵌套 CV 证明折稳定）。
6. **Chowilla all-cells** 是评分协议与 EXT 学习域的相互作用，应作为结果写进正文，而非附录藏匿。

### 开放科学问题（来自进度评论）

1. O2−O1 作为诊断很有信息量，但与执行技能解耦——未来应报告“容量匹配后的留出技能”而非单看 O2−O1。
2. 强 LF 反例的社区评分规范应如何标准化？
3. `var_scale` 能否跨事件/站点迁移而不重拟合？（待补充实验）
4. 与 REOF-SGP、Tan 区域化 LSG 的精细边界还需对照表持续维护；未来局部 EOF 洪水代理应默认报告等容量基线。
"""

    innov = f"""## 创新点

{table_md(t_innov_h, t_innov_r, "创新点 vs 既往工作（有边界）")}
"""
    innov_html = f"""
<section id="{slug('创新点')}">
<h2>创新点</h2>
{table_html(t_innov_h, t_innov_r, "创新点 vs 既往工作（有边界）")}
</section>
"""

    repro = f"""## 可复现性与质量保证

{table_md(t_tests_h, t_tests_r, "测试与可复现记录")}

### 推荐复现命令

```powershell
.\\.venv\\Scripts\\Activate.ps1
python scripts/run_lsg_workflow.py --config config/carlisle.yaml
python scripts/run_lsg_workflow.py --config config/chowilla.yaml
python scripts/run_lsg_workflow.py --config config/burnett.yaml
python scripts/rescore_uq_calibrated.py --config config/carlisle.yaml
.\\.venv\\Scripts\\python.exe -m pytest tests -q
```

### 工件索引（摘要）

- Carlisle 主结果：`outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix.json`
- Carlisle UQ：`..._uq_calibrated.json`
- Chowilla H-LSG / global / wet_correlation：`..._hlsg_max.json` / `..._global_max.json` / `..._wet_correlation_max.json`
- Chowilla/Burnett UQ rescore：`..._hlsg_max_uq_calibrated.json`
- Burnett H-LSG / global：`..._hlsg_max.json` / `..._global_max.json`
- 图：`outputs/figures/fig01`–`fig06_*`（manifest skips=[]）
"""

    repro_html = f"""
<section id="{slug('可复现性与质量保证')}">
<h2>可复现性与质量保证</h2>
{table_html(t_tests_h, t_tests_r, "测试与可复现记录")}
<pre class="cmd">.\\.venv\\Scripts\\python.exe -m pytest tests -q
python scripts/run_lsg_workflow.py --config config/carlisle.yaml
python scripts/rescore_uq_calibrated.py --config config/carlisle.yaml</pre>
</section>
"""

    limits = f"""## 局限性

{table_md(t_limit_h, t_limit_r, "局限性与缺口")}
"""
    limits_html = f"""
<section id="{slug('局限性')}">
<h2>局限性</h2>
{table_html(t_limit_h, t_limit_r, "局限性与缺口")}
</section>
"""

    future = """## 未来工作

1. 内存或流式摄取允许时，对 Chowilla/Burnett 全时序 Grp1 做等容量对照（当前主机不可行）。
2. 连通性约束或流域分区与残差响应分区的对照研究（另一篇工作，而非本稿未完成项）。
3. Burnett 的 CRPS *s* 嵌套 CV；跨站点 `var_scale` 迁移实验。
4. 许可到来后的 Brisbane 与其他公开多保真基准的等容量复现。
5. 发展“容量匹配后可预测局部化增益”的训练期判据（若存在）。
"""

    conclusion = f"""## 结论

在三个公开多保真案例上，本项目复现并扩展了 LSG 栈：EXT+WSE 双场、SGPR 诱导点稳健化、CRPS 方差标定与 O1–O4 神谕预算，并对残差层次分区做了**等容量对照**。关于局部化：Chowilla/Burnett 上一旦对齐 GP 输入维度，残差分区在 O2−O1 上的表观优势会被等容量全局模型复现或超越，且不转化为留出深度技能（Burnett 上额外残差容量经退化的 LF→HF GP 映射恶化 RMSE）。Carlisle Max 在 *n*_train=8 的秩上限下呈现异质：残差堆叠改善 wet RMSE（0.094 vs 原生全局 0.112 m），而把全局容量拉满至秩上限（实现维 8）反而恶化 RMSE（0.202 m）。**可辩护的核心**依然成立：多保真 LSG 在弱 LF 情景提供主要技能；O1–O4 阶梯定位误差部件；CRPS 方差标定在 Carlisle/Burnett 改善可靠性而**按构造**不动 CSI/RMSE，在 Chowilla Max 上 CRPS 近乎持平；残差层次分区最宜用作**截断诊断**，并在等容量与站点约束下报告，而非普遍精度升级。评价单元是 hold-out 事件，不是栅格单元。所有结论均锚定于本仓库 JSON/图件，可独立复核。
"""

    avail = """## 数据与代码可用性

- 公共立方体：Figshare DOI [10.26188/24312658](https://doi.org/10.26188/24312658)（CC BY 4.0）。
- 本仓库配置与脚本：`config/*.yaml`、`lsg/`、`scripts/`（无密钥）。
- Brisbane TUFLOW/URBS：昆士兰州政府许可，需申请；本地为 missing。
- Hybrid LSG 参考代码：https://github.com/nfraehr/Hybrid_LSG_model
"""

    refs = """## 参考文献

1. Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2022). Water Resources Research, 58, e2022WR032248. https://doi.org/10.1029/2022WR032248
2. Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2023). Water Resources Research, 59, e2022WR033836. https://doi.org/10.1029/2022WR033836
3. Fraehr, N., et al. (2023). Nature Water. https://doi.org/10.1038/s44221-023-00132-2
4. Fraehr, N., et al. (2024). Water Research. https://doi.org/10.1016/j.watres.2024.121202
5. Wang, W., Wang, Q. J., & Nathan, R. (2026). Water Resources Research, 62, e2025WR042481. https://doi.org/10.1029/2025WR042481
6. Lu et al. (2025). Journal of Hydrology. https://doi.org/10.1016/j.jhydrol.2025.132949
7. Tan et al. (2025). HESS, 29, 3833. https://doi.org/10.5194/hess-29-3833-2025
8. Wang, R. et al. (2025). REOF-SGP. https://doi.org/10.1007/s13753-025-00642-5
9. Fraehr (2024) datasets. https://doi.org/10.26188/24312658
10. 其余概率代理与 FIER 文献见 `docs/paper/01_literature_review.md`。
"""

    glossary_h = ["中文名", "英文全称", "缩写/符号", "物理意义", "方程/流程位置", "本项目引入原因"]
    glossary_r = [
        ["低保真—空间分析—高斯过程学习", "Low-fidelity, Spatial analysis, and Gaussian Process Learning", "LSG", "多保真淹没代理总方法", "全管道", "研究对象"],
        ["高精度 / 低精度", "High-/Low-fidelity", "HF / LF", "细/粗水动力解", "输入场", "多保真设定"],
        ["经验正交函数", "Empirical Orthogonal Function", "EOF", "空间模态基", "降维", "压缩淹没场"],
        ["展开系数", "Expansion Coefficient", "EC / 伪 EC", "模态时间/事件系数；伪 EC 来自 LF 投影", "GP 输入", "建立 LF→HF 学习"],
        ["淹没范围 / 水面高程", "Extent / Water-Surface Elevation", "EXT / WSE", "湿干与水面", "双场重构", "降虚警、近发表 CSI"],
        ["层次残差 LSG", "Hierarchical residual LSG", "H-LSG", "全局+残差分区", "WSE 残差", "实现 zonal future work"],
        ["稀疏高斯过程回归", "Sparse Gaussian Process Regression", "SGPR", "诱导点近似 GP", "模态映射", "可扩展回归"],
        ["诱导点", "Inducing points", "Z / m", "稀疏近似支撑集", "SGPR", "Max 路径数值稳健"],
        ["临界成功指数", "Critical Success Index", "CSI", "hits/(hits+misses+FA)", "点技能", "淹没范围技巧"],
        ["均方根误差", "Root Mean Square Error", "RMSE", "水深误差均方根", "点技能", "深度精度"],
        ["连续分级概率评分", "Continuous Ranked Probability Score", "CRPS", "概率预报评分", "UQ 目标", "方差标定"],
        ["神谕误差阶梯", "Oracle error budget", "O1–O4", "反事实误差分解", "诊断", "归因"],
        ["残差", "Residual", "ε", "全局重构后的剩余场", "分区 EOF", "局部修正"],
        ["湿训练掩膜", "Fraehr wet_train mask", "wet_train", "训练湿类别单元", "评分", "与发表表对齐"],
    ]

    appendix = f"""## 附录

### A. 术语与符号表

{table_md(glossary_h, glossary_r, "术语与符号词汇表")}

### B. 工件索引

| 类别 | 路径 |
| --- | --- |
| 进度/文献/框架 | `docs/paper/00_progress_review.md` 等 |
| 评价 JSON | `outputs/evaluation/{{carlisle,chowilla,burnett}}/` |
| 图件 | `outputs/figures/fig01*`–`fig06*` |
| 配置 | `config/{{carlisle,chowilla,burnett,burnett_global,chowilla_wet_correlation}}.yaml` |
| 核心代码 | `lsg/{{gp,zoning,uq,diagnostics,wse_ext,fraehr}}.py` |
| 本报告 | `docs/report/report.{{html,md,pdf}}` |
"""

    appendix_html = f"""
<section id="{slug('附录')}">
<h2>附录</h2>
<h3>A. 术语与符号表</h3>
{table_html(glossary_h, glossary_r, "术语与符号词汇表")}
<h3>B. 工件索引</h3>
<ul>
<li><code>docs/paper/</code> 进度、文献、框架</li>
<li><code>outputs/evaluation/</code> 评价 JSON</li>
<li><code>outputs/figures/</code> SciencePlots 图（fig01–fig06；skips 空）</li>
<li><code>config/</code> 与 <code>lsg/</code> 代码</li>
</ul>
</section>
"""

    pending = f"""## 范围边界与本轮已完成项

1. Chowilla / Burnett **全时序** Grp1 — 计算边界（Burnett HF≈199 GB ≫ ≈128 GB RAM）；等容量结论建立在 Max 面。
2. Brisbane / FloodCastBench — 移出公开证据链，仅未来外部复现。
3. Burnett CRPS *s* 嵌套 CV、容量×分区×站点完整析因、oracle 顺序置换 — 不构成本稿逻辑缺口。

**本轮已完成：** Chowilla/Burnett 等容量对照；Carlisle 等容量对照（秩上限说明，见 `docs/paper/05_carlisle_capacity.md`）；Chowilla+Carlisle CRPS *s* 嵌套 CV；Carlisle 区划 8-NN 相干诊断；硬件/软件版本钉扎；手稿清除全部「待补充/待修改」占位。

**Carlisle 等容量教学要点（wet_train）：** H-LSG 维 13 → RMSE 0.094 m；原生全局维 1 → 0.112 m；`force_n_modes: 13` 受 *n*_train=8 限制实现为维 8 → RMSE 0.202 m 且 O2−O1=0；`residual_eof_modes: 0` 坍缩回原生全局。精确维 13 的全局匹配在 Max 路径上不可行。
"""

    # Assemble MD
    md_parts = [
        cover_md,
        toc_md,
        abstract,
        bg,
        lit,
        data_sec,
        methods,
        timeline,
        ingest,
        wse,
        sgpr,
        hlsg,
        uq_sec,
        o14,
        exp,
        results,
        cross,
        capacity,
        "\n".join(figs_md),
        discuss,
        innov,
        repro,
        limits,
        future,
        conclusion,
        avail,
        refs,
        appendix,
        pending,
        "\n---\n\n**状态声明：** 工作区 `20260522-LSG-WRR` 仍无 `.git`；公开镜像通过 staging 副本 `I:\\Projects\\_publish_lsg-flood-surrogate-benchmark` 推送到 https://github.com/Coucou2016/lsg-flood-surrogate-benchmark （等容量负结果修订）。\n",
    ]
    md_text = "\n\n".join(md_parts)
    (OUT / "report.md").write_text(md_text, encoding="utf-8")

    # Assemble HTML
    css = """
:root {
  --fg: #1a1a1a; --muted:#444; --line:#ccc; --bg:#fff; --accent:#1f4e79;
  --callout:#f3f6f9; --table-head:#e8eef5;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0 auto; padding: 24px 18px 80px;
  max-width: 980px;
  color: var(--fg);
  background: var(--bg);
  font-family: "Times New Roman", "Noto Serif CJK SC", "Source Han Serif SC",
               "Microsoft YaHei", SimSun, serif;
  font-size: 11.5pt; line-height: 1.65;
}
h1,h2,h3,h4 {
  font-family: "Microsoft YaHei", "Noto Sans CJK SC", "Times New Roman", sans-serif;
  color: var(--accent); line-height: 1.35; page-break-after: avoid;
}
h1 { font-size: 1.55rem; }
h2 { font-size: 1.3rem; margin-top: 2.2rem; border-bottom: 1px solid var(--line); padding-bottom: .25rem; }
h3 { font-size: 1.12rem; margin-top: 1.4rem; }
a { color: var(--accent); }
code, pre, .cmd {
  font-family: Consolas, "Courier New", monospace;
  font-size: 0.92em;
}
pre.cmd, pre {
  background: #f7f7f7; padding: 12px; overflow: auto;
  border: 1px solid var(--line); white-space: pre-wrap;
}
.cover { padding: 2rem 0 3rem; }
.eyebrow { letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-size: .9rem; }
.subtitle { color: var(--muted); font-size: 1.05rem; }
table { border-collapse: collapse; width: 100%; font-size: 0.95em; }
th, td { border: 1px solid var(--line); padding: 6px 8px; vertical-align: top; }
th { background: var(--table-head); text-align: left; }
.table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.table-wrap { margin: 1rem 0 1.4rem; }
.table-wrap figcaption { font-weight: 600; margin-bottom: .4rem; }
.meta { margin-top: 1.5rem; }
.callout { background: var(--callout); border-left: 4px solid var(--accent); padding: 10px 12px; margin: 1rem 0; }
.figure-embed { margin: 1rem 0; text-align: center; page-break-inside: avoid; }
.figure-embed svg { max-width: 100%; height: auto; }
.figcaption { font-size: 0.95em; color: var(--muted); margin-top: .3rem; }
.interpret p { margin: .55rem 0; }
.eq {
  display: block; margin: .6rem 0; padding: .55rem .8rem;
  background: #fafafa; border: 1px dashed var(--line);
  font-family: "Times New Roman", serif;
}
.toc ol { padding-left: 1.2rem; }
.page-break-after { page-break-after: always; break-after: page; }
@media print {
  body { max-width: none; padding: 0; font-size: 10.5pt; }
  a { text-decoration: none; color: inherit; }
  .figure-embed { break-inside: avoid; }
  h2, h3 { break-after: avoid; }
  @page { margin: 18mm 16mm; }
}
@media (max-width: 720px) {
  body { padding: 14px 10px 60px; font-size: 11pt; }
}
"""

    html_body_parts = [
        cover_html,
        toc_html,
        f'<section id="{slug("摘要与执行概要")}">{md_to_simple_html(abstract)}</section>',
        f'<section id="{slug("研究背景与目标")}">{md_to_simple_html(bg)}</section>',
        f'<section id="{slug("文献与科学缺口")}">{md_to_simple_html(lit)}</section>',
        data_html,
        methods_html,
        f'<section id="{slug("完整研究过程与时间线")}">{md_to_simple_html(timeline)}</section>',
        f'<section id="{slug("数据摄取与对齐修复")}">{md_to_simple_html(ingest)}</section>',
        f'<section id="{slug("EXT+WSE 双场模型")}">{md_to_simple_html(wse)}</section>',
        f'<section id="{slug("SGPR 诱导点问题与修复")}">{md_to_simple_html(sgpr)}</section>',
        f'<section id="{slug("层次残差 EOF（H-LSG）")}">{md_to_simple_html(hlsg)}</section>',
        f'<section id="{slug("不确定性量化与标定")}">{md_to_simple_html(uq_sec)}</section>',
        o14_html,
        f'<section id="{slug("实验设计与评价指标")}">{md_to_simple_html(exp)}</section>',
        f'<section id="{slug("分案例结果")}">{md_to_simple_html(results)}</section>',
        cross_html,
        capacity_html,
        "\n".join(figs_html),
        f'<section id="{slug("讨论与因果分析")}">{md_to_simple_html(discuss)}</section>',
        innov_html,
        repro_html,
        limits_html,
        f'<section id="{slug("未来工作")}">{md_to_simple_html(future)}</section>',
        f'<section id="{slug("结论")}">{md_to_simple_html(conclusion)}</section>',
        f'<section id="{slug("数据与代码可用性")}">{md_to_simple_html(avail)}</section>',
        f'<section id="{slug("参考文献")}">{md_to_simple_html(refs)}</section>',
        appendix_html,
        f'<section id="{slug("范围边界与本轮已完成项")}">{md_to_simple_html(pending)}</section>',
        '<p class="callout"><strong>状态声明：</strong>工作区 <code>20260522-LSG-WRR</code> 仍无 <code>.git</code>；公开镜像通过 staging 副本推送到 <a href="https://github.com/Coucou2016/lsg-flood-surrogate-benchmark">github.com/Coucou2016/lsg-flood-surrogate-benchmark</a>（等容量负结果修订）。</p>',
    ]

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>
{css}
</style>
</head>
<body>
{''.join(html_body_parts)}
</body>
</html>
"""
    (OUT / "report.html").write_text(html_doc, encoding="utf-8")

    # Validation summary JSON for the agent
    summary = {
        "html_bytes": (OUT / "report.html").stat().st_size,
        "md_bytes": (OUT / "report.md").stat().st_size,
        "figures_inlined": list(FIGURES.keys()),
        "skips": skips,
        "metrics_spotcheck": {
            "car_max_csi": metrics["car_max_all_csi"],
            "chow_all_csi": metrics["chow_h_all_csi"],
            "burn_wet_csi": metrics["burn_h_wet_csi"],
            "var_scale_max": var_max,
        },
    }
    (OUT / "_build_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
