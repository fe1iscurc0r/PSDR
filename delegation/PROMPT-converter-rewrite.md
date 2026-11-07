# 任务：KiCad→eprj3 转换器——探明客户端加载卡死、源码修 bug、重写架构（可选回推 PR）

配套 `PROMPT-executor-brief.md`（怎么干活）使用；本文件只管**做什么**。
委托方是 PortableSDR（PSDR）项目的第三方接手者。优先级：**P0 探明问题 > P1 修两 bug > P2 重写架构 > P3 备 PR**。
P0 没拿出可核证据之前，不要急着大改架构。

---

## 0. 背景（自包含，执行方没有本会话上下文）

有一个官方开源转换器，把 KiCad 工程转成嘉立创EDA专业版（EasyEDA Pro / JLC EDA）的原生
`eprj3` 文件夹工程。我们用它转了一块真实的 4 层射频板（PSDR rev-B，391 个器件），
转换产物**离线看起来全对**（板框、277 网、12 块铺铜都修复并回读核验过），
但**嘉立创EDA桌面客户端 V4.1.60 打开这块板会加载极久——委托方报告跑了一天都没打开**，
看不出它在干什么。委托方要求：拉下工具、**探明客户端为什么卡死**、把架构重写干净，
运气好往上游回推 PR。

已知的硬事实（都是委托方离线实测，强度=原件/算得，执行方可复算但不要推翻前提除非有反证）：

- 转换器仓库：`easyeda/kicad-to-easyeda-eprj3`，commit `a16545dd7922455e6a20f69adeb234c924af08b5`
  （2026-09-10）。Node.js ≥ 18，**零 npm 依赖**。
- 用法：`node scripts/convert-kicad.js convert <KiCad工程目录> <输出目录> [--project-name <名称>]`
- 源码结构：`scripts/convert-kicad.js`（1396 行，工程转换入口，PCB/原理图逻辑都在这）；
  `scripts/lib/{kicad.js S-expression解析器, kicad-to-eprj3.js 符号/封装→记录, eprj3.js 读写核心,
  elibz2.js 库包, zip.js 零依赖zip, utils.js}`；`test/smoke.js`（68 项端到端断言）、
  `test/validate-format.js`（用官方 JSON Schemas 逐条校验，依赖 `easyeda-pro-format-skill` 的
  `validate.js`，默认同级目录查找，可用环境变量 `EASYEDA_FORMAT_SKILL` 指路径）。
- 输出形态：文件夹工程 `<名称>.eprj3`（JSON 索引）+ `sch/*.esch2` + `pcb/PCB1.epcb2`。
  `.epcb2`/`.esch2` 是**记录流文本**，每行 `HEAD||BODY|`，可离线逐行解析/改写。
  我们这块板的 `PCB1.epcb2` 是自包含的（57 个 FOOTPRINT + 57 个 DEVICE doc head 都在内）。
- **加载瓶颈在客户端，不在文件解析**：Node `JSON.parse` 全部约 11,800 条记录只要 **13–23 ms**，
  客户端却要一天量级 ⇒ 卡在客户端对象构建/渲染/实时 DRC，不是读文件。
  **压缩文件、舍入坐标救不了**：坐标舍入到 0.01 mil 只省 13.1% 体积，几何变化 0.0000 mil，已试过无效。
- 交付件离线计数（委托方口径，执行方解析后要对账，不一致要报告而不是默默改）：
  **391 COMPONENT / 277 NET / 1132 PAD_NET**（其中 145 个 PADS 自动网名 `$$$NNNNN` 在 EDA 显示为
  `##NNNNN`，**不是乱码**）/ **12 POUR**（全部有网）/ **1 BOARD_OUTLINE**（闭合 1212 点，
  包围盒 99.9998 × 64.9986 mm）/ **6578 LINE / 419 VIA**。
  注意 README 把 PCB `segment`/`arc` 走线映射成 **FILL**（闭合细多边形），与上面的 LINE 计数口径
  可能不同——执行方要 reconcile「LINE vs FILL」并报告各自计数，别假设。

格式权威与参考工程（都在 GitHub `easyeda` 组织下，见 §2 白名单）：
- `easyeda/easyeda-pro-format-skill` — types 索引、图元字段定义、JSON Schemas、`validate.js`（格式权威）
- `easyeda/easyeda-eprj3-skill` — 从零生成 `.eprj3` 的技能包（本仓 `eprj3.js`/`utils.js` 的来源）
- `easyeda/easyeda-pro-eprj3-format` — 官方 eprj3 格式示例工程（拿它当"正常能加载"的结构对照）

上游已有 issue（执行方**只读**，不去评论）：
- `easyeda/kicad-to-easyeda-eprj3#2`（委托方 2026-11-07 提报，含下面两个 bug 与全部数字）
- `easyeda/kicad-to-easyeda-eprj3#1`（维护者曾要求给具体复现）

---

## 1. 附件清单（先取齐再动手；未附的条目显式跳过并登记）

| # | 附件 | sha256 / 字节 | 用途 | 没有它怎么办 |
|---|---|---|---|---|
| A1 | `PSDR_2.6.1_revB.kicad_pcb` | `aa24bda9e32124628c1ded471715690b13eb1f08cdd5be9975ffca306af8ac60` | 转换输入，复现转换 | 无 A1 则 P1/P2 的"重跑转换"跳过，只能审计 A2 |
| A2 | `PCB1.epcb2`（交付件，**卡死客户端的那份**） | 3,644,007 B；`e4e246e945f9fc761423ab0a7b14c568d191117fab4dad904233aea82ed22303` | P0 离线几何审计的主对象 | **无 A2 则 P0 无法做**，停下向委托方要 |
| A3 | `SOP-kicad-to-eprj3.md` | 见仓内 `docs/` | 背景与已修 bug 的细节 | 可选；本文件已含核心事实 |
| A4 | `Hardware/PSDR.asc` | 见仓内 | bug2 铺铜 bbox 匹配的参考 | 无 A4 则 bug2 的"按源板匹配"复算跳过 |
| A5 | 原始未修复转换输出 `PSDR_revB/`（文件夹） | — | 对照两 bug 修复前后 | 可选 |
| A6 | `watch_eda.ps1` + 现场读数 | — | 客户端"在干活还是死了"的判活证据 | 可选；P0 的客户端侧现象以委托方实测为准 |

取料渠道：委托方会上传到 IMA 知识库 `psdr` 文件夹，或直接贴仓内文件。
**逐份核对字节数与 sha256 前缀**，对不上就停下报告。抽取版（知识库转码）哈希必然不符——
不要对抽取版做字节级自证，做**结构级举证**（记录条数、首行、计数对账）即可，并登记哈希不符这件事。

---

## 2. 网络白名单（本任务允许联网，但只限以下）

只允许访问 GitHub 克隆/读取这四个仓库（及其 CDN `codeload.github.com`、`raw.githubusercontent.com`、
`objects.githubusercontent.com`）：
`easyeda/kicad-to-easyeda-eprj3`、`easyeda/easyeda-pro-format-skill`、
`easyeda/easyeda-eprj3-skill`、`easyeda/easyeda-pro-eprj3-format`。
**其余全网禁**：不许用搜索引擎摘要、商城页、论坛、你自己的记忆替代附件或源码。
克隆失败写清 HTTP 状态码与客户端；403/429 只能写"我方出口被拒/被限流"，不许写"仓库不存在/已撤档"。

---

## 3. 任务分段（每段都要可判定验收 + 自检输出）

### P0 探明客户端加载卡死（最高优先，先交这个）

目标：给出**卡死的可核原因或排序假设**，而不是"客户端慢"这种话。两条腿走：

1. **离线几何审计**（不依赖客户端，能独立出结论）：解析 A2，逐记录类型统计并找病理性几何：
   - 每类记录的**顶点总数/最大单条顶点数**（重点：`POURED`/`POUR` 的 `pourFill`、`FILL` 走线多边形、
     1212 点的 `BOARD_OUTLINE`）；有没有**几十万顶点的单条多边形**；
   - **自相交/退化多边形**（零长边、重复点、面积为 0、绕数异常）——客户端铺铜/填充算法可能在这种输入上死循环；
   - 圆弧派生的 `FILL`/`ARC` 段：扫角/圆心字段是否合法（联系 bug1）；
   - 坐标**量级与精度**（mil 值是否异常大、小数位是否爆炸）、**重复 ID**、`HEAD||BODY|` 结构是否合法；
   - 用 `test/validate-format.js`（配 `easyeda-pro-format-skill`）逐条校验，列出**所有 schema 偏差**；
   - 与官方示例工程 `easyeda-pro-eprj3-format` 的同类记录**结构对照**，找我们多出来/写错的字段。
2. **剥离二分变体**（客户端加载由委托方做，执行方产变体）：从 A2 离线生成逐级变体，每级只加一类图元：
   - V1 仅器件（COMPONENT+FOOTPRINT+DEVICE+PAD/PAD_NET+NET）；
   - V2 = V1 + BOARD_OUTLINE；V3 = V2 + POUR/POURED；V4 = V3 + 走线(LINE/FILL)+VIA（=全板）。
   - 每个变体附离线计数与 sha256。**委托方在客户端逐个打开、计时、报告哪级秒开哪级卡死**，
     执行方据此定位是哪类图元触发卡死。变体加载结果强度=**委托方实测**，执行方不许自己写成"已验证能加载"。

交付：`DIAGNOSIS.md`（审计读数 + 排序假设表，每条标 读得/算得/待测 + 证据位置）+ 变体文件 + 计数清单。
**验收**：假设表里每条都有可核证据或显式标"待测"；若离线找到确定性病理（如某条多边形自相交/百万顶点），
明确指出记录 ID 与复算方法；找不到确定性原因就如实写"离线未定位，需变体加载反馈"，不许糊。

### P1 源码级修两个已知 bug（附回归）

两个 bug 的权威锚点（commit a16545d，`scripts/convert-kicad.js`，执行方克隆后核对行号）：

- **Bug1 板框圆弧**：`arcOutlinePath` @1037–1043，emit @1042：
  `return [x1, y1, 'ARC', r2(sweep), x2, y2, x1, y1];`
  把**扫角**放在 `ARC` 后，宿主把前两个数当**圆心**读 ⇒ 小圆角渲染成大圆；板框还被拆成 50 条
  `BOARD_OUTLINE` 碎片。自带 example 有 **0 个 `gr_arc`**，此路径上游没测过。
  委托方离线修法：25 条 `gr_arc` 按 2° 折线化 + 42 条 `gr_line` 缝成一条闭合 1212 点 POLY，
  包围盒 99.9998×64.9986 mm 与源一致，最大 sag 0.0007 mm。执行方在源码里实现等价修复，
  **并补一个含 `gr_arc` 的回归 fixture**（example 现在测不到这条路径）。
- **Bug2 铺铜丢网**：`netNames` 表 @775–779 只按**数字网号**建键
  （`/^\d+$/.test(node[1].v)`，`netNames[node[1].v] = name`）；`normNet` @1020
  `return netArr ? (netNames[netArr[0]] || '') : '';`；`convertZone` @1177
  `const netName = normNet((netNameArr && netNameArr[0]) || (netArr ? (netNames[netArr[0]] || '') : ''));`。
  我们的 zone 写的是名字串 `(net "GND")`（无数字网号、无 `net_name`）⇒ `netNames["GND"]` undefined
  ⇒ `netName:""` ⇒ 12 块 POUR 全 `name:"POUR1"`、`keepIsland:false`（@1189）= **浮铜**。
  走线用数字网号所以没事，极具迷惑性。修法：网号表同时按数字与名字建键，或 zone 网名直接按字符串解析；
  修后 12/12 POUR `netName` 非空且与源板一致（委托方离线按 bbox 匹配 `Hardware/PSDR.asc` 12 个 POUROUT，
  误差 0.000 mil 可作对照）。

**验收**：`npm test`（68 断言）全过 + 新增 fixture 断言过 + `validate-format.js` 对修复后产物无新增偏差；
重跑 A1 转换，POUR.netName 12/12 非空、板框单条闭合、包围盒与源板差 ≤ 0.001 mm。自檢脚本失败必须非零退出。

### P2 重写架构（委托方点名；先提案后动手）

目标：把转换器重写到**可维护、产物正确且客户端能快速加载**。边界：
- **先在 S2 给架构提案**（模块划分、记录流读写、几何管线、测试策略、与现有 lib 的关系），
  列清改动范围与风险，**等委托方拍板再大改**；委托方说"直接干"才继续。
- **先交最小可用版**：能跑通、能自检、结构完整、P0/P1 成果保留，再谈增强。
- 重写要**针对 P0 诊断出的卡死根因**（例如几何简化/顶点数控制/正确记录结构），不是无目的重构。
- 不丢现有覆盖范围（README 的 KiCad→eprj3 映射表是契约）；不迁移项（3D/网络类/SPICE/自定义规则）照旧跳过并告警。
- 几何简化若有损，给**容差口径**（如板框 sag ≤ 0.001 mm）并回读对账，不许悄悄降精度。

**验收**：架构提案文档 + 最小可用实现 + `npm test`/`validate-format` 通过 + 重跑 A1 的产物计数对账 +
（若委托方跑了变体加载）加载时间对比读数。没有客户端读数就不许写"加载变快/已修复"。

### P3 回推 PR 准备（可选，委托方逐次批准；执行方只备不发）

- 产出 **PR-ready diff**（相对 a16545d）+ **ASCII 英文 PR 描述草稿**（含复现步骤、修复前后计数、
  回归 fixture、关联 issue #2/#1）+ 证据清单。
- **执行方不 push、不开 PR、不评论 issue、不联系维护者**（brief 禁区）。是否推、推到哪（是否先 fork
  `easyeda/kicad-to-easyeda-eprj3`）、何时推，全由委托方逐次决定。
- 描述里披露 AI 辅助、第三方身份；不写没有实测支撑的效果话。

---

## 4. 证据与自检口径（照 brief，再加这条任务的硬要求）

- 三态分开：**读得**（附件/源码逐行，给 file:line）/ **算得**（公式+代入+结果+单位）/ **待测**（没做的，不许写成读数）。
- 客户端加载时间是**委托方实测**，执行方引用时标来源；执行方自己没有客户端，不许凭空写加载读数。
- 自检脚本随交付、可重跑；**断言失败必须非零退出**，不许把失败打印成成功。
- 做一次**反向注入测试**：故意往产物里注入一处违规（如空 netName 的 POUR、自相交多边形、坏 HEAD），
  证明你的审计/校验脚本真的会 FAIL并非零退出——证明自检不是摆设。
- **失败必须登记为失败**并附替代证据；跳过必须写为什么跳过。不许"基本可用""整体良好"。

## 5. 交付物清单

1. `DIAGNOSIS.md`（P0：审计读数 + 排序假设表 + 变体加载反馈位）
2. 剥离变体 V1–V4（`.epcb2`）+ 各自计数与 sha256
3. 源码补丁（P1 两 bug + 回归 fixture）+ `npm test`/`validate-format` 输出
4. 架构提案 + 最小可用实现（P2，若委托方批准）
5. PR-ready diff + ASCII 描述草稿 + 证据清单（P3，只备不发）
6. `SELFTEST.md`（自查了什么、通过/失败/跳过、反向注入结果）
7. 需委托方拍板的问题编号表（见 §6）

## 6. 需委托方拍板的问题（一次问清，含你的默认假设）

1. P2 重写范围/边界？（默认：保留现有覆盖契约，只针对 P0 根因 + 可维护性，先最小可用）
2. PR 目标与是否先 fork `easyeda/kicad-to-easyeda-eprj3`？（默认：执行方只备 diff，不 push）
3. 变体加载由谁跑、计时口径？（默认：委托方在 V4.1.60 桌面客户端逐个打开 V1–V4，记录"秒开/卡死/耗时"）
4. 附件上传渠道与是否补齐 A4/A5/A6？（默认：IMA `psdr` 文件夹；A2 必传）
5. 几何简化可接受容差？（默认：板框 sag ≤ 0.001 mm，铺铜 clearance 不变）

## 7. 禁区重申（违反一条即不合格）

- 不对外：不 push / 不开 PR / 不评论 issue / 不联系任何人。
- 不改委托方的 PSDR 仓库与 git 历史；只在执行方自己克隆的 easyeda 仓库副本上工作。
- 不写没有实测支撑的"已修复/性能更好/可用"。
- 抓取失败 ≠ 资源消失（写状态码，不许写"官方撤档"）。
- 替代件/国产化/降本内容与本任务无关，不得夹带进任何对外草稿。