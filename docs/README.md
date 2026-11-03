# 文档索引

先读根目录的 `README.fork.md`（这个 fork 是什么、加了什么、不声称什么），再按需要往下查。
标 **fork-only** 的文档只在我们这棵树里，作者没有向上游提议过。

| 文件 | 是什么 | 建议读者 |
|---|---|---|
| `WO-psdr-takeover.md` | **施工总账**：A–I 章，逐条记录做了什么、命令与输出、结论与未完成项（约 3,000 行，按章查） | 想知道"这件事到底怎么验的" |
| `PSDR-firmware-survey.md` | **固件只读审阅**（fork-only）：两棵树的项目代码只占约 1 万行，按模块给中文注释、缺陷清单（P0 两处，**已按分支标归属**）、架构判断与改进路线 | 要改固件的人，先读这个 |
| `PSDR-author-measurement-log.md` | **作者自述的装配与实测记录**（fork-only）：commit sha/日期/血统/原话逐条编目——2016 实测 2.5–175 MHz、-90 dBm@7MHz、-80~-85 dBm@146.4MHz、"2m 很弱可能要前放"、2.5 原型已装配、原理图 notes 区这条没挖的线索、以及库里那棵 **2019 CubeMX+FreeRTOS 重建**（`TestingMakeFile*/`，带 F746 的 Makefile） | 想知道"这板子到底跑到过什么程度"的人 |
| `PSDR-HMC1023-netlist.md` | **U287（HMC1023LP5E 可编程低通）引脚—网络—SPI 表**（fork-only）：SPI 四线接 PB12–15、校准时钟来自 Si5338、`VDDBG` 无供电是硬件缺口 | 做 #16（前放/低通）的人 |
| `PSDR-scope-and-cost.md` | **最初需求、成本结构与降本边界**（fork-only）：README 原文需求、BOM 构成（$276.78）、**VNA 判为保留项**、保留版地板 ≈$225–235、GPS 三条降本路线、LC 带通组"先验证再谈上游"与免改版的验证路径、CMOS/继电器按节点的结论、"为什么是短波而不是 UV" | 决定改版范围/预算的人 |
| `PSDR-alternates-proposal.md` | **替代件与局部改版提案**（fork-only）：U304 实测封装/偏置拓扑、国产无源件候选表（36 行/184 件）、两颗停产 IC 的三条路线（**路线 C 已按 Ron 更正**：通用 CMOS 不能顶替天线侧 GaAs）、局部改版范围 | 打算换料/改板的人 |
| `PSDR-open-data-gaps.md` | **资料缺口 + PCB 改版/移植问题**（fork-only）：要查的数据手册、2.6→2.6.1 只差 R164、断供器件封装不可替换 | 打算改板或换料的人 |
| `SOP-eda-import-2.6.1.md` | **EDA 导入 SOP**：7 步，含"直接导入只得 10/12，不是回归"与两处必须人工的步骤 | 下次往嘉立创EDA导板的人 |
| `PSDR-bringup-checklist.md` | **上电前检查表**（M3）：42 个测点带坐标与网络、射频只写观测方法、无实物逐条 SKIP | 板子到手那天 |
| `psdr-build-notes.md` | 构建笔记（F4 线的工具链与坑） | 要复现编译的人 |
| `PSDR-TAKEOVER-WORKORDER-2026-10-30.md`<br>`PSDR-TAKEOVER-PROMPT-2026-10-30.md`<br>`PSDR-TAKEOVER-EVALUATION-2026-10-30.md` | **上游给的工单/提示词与当时的评估**（历史输入，不是我们的产出；评估里个别结论已被后续实测更正，正文有标注） | 想知道起点是什么 |
| `psdr-handoff/` | 交接材料里的脚本（`anchor_check.py`、`Makefile.linux`、`PATCH-NOTES.md`），F4 锚点自证用 | 核对 F4 构建 |
| `../evidence/` | **不可重跑的现场读数**（EDA 12/12 与 DRC 513 的构成等）与其 README | 想核对"当时到底读到什么" |

## 相关但不在 `docs/`

- `dist/kicad/SHA256SUMS` + `tools/reproduce_kicad.py`：一条命令重建参考板、DRC 与制造包并自检。
- `dist/fab/PSDR_2.6.1_placement.csv`：SMT 贴装表（391 件），与 BOM 和 KiCad 锚点双向对账过。
- `tools/`：解析器、KiCad 生成器、Gerber 对拍、层覆盖率、固件统计（`fw_stats.py` / `fw_funcindex.py`）。
