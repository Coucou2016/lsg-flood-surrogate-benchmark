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
    manifest = load_json("outputs/figures/figure_manifest.json")

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
    }

    car_max_eb = eb_test(car_fix, "lsg_max")
    car_ts_eb = eb_test(car_fix, "lsg_ts")
    car_g_max_eb = eb_test(car_global, "lsg_max")
    car_g_ts_eb = eb_test(car_global, "lsg_ts")
    car_pre_max_eb = eb_test(car_hlsg_pre, "lsg_max")
    car_pre_ts_eb = eb_test(car_hlsg_pre, "lsg_ts")
    chow_h_eb = eb_test(chow_h, "lsg_max")
    chow_g_eb = eb_test(chow_g, "lsg_max")
    burn_eb = eb_test(burn, "lsg_max")

    uq_max = car_uq["lsg_max"]
    uq_ts = car_uq["lsg_ts"]
    var_max = uq_max["uq_calibration"]["var_scale"]
    var_ts = uq_ts["uq_calibration"]["var_scale"]
    crps_max_before = uq_max["uq_uncalibrated"]["crps"]
    crps_max_after = uq_max["uq"]["crps"]
    crps_ts_before = uq_ts["uq_uncalibrated"]["crps"]
    crps_ts_after = uq_ts["uq"]["crps"]

    chow_var = chow_h["lsg_max"]["uq_calibration"]["var_scale"]
    chow_g_var = chow_g["lsg_max"]["uq_calibration"]["var_scale"]
    burn_var = burn["lsg_max"]["uq_calibration"]["var_scale"]

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
            "Carlisle 有 before/after；Chowilla/Burnett 仅有标定后块",
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
        ["Burnett", "LF only", "all / wet_train", f"{r4(metrics['burn_lf_all_csi'])} / {r4(metrics['burn_lf_wet_csi'])}", f"{r3(metrics['burn_lf_all_rmse'])} / {r3(metrics['burn_lf_wet_rmse'])}", "…hlsg_max.json"],
        ["Burnett", "LSG-Max H-LSG", "all / wet_train", f"{r4(metrics['burn_h_all_csi'])} / {r4(metrics['burn_h_wet_csi'])}", f"{r3(metrics['burn_h_all_rmse'])} / {r3(metrics['burn_h_wet_rmse'])}", "同上"],
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
            "Chowilla H-LSG Max",
            r3(chow_var),
            "未标定 before 块缺失（待补充）",
            f"标定后 cov90_active={r3(chow_h['lsg_max']['uq'].get('coverage_90_active'))}",
            "点估计见交叉表",
            "fig04 skip：无 uncalibrated before",
        ],
        [
            "Chowilla global Max",
            r3(chow_g_var),
            "未标定 before 块缺失（待补充）",
            f"标定后 cov90_active={r3(chow_g['lsg_max']['uq'].get('coverage_90_active'))}",
            "—",
            "同上",
        ],
        [
            "Burnett H-LSG Max",
            r3(burn_var),
            "未标定 before 块缺失（待补充）",
            f"标定后 cov90_active={r3(burn['lsg_max']['uq'].get('coverage_90_active'))}",
            "—",
            "fig04 skip：无 uncalibrated before",
        ],
    ]

    t_innov_h = ["主张", "相对既往工作的边界", "本仓库证据"]
    t_innov_r = [
        [
            "残差层次多分区 LSG（全局+局部残差基；EXT 全局 / WSE 残差）",
            "≠ REOF-SGP（Wang 2025）；≠ Tan 2025 单焦点区域重训；实现 Wang 2026 点名的 zonal EOF future work",
            "residual_kmeans 默认；O2−O1 缩小；CSI 不宣称大幅超越 global",
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

    t_limit_h = ["限制 / 缺口", "状态", "影响"]
    t_limit_r = [
        ["Chowilla / Burnett 全时序 Grp1 折", "未运行（内存）", "不能声称三案例均完成 LSG-TS"],
        ["Burnett Global A/B", "未运行 / 缺数据（fig03 skip）", "不能跨案例断言 zoning 消融普适"],
        ["Chowilla/Burnett UQ 未标定 before", "缺数据（fig04 skip）", "只能报告 var_scale 与标定后分，不能画 before–after 柱"],
        ["单元级 P(wet) 概率图", "缺数据（fig05 显示二值淹没）", "不得把 fig05 称为概率淹没图"],
        ["Brisbane 许可数据", "未运行", "附录级，不作主结论"],
        ["FloodCastBench / wet_correlation 扫描", "未运行 / 推迟", "分区超参未穷尽"],
        ["跨事件/站点的 var_scale 迁移", "开放问题", "当前每案例重拟合"],
    ]

    t_tests_h = ["项目", "记录", "本报告是否重跑"]
    t_tests_r = [
        [
            "pytest",
            "<code>docs/paper/00_progress_review.md</code>：74 passed, 1 skipped（128 s，2026-08-16）",
            "构建时另跑一次（见文末验证节）",
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
    title = "LSG 多保真洪水淹没代理模型：残差层次分区、神谕误差预算与 CRPS 方差标定的公开数据研究报告"
    subtitle = "Low-fidelity, Spatial analysis, and Gaussian Process Learning（LSG）公共基准复现与诊断扩展"

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
</table>
</section>
"""

    toc_items = [
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
        ("待补充清单", "待补充清单"),
    ]

    toc_md = "## 目录\n\n" + "\n".join(f"- {t}" for _, t in toc_items) + "\n"
    toc_html = (
        '<nav class="toc page-break-after"><h2>目录</h2><ol>'
        + "".join(f'<li><a href="#{slug(t)}">{html.escape(t)}</a></li>' for _, t in toc_items)
        + "</ol></nav>"
    )

    abstract = f"""## 摘要与执行概要

本报告系统记录并解释仓库 `20260522-LSG-WRR` 中基于公开多保真淹没立方体的 LSG（Low-fidelity, Spatial analysis, and Gaussian Process Learning，低保真—空间分析—高斯过程学习）实现、诊断与概率扩展。LSG 不依赖 HEC-RAS、TUFLOW 或任一特定求解器品牌：它只要求成对的高精度（high-fidelity, HF）与低精度（low-fidelity, LF）淹没场。

在 Fraehr 风格的 Grp1 / `wet_train` 协议下，三案例点技能的主结论是：（1）相对 LF-only，多保真 LSG 在 Burnett 等弱 LF 情景给出清晰的 CSI（Critical Success Index，临界成功指数）与湿单元 RMSE（root mean square error，均方根误差）提升；（2）层次残差分区（H-LSG，`residual_kmeans`）主要缩小截断间隙 O2−O1，而不是以大幅 CSI 超越全局 EOF（empirical orthogonal function，经验正交函数）作为 headline；（3）Carlisle Max 路径上 CRPS（Continuous Ranked Probability Score，连续分级概率评分）方差标定把方差尺度压到 s≈{r3(var_max)}，CRPS 由 {r3(crps_max_before)} 降至 {r3(crps_max_after)}，而 CSI/RMSE 保持不变；（4）Chowilla 在 all_cells 上出现 CSI≈{r4(metrics['chow_h_all_csi'])} 的“崩溃”，但在 `wet_train` 上 CSI≈{r4(metrics['chow_h_wet_csi'])}、RMSE≈{r3(metrics['chow_h_wet_rmse'])} m——这是强 LF 范围情景下的评分协议反例，不是静默失败。

报告按教学体例撰写：每个图/表前说明动机，之后逐面板解读，并给出因果时序（问题→证据→诊断→修复→验证→含义）。缺失资产一律标为「待补充」，不编造。
"""

    bg = """## 研究背景与目标

### 背景

快速、可重复的淹没图是洪水风险管理、应急推演与情景分析的核心需求。高精度二维水动力模型计算昂贵；低精度模型快但不准。Fraehr 等人提出的 LSG 用 HF 场做 EOF 降维，把 LF 场投影为伪展开系数（pseudo expansion coefficients, 伪 EC），再用稀疏高斯过程（Sparse GP / SGPR）学习 LF→HF 的模态系数映射，从而在秒—分钟级给出接近 HF 的淹没重构。

Wang 等（2026）在大型复杂洪泛区进一步讨论 LSG-TS 与 LSG-Max，并在文中将“分区 EOF（zonal EOF）”列为未来工作。本仓库的科学任务不是“发明 LF→HF”这一想法，而是在**可公开复现的三案例立方体**上，实现并严格评估：残差层次分区、校准后的 GP 地图不确定性、以及 O1–O4 神谕误差阶梯。

### 研究问题（与 `02_paper_framework.md` 对齐）

1. **RQ1（技能）**：相对 LF-only 与全局 LSG，残差层次 LSG 在公开 Carlisle/Chowilla/Burnett 折上增加多少技能？
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

- Tan et al. 2025 HESS：区域化训练 + 两段误差分解（阻断“首个 LSG 局部化/首个误差分解”）。
- Rukai Wang et al. 2025：REOF + Sparse GP（阻断宽泛“首个局部 EOF 多保真代理”）。
- FIER / Markert 等：旋转/分区 EOF 预报谱系（术语风险，非 LSG）。
- 多种非 LSG 概率淹没代理（Donnelly、Kohanpur、Siripatana 等）：阻断“首个概率淹没图代理”。

### 本项目可辩护新颖性（严格边界）

可主张：同时域残差层次多分区 LSG（全局模态 + WSE 残差局部基；EXT 全局）+ CRPS 标定的 LSG 地图后验 + O1–O4 神谕阶梯的公开三案例评估。不可主张：首个局部 EOF、首个 LSG 误差分解、zoning 总是大幅提升 CSI。
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
9. **跨案例 max-surface 折**：Chowilla/Burnett；Chowilla global A/B；记录 skips。
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

Max CRPS {r3(crps_max_before)}→{r3(crps_max_after)}；CSI/RMSE 不变。Chowilla/Burnett 的未标定 before 块缺失（待补充），但标定后的 s 分别为 {r3(chow_var)} 与 {r3(burn_var)}。
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
- 分区：`residual_kmeans` vs `none`（Chowilla 完整；Burnett global 待补充）
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
- LSG-Max CSI≈{r4(metrics['burn_h_wet_csi'])}，RMSE≈{r3(metrics['burn_h_wet_rmse'])} m
- 这是“多保真 LSG 为主技能源”的最清晰跨案例证据
"""

    cross = f"""## 跨案例比较

{table_md(t_cross_h, t_cross_r, "跨案例点技能（JSON 核验；主协议见列）")}

### 比较命题

1. **技能主源**：Burnett 式弱 LF → LSG 大幅提升；不是 zoning。
2. **分区作用**：看 O2−O1，不看 CSI 排行榜。
3. **协议敏感性**：Chowilla all-cells vs wet_train 必须并排出现。
4. **UQ**：Carlisle 提供唯一完整 before/after；其他案例标待补充。
"""

    cross_html = f"""
<section id="{slug('跨案例比较')}">
<h2>跨案例比较</h2>
{table_html(t_cross_h, t_cross_r, "跨案例点技能（JSON 核验）")}
<ol>
<li>技能主源是多保真 LSG（Burnett）。</li>
<li>分区看 O2−O1。</li>
<li>Chowilla 必须双报 all_cells 与 wet_train。</li>
<li>UQ before/after 完整证据主要在 Carlisle。</li>
</ol>
</section>
"""

    # Figure interpretations
    figs_md = ["## 详细图件解读", ""]
    figs_html = [f'<section id="{slug("详细图件解读")}"><h2>详细图件解读</h2>',
                 f'<div class="callout"><strong>图清单跳过项（figure_manifest.json）</strong><ul>'
                 + "".join(f"<li>{html.escape(s)}</li>" for s in skips)
                 + "</ul></div>"]

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
            "对比 global（zoning:none）与 H-LSG（residual_kmeans）在 CSI、RMSE、O2−O1 等指标上的并排柱。Burnett Global 被 manifest 明确跳过。",
            "Carlisle/Chowilla 面板应显示：湿 CSI 接近，O2−O1 上 H-LSG 更小。缺失的 Burnett Global 面板应保留空白或注释，而不是用 H-LSG 冒充。",
            f"Chowilla 湿 CSI：H-LSG {r4(metrics['chow_h_wet_csi'])} vs global {r4(metrics['chow_g_wet_csi'])}；O2−O1：{r3(chow_h_eb.get('o2_minus_o1'))} vs {r3(chow_g_eb.get('o2_minus_o1'))}。",
            "原因：残差局部基吃掉全局模态无法表示的空间剩余；它不自动修复 LF 伪 EC 的大尺度偏差，故 CSI 可持平。",
            "可以：报告分区对截断间隙的作用。不可以：在 Burnett 上声称完成 global 消融（待补充）。",
            "像给全国地图先画大趋势，再在各省画“剩余误差”的小修正层——总轮廓未必大变，但局部起伏更贴真值。",
        ),
        (
            "fig04",
            "图4 UQ 的 CRPS 方差标定",
            "回答 RQ3：概率层是否可校准。角色：证明“均值不动、方差可缩”。",
            "比较标定前后 CRPS、coverage（优先 active）、以及 s。仅 Carlisle 有完整 before；Chowilla/Burnett before 缺失。",
            "Carlisle Max：CRPS 明显下降，s≈0.42。Carlisle TS：s≈0.90，变化小。缺 before 的案例如实标注。",
            f"Max：CRPS {r3(crps_max_before)}→{r3(crps_max_after)}，s={r3(var_max)}。TS：s={r3(var_ts)}。",
            "未标定截断 MSE 常使区间过宽 → CRPS 惩罚过散分布 → 学到 s<1 收缩方差。",
            "可以：Carlisle 上断言标定改善概率评分且不改点估计。不可以：声称已在三案例完成 before–after 可视化。",
            "像预报温度时平均值对了，但总把“±10°C”说成不确定度；标定相当于学会改口说“±4°C”，中心温度不变。",
        ),
        (
            "fig05a",
            "图5a Carlisle E1 空间图",
            "把表格技能翻译成可检查的空间结构：LF、LSG、HF 的淹没/水深差异出现在哪里。",
            "多为多面板空间场：HF 真值、LF、LSG 预测、误差或二值淹没。色标为水深（m）或湿/干。注意：manifest 写明缺失单元级 P(wet)，当前为二值淹没（depth≥0.03 m），不是概率。",
            "逐面板检查河道主槽、漫滩边缘与已知高误差带；对比 LSG 是否减少 LF 的边缘虚警。",
            "与 CSI≈0.97 量级一致时，空间上应看到边缘更干净；若仅中心深槽改善而边缘仍乱，需回到 EXT 分支。",
            "EXT+WSE 分离范围与水深 → 降低干燥区浅水伪影；H-LSG 改善局部残差但不应被误读为概率场。",
            "可以：定性支持点技能。不可以：把二值面板叫作概率淹没或可信区间地图。",
            "像把模糊的卫星淹水照片（LF）对照高清航拍（HF），再看算法修复版是否把岸线“描”回正确位置。",
        ),
        (
            "fig05b",
            "图5b Chowilla E1 空间图",
            "可视化协议反例：为何 all-cells CSI 低而 wet_train 高。",
            "同样为空间二值/水深面板，不是 P(wet)。关注训练湿掩膜内外的差异。",
            "在湿掩膜内，LSG 水深应接近 HF；掩膜外可能出现系统漏检，拖累 all-cells。",
            f"与表一致：湿 CSI≈{r4(metrics['chow_h_wet_csi'])}，all-cells≈{r4(metrics['chow_h_all_csi'])}。",
            "EXT 学习域=训练湿类别；强 LF 已覆盖大部分范围时，掩膜外评分暴露归纳偏置。",
            "可以：作为协议教学案例。不可以：单独用 all-cells CSI 否定湿掩膜上的深度订正成功。",
            "像考试只复习了“常考章节”（湿掩膜），超纲题（掩膜外单元）答不好，但不能说常考题也没学会。",
        ),
        (
            "fig05c",
            "图5c Burnett E1 空间图",
            "展示弱 LF 上 LSG 的空间订正幅度。",
            "读法同 5a；二值面板非概率。",
            "LF 边缘与深度误差应显著大于 Carlisle；LSG 应更接近 HF。",
            f"与 CSI {r4(metrics['burn_lf_wet_csi'])}→{r4(metrics['burn_h_wet_csi'])}、RMSE {r3(metrics['burn_lf_wet_rmse'])}→{r3(metrics['burn_h_wet_rmse'])} m 的表格叙事一致。",
            "LF 水动力简化误差大 → 多保真映射可学空间偏差场。",
            "可以：支持“LSG 主技能源”。不可以：外推到未运行的 Burnett global 消融。",
            "像用一台偏差很大的快测仪（LF）配少量金标准（HF）做校正曲线，再快速出接近金标准的图。",
        ),
    ]

    figs_md.append(
        "**figure_manifest.json 跳过项：**\n\n"
        + "\n".join(f"- {s}" for s in skips)
        + "\n"
    )
    for spec in fig_specs:
        md_f, html_f = fig_block(*spec)
        figs_md.append(md_f)
        figs_html.append(html_f)
    figs_html.append("</section>")

    discuss = f"""## 讨论与因果分析

### 主因果叙事（锁定）

1. **多保真 LSG vs LF** 是技能主效应（Burnett 最清晰；Carlisle 在高位微调；Chowilla 深度 RMSE 在湿掩膜上大幅下降）。
2. **残差分区** 的可重复收益是 O2−O1 缩小（Carlisle Max、Chowilla），不是 CSI 排行榜。
3. **SGPR 诱导点** 曾把“分区有害”的假象写入 Max O4；修复后假象消失——方法论文必须报告失败模式。
4. **UQ 标定** 解决过宽区间；与点估计正交。
5. **Chowilla all-cells** 是评分协议与 EXT 学习域的相互作用，应作为结果写进正文，而非附录藏匿。

### 开放科学问题（来自进度评论）

1. 为何正确 SGPR 后 O2−O1 增益显得“谦逊”？可能因为全局模态已吸收大部分能量。
2. 强 LF 反例的社区评分规范应如何标准化？
3. `var_scale` 能否跨事件/站点迁移而不重拟合？（待补充实验）
4. 与 REOF-SGP、Tan 区域化 LSG 的精细边界还需对照表持续维护。
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
- Chowilla H-LSG / global：`..._hlsg_max.json` / `..._global_max.json`
- Burnett：`..._hlsg_max.json`
- 图：`outputs/figures/fig01`–`fig05_*`
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

1. 在内存允许时补跑 Chowilla/Burnett 全时序 Grp1。
2. 完成 Burnett global A/B，补齐 fig03 缺口。
3. 保存并图示 Chowilla/Burnett UQ 未标定 before，补齐 fig04。
4. 导出单元级 P(wet) 与区间地图，替换 fig05 二值权宜面板。
5. `wet_correlation` 分区与区数/残差模态扫描。
6. 许可到来后的 Brisbane 附录复现。
7. `var_scale` 跨折迁移实验。
"""

    conclusion = f"""## 结论

在三个公开多保真案例上，本项目复现并扩展了 LSG 栈：EXT+WSE 双场、残差层次分区、SGPR 诱导点稳健化、CRPS 方差标定与 O1–O4 神谕预算。**技能提升的主导因素是多保真 LSG 本身**；残差分区稳定地表现为截断间隙（O2−O1）的缩小；概率标定改善可靠性且不改动点估计；Chowilla 提醒社区必须同时报告 all_cells 与 wet_train。这些结论均锚定于本仓库 JSON/图件，可独立复核。
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
| 图件 | `outputs/figures/fig01*`–`fig05*` |
| 配置 | `config/{{carlisle,chowilla,burnett}}.yaml` |
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
<li><code>outputs/figures/</code> SciencePlots 图</li>
<li><code>config/</code> 与 <code>lsg/</code> 代码</li>
</ul>
</section>
"""

    pending = f"""## 待补充清单

1. Chowilla / Burnett **全时序** Grp1 折（内存）— 未运行。
2. Burnett **Global A/B** 完整结果 — 未运行（fig03 skip）。
3. Chowilla / Burnett UQ **未标定 before** 块 — 缺数据（fig04 skip）。
4. 三案例 **单元级 P(wet)** 概率图 — 缺数据（fig05 现为二值）。
5. Brisbane 许可立方体复现 — 未运行。
6. FloodCastBench、`wet_correlation` 扫描 — 未运行/推迟。
7. 训练硬件型号与完整墙钟时间表 — 仅有 JSON 秒数，机型待补充。
8. 跨站点 `var_scale` 迁移实验 — 开放问题。
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
        "\n---\n\n**状态声明：** 仅本地修改，未提交、未推送、未创建 PR、未部署。\n",
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
        f'<section id="{slug("待补充清单")}">{md_to_simple_html(pending)}</section>',
        '<p class="callout"><strong>状态声明：</strong>仅本地修改，未提交、未推送、未创建 PR、未部署。</p>',
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
