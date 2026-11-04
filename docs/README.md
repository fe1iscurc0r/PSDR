# 文档索引

先读根目录的 `README.fork.md`（这个 fork 是什么、加了什么、不声称什么），再按需要往下查。
标 **fork-only** 的文档只在我们这棵树里，作者没有向上游提议过。

| 文件 | 是什么 | 建议读者 |
|---|---|---|
| `WO-psdr-takeover.md` | **施工总账**：A–K 章，逐条记录做了什么、命令与输出、结论与未完成项（3.5k 行且在长；**按章/§号查，别按行号引用**——追加记录会让行号漂移） | 想知道"这件事到底怎么验的" |
| `PSDR-firmware-survey.md` | **固件只读审阅**（fork-only）：两棵树的项目代码只占约 1 万行，按模块给中文注释、缺陷清单（**现基线 `PSDR_F7` 上 P0 只剩一处**，另一处属 `PSDR_Rebuild` 血统；新增"现基线复测"表给出 P0/P1/P2 的新行号与两条更正）、架构判断与改进路线 | 要改固件的人，先读这个 |
| `PSDR-author-measurement-log.md` | **作者自述的装配与实测记录**（fork-only）：commit sha/日期/血统/原话逐条编目——2016 实测 2.5–175 MHz、-90 dBm@7MHz、-80~-85 dBm@146.4MHz、"2m 很弱可能要前放"、2.5 原型已装配、原理图 notes 区这条没挖的线索、以及库里那棵 **2019 CubeMX+FreeRTOS 重建**（`TestingMakeFile*/`，带 F746 的 Makefile） | 想知道"这板子到底跑到过什么程度"的人 |
| `PSDR-HMC1023-netlist.md` | **U287（HMC1023LP5E 可编程低通）引脚—网络—SPI 表**（fork-only）：SPI 四线接 PB12–15、校准时钟来自 Si5338、`VDDBG` 无供电是硬件缺口 | 做 #16（前放/低通）的人 |
| `PSDR-scope-and-cost.md` | **最初需求、成本结构与降本边界**（fork-only）：README 原文需求、BOM 构成（$276.78）、**VNA 判为保留项**、保留版地板 ≈$225–235、GPS 三条降本路线、LC 带通组"先验证再谈上游"与免改版的验证路径、CMOS/继电器按节点的结论、"为什么是短波而不是 UV" | 决定改版范围/预算的人 |
| `PSDR-alternates-proposal.md` | **替代件与局部改版提案**（fork-only）：U304 实测封装/偏置拓扑、国产无源件候选表（36 行/184 件）、两颗停产 IC 的三条路线（**路线 C 已按 Ron 更正**：通用 CMOS 不能顶替天线侧 GaAs）、局部改版范围 | 打算换料/改板的人 |
| `PSDR-open-data-gaps.md` | **资料缺口 + PCB 改版/移植问题**（fork-only）：要查的数据手册、2.6→2.6.1 的**三处**电阻改动**加 2.6.1 表内自相矛盾**（§2.1，"只差 R164"那句已作废）、断供器件封装不可替换 | 打算改板或换料的人 |
| `PSDR-chronicle.md` | **编年史**（fork-only）：**第〇纪**我们从 2026-08-19 起的手（不是 10-30 的工单）、上游 2014→2025 原史 + **2014–2017 十条帖子逐条捞出的原话**（众筹支持者、热成像指到 `U241`=Si5338、"deaf as a brick −70 dBm / 差 50 dB" 的真实出处）、接手七天按天编年、对外件全表带评论 id 与字节数、**我们自己撤过的 11 条断言**（旧说法→推翻证据→现口径）、#16 点名的外部项目与 UHSDR 调研现状 | 想知道"这件事从头是怎么走过来的" |
| `PSDR-upstream-threads.md` | **上游 21 条 issue/PR 的原文存档**（引用底稿，不是我们的判断）：2026-11-04 用 REST 全量抓回的正文与 61 条评论，按 issue 照录（只压空白），编年史里每句英文原话都能在这份回查 | 要核对"某人到底说过什么" |
| `PSDR-documentation-archive.md` | **`Documentation/` 那 6 份作者材料的档案**（fork-only）：2014 半成品 VNA 说明页（作者自己的 TODO、"30mV/db 10mV/Degree" 说法，且**位号属 PSDR2 一代**：`U23`=AD8302、`U24-27`=DPDT）、2016 装配说明（图纸框还留着 `<INSERT COMPANY NAME HERE>`）、两份视频文稿（"open source""kits""我没把它设计成应急设备"原话）、2014 滤波系数表（512 点 == 固件 `FFT_BUFFER_SIZE 512`，表里是浮点系数而代码只填 1/0） | 想知道"作者留下过什么、我们此前漏了什么" |
| `PSDR-external-findings-2026-11-03.md` | **外部执行方回传资料核实**（fork-only）：6 份答案的验收过程（49/55 行对账、错位实锤、4 个 sha256 复算一致）、8 条被推翻/修正的说法（SXB 是 5–2500 MHz、U279/280 是 D 触发器不是 ÷2、实购 CB3Q 非 CBTLV、ST 勘误 §2.2.1 ADC 触发丢失…）、HMC1023/AD8302/Si5338/总线开关的手册级补口、"信息不足"大头其实是我们包缺 `Value`、以及按谁能推动分四组的待办队列 | 要用这批外部结论之前，先读它的证据分级 |
| `SOP-eda-import-2.6.1.md` | **EDA 导入 SOP**：7 步，含"直接导入只得 10/12，不是回归"与两处必须人工的步骤 | 下次往嘉立创EDA导板的人 |
| `PSDR-bringup-checklist.md` | **上电前检查表**（M3）：42 个测点带坐标与网络、射频只写观测方法、无实物逐条 SKIP | 板子到手那天 |
| `psdr-build-notes.md` | 构建笔记（F4 线的工具链与坑） | 要复现编译的人 |
| `PSDR-TAKEOVER-WORKORDER-2026-10-30.md`<br>`PSDR-TAKEOVER-PROMPT-2026-10-30.md`<br>`PSDR-TAKEOVER-EVALUATION-2026-10-30.md` | **上游给的工单/提示词与当时的评估**（历史输入，不是我们的产出；评估里个别结论已被后续实测更正，正文有标注） | 想知道起点是什么 |
| `psdr-handoff/` | 交接材料里的脚本（`anchor_check.py`、`Makefile.linux`、`PATCH-NOTES.md`），F4 锚点自证用 | 核对 F4 构建 |
| `../evidence/` | **不可重跑的现场读数**（EDA 12/12 与 DRC 513 的构成等）与其 README | 想核对"当时到底读到什么" |

## 相关但不在 `docs/`

- `dist/kicad/SHA256SUMS` + `tools/reproduce_kicad.py`：一条命令重建参考板、DRC 与制造包并自检。
- `dist/reference/`：**F7 构建的锚点参考 hex**（两份基线各一，带 sha256/blob/出处）与复算命令；
  放这里是因为 `Source_F7/.gitignore` 的 `/Debug` 会把它们挡在版本控制外（2026-11-03 改基时差点丢）。
- `Hardware/BOMs/PSDR_2.6.1/PSDR2.6_BOM_flat.csv` / `PSDR2.6.1_BOM_flat.csv` /
  `BOM_refdes_crosscheck.csv`：**派生件，不是源**。`.xls` 仍然是 BOM 的权威版本；两份扁平 CSV
  由 office-excel 展平（文件头写源 BIFF 版本哈希），交叉表由
  `python tools/bom_refdes_crosscheck.py` 重算。注意展平用的是**带 PR #18 修正后**的 .xls，
  要看上游未修版得从 `45acd0f5` 取。
- `dist/fab/PSDR_2.6.1_placement.csv`：SMT 贴装表（391 件），与 BOM 和 KiCad 锚点双向对账过。
- `tools/`：解析器、KiCad 生成器、Gerber 对拍、层覆盖率、固件统计（`fw_stats.py` / `fw_funcindex.py`）。
- `delegation/` + `tools/make_delegation_pack.py`：**派给外部执行方的自包含输入包**
  （36 只 IC 的引脚/网络上下文、23 个封装的原始 `*PARTDECAL*` 块、件数普查、带 DigiKey 号的 BOM 行），
  含答案 schema 与"无出处不作答"的硬规则；重跑一条命令，位号错配由 `EXPECT` 守卫挡住。
  `delegation/answers/` 是**对方交回的原件收档**（6 份，只加了 PROVENANCE 头，正文一字未改）：
  属外部断言，未逐条复核的数字不得直接进对外文本；`MANIFEST.csv` 只覆盖输入包。
  同目录还有下一轮的**可粘贴提示词**：`PROMPT-recheck-taskC.md`（TASK_C 剩余 32 行，带附件哈希与
  "CONTESTED 两值都算"的硬规则）、`PROMPT-uhsdr-frontend.md`（UHSDR/OVI40 前端，
  只收 文件+commit+行号 级出处，并禁止替 PSDR 下结论）。
