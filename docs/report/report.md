# LSG 多保真洪水淹没代理模型：残差层次分区、神谕误差预算与 CRPS 方差标定的公开数据研究报告

**Low-fidelity, Spatial analysis, and Gaussian Process Learning（LSG）公共基准复现与诊断扩展**

| 项目 | 内容 |
| --- | --- |
| 报告类型 | 正式科学研究报告（方法/诊断导向，非短文） |
| 项目仓库 | `I:\Projects\20260522-LSG-WRR` |
| 主案例 | Carlisle；次案例 Chowilla；第三案例 Burnett |
| 证据日期 | 2026-08-16（与 `docs/paper/00_progress_review.md` 对齐） |
| 目标期刊语境 | WRR / JoH / EMS（methods） |
| 一句话论点 | 多保真 LSG 是技能主源；残差分区主要压缩截断间隙（O2−O1）；CRPS 方差标定改善概率可靠性且不改 CSI/RMSE；Chowilla all-cells 是强 LF 协议反例 |
| Git 状态 | 仓库基线无 `.git` / 本交付仅本地写 `docs/report/`，不提交不推送 |
| 图件风格 | SciencePlots；Times New Roman；600 dpi PNG 并存；HTML 优先内联 SVG |
| 顾问评审 | ChatGPT 结构评审 https://chatgpt.com/c/6a816202-85e0-83ea-9ed9-3de1fdb994cb；大改章节合并未执行 |

---

## 报告读法（结构边界）

本文件是**可离线传阅的正式研究工作稿**：主体按科学逻辑组织，但保留工程诊断闭环（数据对齐、SGPR 诱导点配置、UQ 标定）以便复现。阅读时请优先沿“问题→证据→诊断→最小处理→验证→边界”主线；“完整时间线”与“待补充清单”服务归档与缺口透明，发布终稿可将冗长 chronology 下沉附录。O1–O4 与跨案例差异支持**机制诊断/反事实归因**，不宜写成严格可加的因果贡献率。方差标定改善的是概率评分；点估计 CSI/RMSE 因均值不变而按构造保持不变。

---


## 目录

- 报告读法（结构边界）
- 摘要与执行概要
- 研究背景与目标
- 文献与科学缺口
- 数据来源与案例研究
- 方法学基础
- 完整研究过程与时间线
- 数据摄取与对齐修复
- EXT+WSE 双场模型
- SGPR 诱导点问题与修复
- 层次残差 EOF（H-LSG）
- 不确定性量化与标定
- O1–O4 误差预算
- 实验设计与评价指标
- 分案例结果
- 跨案例比较
- 详细图件解读
- 讨论与因果分析
- 创新点
- 可复现性与质量保证
- 局限性
- 未来工作
- 结论
- 数据与代码可用性
- 参考文献
- 附录
- 待补充清单


## 摘要与执行概要

本报告系统记录并解释仓库 `20260522-LSG-WRR` 中基于公开多保真淹没立方体的 LSG（Low-fidelity, Spatial analysis, and Gaussian Process Learning，低保真—空间分析—高斯过程学习）实现、诊断与概率扩展。LSG 不依赖 HEC-RAS、TUFLOW 或任一特定求解器品牌：它只要求成对的高精度（high-fidelity, HF）与低精度（low-fidelity, LF）淹没场。

在 Fraehr 风格的 Grp1 / `wet_train` 协议下，三案例点技能的主结论是：（1）相对 LF-only，多保真 LSG 在 Burnett 等弱 LF 情景给出清晰的 CSI（Critical Success Index，临界成功指数）与湿单元 RMSE（root mean square error，均方根误差）提升；（2）层次残差分区（H-LSG，`residual_kmeans`）主要缩小截断间隙 O2−O1，而不是以大幅 CSI 超越全局 EOF（empirical orthogonal function，经验正交函数）作为 headline；（3）Carlisle Max 路径上 CRPS（Continuous Ranked Probability Score，连续分级概率评分）方差标定把方差尺度压到 s≈0.417，CRPS 由 0.039 降至 0.028，而 CSI/RMSE 因均值不变而按构造保持不变；（4）Chowilla 在 all_cells 上出现 CSI≈0.3902 的“崩溃”，但在 `wet_train` 上 CSI≈0.9756、RMSE≈0.093 m——这是强 LF 范围情景下的评分协议反例，不是静默失败。评价单元是 hold-out 事件（Carlisle/Chowilla Max：N=1；Burnett：N=18），不是栅格单元。

报告按教学体例撰写：每个图/表前说明动机，之后逐面板解读，并给出机制诊断时序（问题→证据→诊断→最小处理→验证→边界）。缺失资产一律标为「待补充」，不编造。


## 研究背景与目标

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


## 文献与科学缺口

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

可主张：同时域残差层次多分区 LSG（全局模态 + WSE 残差局部基；EXT 全局）+ CRPS 标定的 LSG 地图后验 + O1–O4 神谕阶梯的公开三案例评估。不可主张：首个局部 EOF、首个 LSG 误差分解、zoning 总是大幅提升 CSI。


## 数据来源与案例研究

**表：案例与数据集清单（来自 data/DATA_INVENTORY.md / README）**

| 案例 | 角色 | HF / LF | 配置 | 几何规模（文档） | 默认时间处理 | 数据状态 |
| --- | --- | --- | --- | --- | --- | --- |
| Carlisle（英国） | 主案例 | LISFLOOD-FP × HEC-RAS | config/carlisle.yaml | HF ≈ 581 061 单元；LF 有效 5 681（去 ghost） | 完整时间序列可训（LSG-TS） | 已解压（~9.6 GB，Figshare 10.26188/24312658） |
| Chowilla（澳大利亚） | 次案例 | 细网格 / 粗网格 HEC-RAS | config/chowilla.yaml | HF ≈ 110k 单元；29 事件 / 10 组 | time_reduction: max | 可用（junction / zip） |
| Burnett（澳大利亚） | 第三案例 | TUFLOW × HEC-RAS | config/burnett.yaml | HF ≈ 780 785；LF ≈ 15 256；74 事件 / 4 组 | time_reduction: max | 可用（junction / zip） |
| Brisbane（附录） | 许可门控附录 | TUFLOW × URBS（Wang 2026） | config/brisbane.yaml | 待补充（许可数据未到） | 待补充 | 未运行（许可门控） |


### 评分掩膜术语（首次完整定义）

- **all_cells（全单元）**：在整个 HF 网格上计算列联表与 RMSE。包含大量“始终干燥”单元；当模型在训练湿掩膜外漏报/误报时，指标可剧烈变化。
- **wet_train（训练湿掩膜）**：Fraehr Categories 定义的湿单元索引（Carlisle Grp1 与 Categories_HFdata_ValidateOnGrp_1 对齐，文档记 239 482 单元）。这是与发表 LSG 表格可比的主协议。
- **阈值 0.03 m**：深度 ≥ 0.03 m 视为湿，用于 POD/RFA/CSI。

### 案例科学角色

- **Carlisle**：可跑完整 LSG-TS 与 LSG-Max；是 SGPR 修复与 UQ before/after 的主证据场。
- **Chowilla**：LF 范围已经很强（CSI≈0.93）；用来展示“协议反例”与 zoning 对 O2−O1 的作用。
- **Burnett**：弱 LF（CSI≈0.85），用来展示多保真 LSG 的主技能跃迁。


## 方法学基础

**表：方法变体与符号位置**

| 变体 / 模块 | 英文全称与缩写 | 物理/算法含义 | 本项目中的位置 |
| --- | --- | --- | --- |
| LSG | Low-fidelity, Spatial analysis, and Gaussian Process Learning | 用低精度水动力场投影到高精度经验正交模态，再以高斯过程学习模态系数映射，重构淹没场 | 主方法栈；不依赖特定求解器品牌 |
| LSG-TS | LSG Time Series | 对完整淹没时间序列训练；最大淹没面由预测序列时间维取 max | Carlisle 主折已跑通；Chowilla/Burnett 全时序 Grp1 未运行（内存） |
| LSG-Max | LSG Maximum surface | 直接学习各事件最大水深面 | 三案例 headline 对比的主表面路径 |
| EXT + WSE | Extent + Water Surface Elevation（lsg.field: wse_ext） | 分别学习二值淹没范围与水面高程，再由 depth = max(WSE−Z, 0) 并经 EXT 门控得到水深 | 官方点估计路径；非 LF 范围后处理门控 |
| H-LSG / residual_kmeans | Hierarchical residual LSG（残差层次分区） | 全局 EOF 之上，对 WSE 残差做 k-means 分区并拟合局部残差 EOF；EXT 保持全局 | 默认 zoning；相对 global 做消融 |
| SGPR | Sparse Gaussian Process Regression（稀疏高斯过程回归） | 用诱导点近似全 GP，降低大样本代价 | 每 EOF 模态一个 SGPR；min_inducing_points 防 Max 路径崩溃 |
| O1–O4 | Oracle error budget ladder（神谕误差阶梯） | 反事实分解截断 / LF 可表达性 / GP 映射误差 | lsg/diagnostics.py；depth RMSE on wet_idx |
| CRPS-scale UQ | Continuous Ranked Probability Score variance calibration | 训练集拟合全局方差尺度 Var_cal = s·Var_raw，均值不变 | 三案例均有 before/after；Chowilla CRPS 近乎持平需如实报告 |
| wet_correlation 分区 | Wet-correlation zoning | 按湿相关结构划分空间再拟合残差/局部模态 | Chowilla Grp1 敏感性已跑；非默认 headline |


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


## 完整研究过程与时间线

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


## 数据摄取与对齐修复

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


## EXT+WSE 双场模型

### 为何引入

单一深度 EOF 把“是否淹没”与“淹没多深”耦在同一连续场里，容易在干燥区产生虚假浅水，推高 RFA（relative false alarm，相对虚警）。

### 机制

- **EXT（extent，淹没范围）**：在临时单元上学习二值湿/干（阈值相关）。
- **WSE（water-surface elevation，水面高程）**：在湿单元上学习水面。
- **合成**：`where(EXT==1, WSE, Z)`，再 `depth=max(WSE−Z,0)`；常湿（AF）强制为湿。

### 重要澄清

`lf_extent_gated` 仅作诊断对照，**不是**官方模型。官方点估计是训练得到的 EXT+WSE。


## SGPR 诱导点问题与修复

### 初始现象

H-LSG 在 Carlisle Max 上出现 RMSE/O4 恶化：pre-fix H-LSG Max 测试 O4=0.267 m，而同一残差结构在修复后 O4=0.094 m。

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

修复后 Max CSI 仍为 0.9757，RMSE(all)=0.061 m；TS max-surface CSI=0.9702。pre-fix TS 的“漂亮”RMSE 0.055 与缺陷残差 GP 共存，**不得**当作最终结果。


## 层次残差 EOF（H-LSG）

### 定义

在全局 EOF 重构之上，对 **WSE 残差**做 k-means 分区（默认 `n_zones=4`），每区再拟合少量残差 EOF（`residual_eof_modes=3`），并用额外 GP 学习残差 EC。EXT 分支保持全局，避免把范围学习切碎。

### 它在方程中的位置

HF ≈ 全局模态重构 + Σ_zones 残差模态重构；GP 输入级联全局伪 EC 与分区残差伪 EC。

### 实证角色

- Chowilla：H-LSG 的 O2−O1=0.013，global=0.057；湿 CSI 几乎持平（0.9756 vs 0.9744）。
- 因此分区是**截断诊断/ refinement**，不是 CSI 冠军叙事。


## 不确定性量化与标定

### 原始 UQ

每个 EOF 模态保留 GP 方差，单元深度方差闭式传播并加残差/截断项（`lsg/uq.py`）。

### 问题

Carlisle Max 未标定 `coverage_90≈0.996`，区间过宽（over-dispersion）。全单元 coverage 还会被 EXT 干燥零方差单元抬高，故报告 `coverage_*_active`（观测或均值 ≥ τ 的主动单元）。

### 标定

在训练集上最小化高斯 CRPS，拟合全局 s：`Var_cal=s·Var_raw`。Carlisle Max s=0.417；TS s=0.900。

### 结果

Max CRPS 0.039→0.028；CSI/RMSE 不变。Chowilla/Burnett 已用保存状态重评 before/after：Burnett CRPS 0.133→0.127（s≈0.604）；Chowilla CRPS 2.155→2.155 近乎持平且 coverage 远离名义（s≈0.419；workflow-fit s≈0.309）。


## O1–O4 误差预算

定义（`lsg/diagnostics.py`；`wse_ext` 下 EXT/WSE 同步神谕再门控成深度 RMSE）：

| 阶 | 名称 | 物理含义 |
| --- | --- | --- |
| O1 | 全秩 HF EC 神谕 | 数值 SVD 地板 |
| O2 | 截断 k 模态 HF EC | EOF 截断 |
| O3 | LF 伪 EC 无 GP 重构 | LF 可表达性 |
| O4 | 完整 LSG（GP+k） | 总误差 |

差值解读：O2−O1≈截断间隙；O3−O2≈LF 投影损失；O4−O3≈GP 映射等剩余。

**表：测试集 O1–O4（depth RMSE，协议湿索引）**

| 案例 / 变体 | O1 | O2 | O3 | O4 | O2−O1 | 解读要点 |
| --- | --- | --- | --- | --- | --- | --- |
| Carlisle LSG-TS H-LSG+fix | 0.018 | 0.033 | 0.240 | 0.102 | 0.015 | 截断间隙中等；O3 高提示 LF 伪 EC 表达受限 |
| Carlisle LSG-Max H-LSG+fix | 0.048 | 0.052 | 0.068 | 0.094 | 0.005 | O2−O1≈0.005，残差分区显著压缩截断间隙 |
| Carlisle LSG-Max global (pre-fix 对照栈) | 0.048 | 0.112 | 0.122 | 0.154 | 0.064 | O2−O1≈0.064，全局截断更重 |
| Carlisle LSG-Max H-LSG pre-fix SGPR | 0.048 | 0.052 | 0.068 | 0.267 | 0.005 | O4 暴涨至 0.267：诱导点缺陷主导，非分区本身 |
| Chowilla LSG-Max H-LSG | 0.020 | 0.034 | 0.701 | 0.093 | 0.013 | O2−O1=0.013；O3 很高（强 LF 几何下伪 EC 仍难） |
| Chowilla LSG-Max global | 0.020 | 0.078 | 0.666 | 0.088 | 0.057 | O2−O1=0.057；分区主要改截断而非 CSI |
| Burnett LSG-Max H-LSG | 0.074 | 0.083 | 0.668 | 0.387 | 0.009 | O2−O1=0.009；相对 LF 的 CSI/RMSE 提升由 LSG 主导 |
| Burnett LSG-Max global | 0.074 | 0.123 | 0.708 | 0.179 | 0.049 | O2−O1≈0.049；湿 CSI 与 H-LSG 持平，截断间隙更大 |
| Chowilla LSG-Max wet_correlation | 0.020 | 0.030 | 0.695 | 0.094 | 0.010 | O2−O1≈0.010；湿 CSI 略高于 residual_kmeans |



## 实验设计与评价指标

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


## 分案例结果

### Carlisle（主）

- LF-only：CSI(all)=0.9602，RMSE=0.074 m
- LSG-Max（H-LSG+SGPR fix）：CSI=0.9757，RMSE(all)=0.061，RMSE(wet)=0.094 m
- LSG-TS max-surface：CSI=0.9702，RMSE(all)=0.099 m
- 与 Fraehr 发表 LSG（Grp E1，湿单元 EXT+WSE）CSI≈0.969 同量级（README 对照表）

### Chowilla（次；协议反例）

- LF 已很强：CSI(all)≈0.9305
- LSG-Max H-LSG：CSI(all)≈0.3902 vs CSI(wet)≈0.9756；RMSE(wet)≈0.093 m（相对 LF 湿 RMSE≈0.690 大幅下降）
- 解释：EXT 在训练湿掩膜上学习；all_cells 暴露掩膜外系统偏差——必须双报协议

### Burnett（第三）

- LF CSI≈0.8533，RMSE≈0.989 m
- LSG-Max H-LSG CSI≈0.9752，RMSE≈0.387 m
- LSG-Max global CSI≈0.9751，RMSE≈0.179 m；O2−O1 global≈0.049 vs H-LSG≈0.009
- 这是“多保真 LSG 为主技能源”的最清晰跨案例证据；分区收益仍以 O2−O1 为主


## 跨案例比较

**表：跨案例点技能（JSON 核验；主协议见列）**

| 案例 | 变体 | 掩膜 | CSI | RMSE (m) | 来源 JSON |
| --- | --- | --- | --- | --- | --- |
| Carlisle | LF only | all_cells | 0.9602 | 0.074 | …sgpr_fix.json |
| Carlisle | LF only | wet_train | 0.9660 | 0.101 | 同上 |
| Carlisle | LSG-TS (max surface) | all / wet_train | 0.9702 / 0.9702 | 0.099 / 0.154 | 同上 |
| Carlisle | LSG-Max H-LSG+SGPR fix | all / wet_train | 0.9757 / 0.9757 | 0.061 / 0.094 | 同上 |
| Chowilla | LF only | all / wet_train | 0.9305 / 0.9247 | 0.690 / 0.690 | …hlsg_max.json |
| Chowilla | LSG-Max H-LSG | all / wet_train | 0.3902 / 0.9756 | 3.789 / 0.093 | 同上；all-cells 反例 |
| Chowilla | LSG-Max global | wet_train | 0.9744 | 0.088 | …global_max.json |
| Chowilla | LSG-Max wet_correlation | wet_train | 0.9778 | 0.094 | …wet_correlation_max.json |
| Burnett | LF only | all / wet_train | 0.8528 / 0.8533 | 0.983 / 0.989 | …hlsg_max.json |
| Burnett | LSG-Max H-LSG | all / wet_train | 0.9752 / 0.9752 | 0.384 / 0.387 | 同上 |
| Burnett | LSG-Max global | wet_train | 0.9751 | 0.179 | …global_max.json |


### 比较命题

1. **技能主源**：Burnett 式弱 LF → LSG 大幅提升；不是 zoning。
2. **分区作用**：看 O2−O1（Chowilla/Burnett global A/B 均已齐），不看 CSI 排行榜。
3. **协议敏感性**：Chowilla all-cells vs wet_train 必须并排出现。
4. **UQ**：三案例均有 before/after；Carlisle/Burnett 改善；Chowilla CRPS 近乎持平、coverage 恶化——如实报告。
5. **分区敏感性**：Chowilla `wet_correlation` 湿 CSI≈0.9778，略高于 H-LSG，仍非 headline。


## 详细图件解读

**figure_manifest.json：** 跳过项为空（[]）。

### 图1 跨案例 CSI 与湿训练 RMSE（wet_train）

**为何制作 / 回答什么问题 / 在报告中的角色**

回答 RQ1：在统一湿训练掩膜下，LF-only 与 LSG 变体的点技能如何跨 Carlisle/Chowilla/Burnett 排列。角色：执行摘要级总览，先于分区消融与 UQ。

![图1 跨案例 CSI 与湿训练 RMSE（wet_train）](../../outputs/figures/fig01_cross_case_csi_rmse_wet_train.svg)

<p class="md-note"><em>说明：Markdown 使用相对路径引用插图；自包含离线要求仅强制适用于 report.html（图为内联 SVG / Base64）。</em></p>


**如何读图（坐标、图例、颜色、指标）**

横轴多为案例或方法分组，纵轴为 CSI（无量纲，0–1，越高越好）或 RMSE（米，越低越好）。颜色区分 LF / LSG-Max / 必要时 TS。误差条若存在则来自折内单元汇总（以实际图面为准）。请同时看成对的 CSI 与 RMSE，避免只宣扬单一指标。

**逐面板/子图说明**

左类面板（CSI）：比较各案例 LF 与 LSG 的命中—虚警综合技巧。右类面板（RMSE）：强调深度误差，尤其 Chowilla 在湿掩膜上 RMSE 大幅下降。若某案例缺柱，对照 manifest skips，不得手绘填补。

**可见模式**

Burnett：LSG 相对 LF 的 CSI 由约 0.8533 升至约 0.9752。Carlisle：高位改进更细（LF≈0.9660 → Max≈0.9757）。Chowilla：湿 CSI 高，但需结合图5/表理解 all-cells 反例。

**模式可能原因（因果与时序）**

因果链：弱 LF 几何误差大 → 伪 EC+GP 映射可学到系统订正 → CSI/RMSE 改善显著；强 LF 范围已准 → CSI 抬升空间小，但深度仍可订正。

**可结论 / 不可结论**

可以：断言多保真 LSG 在公开协议上可复现的点技能格局。不可以：仅凭此图声称残差分区是 CSI 主因（需图3/O 表）。

**非专业类比**

像用粗分辨率天气预报当地气温：如果粗预报已经“会不会下雨”很准，你对“是否下雨”的提升有限，但仍可能把雨强（水深）校正得更好。

### 图2 O1–O4 误差预算条形图

**为何制作 / 回答什么问题 / 在报告中的角色**

回答 RQ2：误差落在截断、LF 表达还是 GP 映射。角色：诊断核心，支撑“分区压缩 O2−O1”而非“分区碾压 CSI”。

![图2 O1–O4 误差预算条形图](../../outputs/figures/fig02_error_budget_o1o4.svg)

<p class="md-note"><em>说明：Markdown 使用相对路径引用插图；自包含离线要求仅强制适用于 report.html（图为内联 SVG / Base64）。</em></p>


**如何读图（坐标、图例、颜色、指标）**

每组柱对应 O1–O4 的深度 RMSE（米）。阅读时先看 O1 地板，再看 O2 相对 O1 的抬升（截断），再看 O3（LF），最后 O4（全系统）。

**逐面板/子图说明**

按案例/变体分面：Carlisle TS/Max、Chowilla、Burnett。Max 上 O2−O1 很小（约 0.005）说明残差分区后截断间隙被压薄；TS 上 O3 很高说明时间序列路径更受 LF 伪 EC 限制。

**可见模式**

Carlisle Max O2−O1≈0.005；Chowilla H-LSG≈0.013 vs global≈0.057；Burnett≈0.009。

**模式可能原因（因果与时序）**

时序：先有全局截断过大 → 引入残差分区 → O2 下降 → 但若 SGPR 诱导点错误，O4 会单独爆炸（见图 eth 叙事/表）→ 修复诱导点后 O4 回落。

**可结论 / 不可结论**

可以：用 O 阶梯定位误差部件。不可以：把 O4 自动等于“模型无能”（需排除近似数值病态）。

**非专业类比**

像体检分项：O1 是仪器噪声底，O2 是“只做主要检查项目”的信息损失，O3 是“用低精度仪器硬测”的损失，O4 是走完整流程后的总偏差。

### 图3 Global vs H-LSG 消融（含 O2−O1）

**为何制作 / 回答什么问题 / 在报告中的角色**

回答“分区到底帮在哪里”。角色：把创新点从 CSI 冠军叙事纠正为截断 refinement。

![图3 Global vs H-LSG 消融（含 O2−O1）](../../outputs/figures/fig03_global_vs_hlsg_ab.svg)

<p class="md-note"><em>说明：Markdown 使用相对路径引用插图；自包含离线要求仅强制适用于 report.html（图为内联 SVG / Base64）。</em></p>


**如何读图（坐标、图例、颜色、指标）**

对比 global（zoning:none）与 H-LSG（residual_kmeans）在 CSI、RMSE、O2−O1 等指标上的并排柱。现含 Chowilla 与 Burnett。

**逐面板/子图说明**

Carlisle（若有）/Chowilla/Burnett 面板：湿 CSI 接近；O2−O1 上 H-LSG 更小。Burnett 全局 RMSE 可低于 H-LSG，故不可把分区写成万能 RMSE 赢家。

**可见模式**

Chowilla 湿 CSI：H-LSG 0.9756 vs global 0.9744；O2−O1：0.013 vs 0.057。 Burnett：H-LSG 0.9752 vs global 0.9751；O2−O1：0.009 vs 0.049。

**模式可能原因（因果与时序）**

原因：残差局部基吃掉全局模态无法表示的空间剩余；它不自动修复 LF 伪 EC 的大尺度偏差，故 CSI 可持平。

**可结论 / 不可结论**

可以：跨案例报告分区对截断间隙的作用。不可以：用 Burnett 全局更低 RMSE 反过来说 H-LSG 无用（看 O2−O1 与 CSI 持平）。

**非专业类比**

像给全国地图先画大趋势，再在各省画“剩余误差”的小修正层——总轮廓未必大变，但局部起伏更贴真值。

### 图4 UQ 的 CRPS 方差标定

**为何制作 / 回答什么问题 / 在报告中的角色**

回答 RQ3：概率层是否可校准。角色：证明“均值不动、方差可缩”，并诚实记录失败/持平案例。

![图4 UQ 的 CRPS 方差标定](../../outputs/figures/fig04_uq_calibration_crps_scale.svg)

<p class="md-note"><em>说明：Markdown 使用相对路径引用插图；自包含离线要求仅强制适用于 report.html（图为内联 SVG / Base64）。</em></p>


**如何读图（坐标、图例、颜色、指标）**

比较标定前后 CRPS、coverage（优先 active）、以及 s。三案例均有 before/after。

**逐面板/子图说明**

Carlisle Max：CRPS 明显下降。Burnett：CRPS 下降、active coverage 靠近 0.90。Chowilla：CRPS 近乎持平，coverage 远离名义——必须原样写出。

**可见模式**

Carlisle Max：CRPS 0.039→0.028，s=0.417。 Burnett：0.133→0.127，s=0.604。 Chowilla：2.155→2.155，s=0.419。

**模式可能原因（因果与时序）**

未标定截断 MSE 常使区间过宽 → CRPS 惩罚过散分布 → 学到 s<1 收缩方差；若分布形态/EXT 门控主导，标量 s 可能无效甚至有害。

**可结论 / 不可结论**

可以：Carlisle/Burnett 上断言标定可改善概率评分且不改点估计。不可以：声称三案例标定均成功。

**非专业类比**

像预报温度时平均值对了，但总把“±10°C”说成不确定度；标定相当于学会改口说“±4°C”，中心温度不变——有时改口后评分并不更好。

### 图5a Carlisle E1 空间图

**为何制作 / 回答什么问题 / 在报告中的角色**

把表格技能翻译成可检查的空间结构：LF、LSG、HF 的淹没/水深差异与单元级 P(wet)。

![图5a Carlisle E1 空间图](../../outputs/figures/fig05_spatial_maps_carlisle_E1.svg)

<p class="md-note"><em>说明：Markdown 使用相对路径引用插图；自包含离线要求仅强制适用于 report.html（图为内联 SVG / Base64）。</em></p>


**如何读图（坐标、图例、颜色、指标）**

多面板：HF / LF / LSG 水深、误差，以及 panel (e) 单元级淹没概率 P(h≥0.03 m)。色标区分水深（m）与概率（0–1）。

**逐面板/子图说明**

逐面板检查河道主槽、漫滩边缘；对照 P(wet) 是否与湿边界一致，而不是把概率面板误读成二值掩膜。

**可见模式**

与 CSI≈0.97 量级一致时，空间上应看到边缘更干净；P(wet) 均值约 0.36（Carlisle pred_examples）。

**模式可能原因（因果与时序）**

EXT+WSE 分离范围与水深 → 降低干燥区浅水伪影；GP 后验经 Tobit 得到 P(wet)。

**可结论 / 不可结论**

可以：定性支持点技能，并引用真实概率场。不可以：把 P(wet) 当成未经标定的决策概率产品而不看 CRPS/coverage。

**非专业类比**

像把模糊的卫星淹水照片（LF）对照高清航拍（HF），再看算法修复版与“会不会淹”的概率图层。

### 图5b Chowilla E1 空间图

**为何制作 / 回答什么问题 / 在报告中的角色**

可视化协议反例：为何 all-cells CSI 低而 wet_train 高；并展示真实 P(wet)。

![图5b Chowilla E1 空间图](../../outputs/figures/fig05_spatial_maps_chowilla_E1.svg)

<p class="md-note"><em>说明：Markdown 使用相对路径引用插图；自包含离线要求仅强制适用于 report.html（图为内联 SVG / Base64）。</em></p>


**如何读图（坐标、图例、颜色、指标）**

水深/误差面板 + P(wet)。关注训练湿掩膜内外的差异。

**逐面板/子图说明**

在湿掩膜内，LSG 水深应接近 HF；掩膜外可能出现系统漏检，拖累 all-cells；P(wet) 均值约 0.31。

**可见模式**

与表一致：湿 CSI≈0.9756，all-cells≈0.3902。

**模式可能原因（因果与时序）**

EXT 学习域=训练湿类别；强 LF 已覆盖大部分范围时，掩膜外评分暴露归纳偏置。

**可结论 / 不可结论**

可以：作为协议教学案例。不可以：单独用 all-cells CSI 否定湿掩膜上的深度订正成功。

**非专业类比**

像考试只复习了“常考章节”（湿掩膜），超纲题（掩膜外单元）答不好，但不能说常考题也没学会。

### 图5c Burnett E1 空间图

**为何制作 / 回答什么问题 / 在报告中的角色**

展示弱 LF 上 LSG 的空间订正幅度与 P(wet)。

![图5c Burnett E1 空间图](../../outputs/figures/fig05_spatial_maps_burnett_E1.svg)

<p class="md-note"><em>说明：Markdown 使用相对路径引用插图；自包含离线要求仅强制适用于 report.html（图为内联 SVG / Base64）。</em></p>


**如何读图（坐标、图例、颜色、指标）**

读法同 5a；panel (e) 为真实 P(wet)（Burnett 均值约 0.55）。

**逐面板/子图说明**

LF 边缘与深度误差应显著大于 Carlisle；LSG 应更接近 HF。

**可见模式**

与 CSI 0.8533→0.9752、RMSE 0.989→0.387 m 的表格叙事一致。

**模式可能原因（因果与时序）**

LF 水动力简化误差大 → 多保真映射可学空间偏差场。

**可结论 / 不可结论**

可以：支持“LSG 主技能源”，并与图3 Burnett global A/B 对照阅读。不可以：把单事件 E1 图外推为全组 18 事件的唯一形态。

**非专业类比**

像用一台偏差很大的快测仪（LF）配少量金标准（HF）做校正曲线，再快速出接近金标准的图与概率图层。

### 图6 Chowilla wet_correlation 分区敏感性

**为何制作 / 回答什么问题 / 在报告中的角色**

回答分区超参是否改变 headline：对比 global / residual_kmeans / wet_correlation。

![图6 Chowilla wet_correlation 分区敏感性](../../outputs/figures/fig06_zoning_wet_correlation_ab.svg)

<p class="md-note"><em>说明：Markdown 使用相对路径引用插图；自包含离线要求仅强制适用于 report.html（图为内联 SVG / Base64）。</em></p>


**如何读图（坐标、图例、颜色、指标）**

柱状图为湿训练 CSI 与 RMSE（及图面所示的对照量）。三柱并排，勿只读最高 CSI。

**逐面板/子图说明**

看 CSI 是否仅有微小抬升，同时回忆表中 O2−O1（wet_correlation≈0.010 vs H-LSG 0.013 vs global 0.057）。

**可见模式**

湿 CSI：global 0.9744；residual_kmeans 0.9756；wet_correlation 0.9778。 RMSE：0.088 / 0.093 / 0.094 m。

**模式可能原因（因果与时序）**

相关分区改变残差能量的空间聚合方式；对 CSI 的边际影响通常小于 LF→LSG 主效应。

**可结论 / 不可结论**

可以：报告单折敏感性。不可以：宣称 wet_correlation 全面优于 residual_kmeans 或已完成超参穷尽。

**非专业类比**

像换一种行政区划重画“剩余误差修正层”——边界换了，全国总分未必大变。


## 讨论与因果分析

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


## 创新点

**表：创新点 vs 既往工作（有边界）**

| 主张 | 相对既往工作的边界 | 本仓库证据 |
| --- | --- | --- |
| 残差层次多分区 LSG（全局+局部残差基；EXT 全局 / WSE 残差） | ≠ REOF-SGP（Wang 2025）；≠ Tan 2025 单焦点区域重训；实现 Wang 2026 点名的 zonal EOF future work | residual_kmeans 默认；O2−O1 缩小；CSI 不宣称大幅超越 global |
| CRPS 尺度标定的 LSG 地图后验方差 | ≠“首个概率淹没代理”（已有多种非 LSG GP/PCE UQ） | Carlisle Max s≈0.417，CRPS 0.039→0.028；均值不动 |
| O1–O4 神谕阶梯 | ≠ Tan 的两段式 ER_DR/ER_LSG；本报告为四段反事实深度 RMSE | 三案例 test budgets 可复现 |
| SGPR 诱导点下限与训练行初始化 | 工程稳健性，非 headline 新颖性 | Max pre-fix O4=0.267 → post-fix 0.094 |



## 可复现性与质量保证

**表：测试与可复现记录**

| 项目 | 记录 | 本报告是否重跑 |
| --- | --- | --- |
| pytest | docs/paper/03_new_results.md：80 passed, 1 skipped（本会话实验后；进度评论旧记 74） | 本文档构建未强制重跑；以 03_new_results 记录为准 |
| 评价协议 | threshold 0.03 m；all_cells + wet_train；Fraehr Categories wet_idx | 复述文档 |
| 随机种子 | config 中 random_seed: 20260814（Carlisle） | — |


### 推荐复现命令

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/run_lsg_workflow.py --config config/carlisle.yaml
python scripts/run_lsg_workflow.py --config config/chowilla.yaml
python scripts/run_lsg_workflow.py --config config/burnett.yaml
python scripts/rescore_uq_calibrated.py --config config/carlisle.yaml
.\.venv\Scripts\python.exe -m pytest tests -q
```

### 工件索引（摘要）

- Carlisle 主结果：`outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix.json`
- Carlisle UQ：`..._uq_calibrated.json`
- Chowilla H-LSG / global / wet_correlation：`..._hlsg_max.json` / `..._global_max.json` / `..._wet_correlation_max.json`
- Chowilla/Burnett UQ rescore：`..._hlsg_max_uq_calibrated.json`
- Burnett H-LSG / global：`..._hlsg_max.json` / `..._global_max.json`
- 图：`outputs/figures/fig01`–`fig06_*`（manifest skips=[]）


## 局限性

**表：局限性与缺口**

| 限制 / 缺口 | 状态 | 影响 |
| --- | --- | --- |
| Chowilla / Burnett 全时序 Grp1 折 | 未运行（内存；Burnett HF 堆叠≈199 GB ≫ ~128 GB RAM） | 不能声称三案例均完成 LSG-TS |
| 等容量 global vs H-LSG；非残差地理分区对照 | 未运行（除 Chowilla wet_correlation 敏感性） | 不能把分区收益与额外容量完全拆开 |
| Carlisle/Chowilla Max Grp1 测试事件数 | N_event=1（Burnett=18） | 单事件对比不可过度外推 |
| CRPS 尺度嵌套 CV；oracle 顺序置换 | 未运行 | s 为训练集拟合；O1–O4 为路径有序反事实 |
| Chowilla Max CRPS 标定 | rescore：CRPS 近乎持平、coverage 远离名义 | 不可把 Carlisle 标定收益外推为普适 |
| Brisbane 许可数据 | 未运行 | 附录级，不作主结论 |
| FloodCastBench | 未运行 / 推迟 | 外部基准未接 |
| 跨事件/站点的 var_scale 迁移 | 开放问题 | 当前每案例重拟合 |
| residual_kmeans 空间连通性图 | 待补充 | 分区指残差响应类，未必地理连通 |



## 未来工作

1. 在内存允许或流式摄取就绪时补跑 Chowilla/Burnett 全时序 Grp1（Burnett HF 堆叠≈199 GB，当前主机 ~128 GB RAM 不可行）。
2. 等容量（匹配总模态/诱导点）global vs H-LSG；残差区连通性图。
3. CRPS *s* 嵌套 CV 与跨站点迁移；解释 Chowilla 标定持平/coverage 恶化。
4. 许可到来后的 Brisbane 附录复现；FloodCastBench。
5. 区数/残差模态更系统的扫描（wet_correlation 已有单折证据）。


## 结论

在三个公开多保真案例上，本项目复现并扩展了 LSG 栈：EXT+WSE 双场、残差层次分区、SGPR 诱导点稳健化、CRPS 方差标定与 O1–O4 神谕预算。**技能提升的主导因素是多保真 LSG 本身**；残差分区稳定地表现为持出子空间可表达性间隙（O2−O1）的缩小（Chowilla/Burnett global A/B 均已齐）；概率标定在 Carlisle/Burnett 改善可靠性，在 Chowilla Max 上 CRPS 近乎持平——必须如实报告；点估计 CSI/RMSE 因均值不变而**按构造**保持不变；单元级 P(wet) 与 Chowilla `wet_correlation` 敏感性已补齐。Chowilla 提醒社区必须同时报告 all_cells 与 wet_train。评价单元是 hold-out 事件（Carlisle/Chowilla Max 为 N=1，Burnett 为 N=18），不是栅格单元。这些结论均锚定于本仓库 JSON/图件，可独立复核。


## 数据与代码可用性

- 公共立方体：Figshare DOI [10.26188/24312658](https://doi.org/10.26188/24312658)（CC BY 4.0）。
- 本仓库配置与脚本：`config/*.yaml`、`lsg/`、`scripts/`（无密钥）。
- Brisbane TUFLOW/URBS：昆士兰州政府许可，需申请；本地为 missing。
- Hybrid LSG 参考代码：https://github.com/nfraehr/Hybrid_LSG_model


## 参考文献

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


## 附录

### A. 术语与符号表

**表：术语与符号词汇表**

| 中文名 | 英文全称 | 缩写/符号 | 物理意义 | 方程/流程位置 | 本项目引入原因 |
| --- | --- | --- | --- | --- | --- |
| 低保真—空间分析—高斯过程学习 | Low-fidelity, Spatial analysis, and Gaussian Process Learning | LSG | 多保真淹没代理总方法 | 全管道 | 研究对象 |
| 高精度 / 低精度 | High-/Low-fidelity | HF / LF | 细/粗水动力解 | 输入场 | 多保真设定 |
| 经验正交函数 | Empirical Orthogonal Function | EOF | 空间模态基 | 降维 | 压缩淹没场 |
| 展开系数 | Expansion Coefficient | EC / 伪 EC | 模态时间/事件系数；伪 EC 来自 LF 投影 | GP 输入 | 建立 LF→HF 学习 |
| 淹没范围 / 水面高程 | Extent / Water-Surface Elevation | EXT / WSE | 湿干与水面 | 双场重构 | 降虚警、近发表 CSI |
| 层次残差 LSG | Hierarchical residual LSG | H-LSG | 全局+残差分区 | WSE 残差 | 实现 zonal future work |
| 稀疏高斯过程回归 | Sparse Gaussian Process Regression | SGPR | 诱导点近似 GP | 模态映射 | 可扩展回归 |
| 诱导点 | Inducing points | Z_ind / m | 稀疏近似支撑集（与地形高程 Z 区分） | SGPR | Max 路径数值稳健 |
| 临界成功指数 | Critical Success Index | CSI | hits/(hits+misses+FA) | 点技能 | 淹没范围技巧 |
| 均方根误差 | Root Mean Square Error | RMSE | 水深误差均方根 | 点技能 | 深度精度 |
| 连续分级概率评分 | Continuous Ranked Probability Score | CRPS | 概率预报评分 | UQ 目标 | 方差标定 |
| 神谕误差阶梯 | Oracle error budget | O1–O4 | 反事实误差分解 | 诊断 | 归因 |
| 残差 | Residual | ε | 全局重构后的剩余场 | 分区 EOF | 局部修正 |
| 湿训练掩膜 | Fraehr wet_train mask | wet_train | 训练湿类别单元 | 评分 | 与发表表对齐 |


### B. 工件索引

| 类别 | 路径 |
| --- | --- |
| 进度/文献/框架 | `docs/paper/00_progress_review.md` 等 |
| 评价 JSON | `outputs/evaluation/{carlisle,chowilla,burnett}/` |
| 图件 | `outputs/figures/fig01*`–`fig06*` |
| 配置 | `config/{carlisle,chowilla,burnett,burnett_global,chowilla_wet_correlation}.yaml` |
| 核心代码 | `lsg/{gp,zoning,uq,diagnostics,wse_ext,fraehr}.py` |
| 本报告 | `docs/report/report.{html,md,pdf}` |


## 待补充清单

1. Chowilla / Burnett **全时序** Grp1 折 — **未运行**（Burnett HF 堆叠≈199 GB ≫ ~128 GB RAM；Chowilla 双场+UQ 同样受限）。
2. 等容量 global vs H-LSG、非残差地理分区对照（除已完成的 Chowilla `wet_correlation` 单折）、oracle 顺序置换 — 未运行。
3. Brisbane 许可立方体复现 — 未运行。
4. FloodCastBench — 未运行/推迟。
5. 训练硬件型号与完整墙钟时间表 — 仅有 JSON 秒数，机型待补充。
6. 跨站点 `var_scale` 迁移 / 嵌套 CV — 开放问题（Chowilla 标定持平已提示不可盲目迁移）。
7. residual_kmeans 区划连通性图 — 待补充。



---

**状态声明：** 仅本地修改，未提交、未推送、未创建 PR、未部署。
