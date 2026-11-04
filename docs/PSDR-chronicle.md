# PSDR 编年史：从 2014 年的原初设计到 2026 年 11 月的这次接手

日期：2026-11-04。本文是"史"，不是待办也不是结论汇总：**每一条都能回指到一个 commit sha、
一个 issue/评论 id、一个文件路径或一个单元格地址**；写不出处的句子直接不写。
要干活看 `docs/WO-psdr-takeover.md`（施工总账，按 §号查）与 `docs/README.md`（文档地图）。

引用约定：
* `next` = 本 fork 主线；`上游` = `MichaelRColton/PSDR`；提交号一律给 7 位短 sha。
* "算得 / 量得 / 读得"三种口径不许混：算得=公式推的，量得=仪器测的（本史里**一条都没有**，
  因为至今没有板子在手），读得=从原件或表格里逐格读出的。
* 引用总账一律用 §号（追加记录会让行号漂移）。

---

## 第一纪 · 上游原史（2014-07 → 2025-10）

全部时间戳来自 GitHub 的 issue/PR 列表与 `git log`，不是回忆。

| 日期 | 事件 | 出处 |
|---|---|---|
| 2014-07-15 | #1「Create Assembly Drawing for PSDR1」、#2「Create PSDR1 Assembly Notes」开——**这两条到 2017-01-07 才关** | issue #1/#2 |
| 2014-09-25 | PR #3（@johnlaur）"Updated pin definitions and initializations"，9-29 关 | PR #3 |
| 2015-02-18 | PR #4（@pwarren）"Firmware Build Notes"，拖到 2016-01-03 才关 | PR #4 |
| 2016-04-18 | `1890b25` "PSDR 2.5 prototypes are assembled… Display comes on, lots of the parts are working, **but no frequency synth yet**" | `git log -1 1890b25` |
| 2016-07-31 | `468dc41` "PSDR 2.6.1 PCB complete. Updates to BOM in preparation for order." 同一提交还加了"不接调试器就不打印"的开关（作者注 "otherwise the board wont run without a debugger attached"） | `git log -1 468dc41` |
| 2016-12-31 | PR #5（@pwarren）"Volume works, compiler warnings, newlib compilation"，2017-01-19 关 | PR #5 |
| 2017-01-06 | 同一人连开 **#6 S 表在 USB 底部被钉住 / #7 许可与贡献 / #8 状态持久化 / #9 "Proper Off menu item"** | issue #6–#9 |
| 2017-01-11 / 01-23 | #10 Linux 安装说明、#11「PNG 转 C 数组用的什么工具」——都很快关 | #10/#11 |
| 2017-01-07 | #1/#2 关闭（距开 2.5 年） | #1/#2 `closed_at` |
| 2018-03-30 / 04-03 / **06-21** | F7 线的三次改动，06-21 那次留下我们用来对账的 hex（`dist/reference/` 里有参考 hex 与 sha256） | `git log --date=short` |
| 2018-07-31 | `ab2c8fd` **"Not sure what the difference is. Maybe nothing. Is there a good way to compare the contents of two Excel files?"** —— 作者本人在两份 BOM 前卡住的那句原话 | `git log -1 ab2c8fd` |
| 2019-05-24 | `TestingMakeFile*/` 那棵 CubeMX + FreeRTOS 重建树（F746 Makefile 在内），从未合回主线 | 任务章 §见 `PSDR-author-measurement-log.md` |
| 2021-01-18 | PR #12（@jeffersonbenson）加 Contributing/License、整理 `Hardware/`，1-27 关 | PR #12 |
| 2021-01-30 | **#13「Obsolete parts in 2.6.1 BOM」、#14「Missing parts in 2.6.1 BOM」**——至今 OPEN，是 PR #18 的直接对象 | #13/#14 |
| 2021-02-01 | PR #15 "Reorganization changes from PSDR_Rebuild"，3-05 关 ⇒ **上游最后一次合并就是它** | PR #15 |
| 2021-02-06 | **#16「Enable Pre-Amp in Firmware」**开（@jeffersonbenson） | #16 |
| 2021-12-06 | @DM2NT："I also have a PSDR here. But like all the others, **it's just a paperweight.**" maintainer 当天回："**Jeff is correct, the preamp/low-pass filter circuit isn't working. I had it working on development hardware, but my efforts to get it to operate properly on the production board didn't reach completion**" | #16 评论 |
| 2021-12-07 | maintainer 展开："There are RF switches that need to be configured, and **the pre-amp/low-pass filter IC has a lot of configuration registers** and things that have to be set correctly" ⇒ 这就是我们后来定位的 MASWSS0129 三片 + HMC1023 | #16 评论（2,785 字符） |
| 2021-12-09 | @DM2NT 点名 uSDX 并递来 UHSDR："**Andreas DF8OE has already implemented the HMC1023 in his UHSDR.** Here is the link"（给的是 `tree/active-devel/mchf-eclipse/…` **目录**级链接）；@petermccracken 递 mcHF 群与 Malahit；maintainer 自评 uSDX "the microcontroller is very underpowered"、说想 "merging the PSDR and the uSDX"，并提到 **KA7OEI 愿意看 PSDR 但一直没看成** | #16 评论 |
| 2022-07-04 | @sanamon 指路 wiki 的 Linux 构建说明（回应"我没有 Windows"） | #16 评论 |
| 2025-10-28 | DM2NT 回访问发过多少台；maintainer 答 **"about 100 units"**（并说有人没寄地址、两台退回） | #16 评论 |
| 2025-10-30 | DM2NT：**"Unfortunately, the MASWSS0129 parts are no longer available here."** ⇒ 我们 2026-11 测到的 `cdn.macom.com/…/MASWSS0129.pdf` 404 与此独立吻合 | #16 评论 |
| 2026-09-11 | **#7 关闭**，maintainer 确认 MIT 为正式许可（"The MIT license is official — fully open"）⇒ 本 fork 的合法性锚点 | #7 `closed_at` + §本账 I 章 |

**这一纪的读法**：#16 的三条关键事实（作者承认前放/LPF 在量产板上没跑起来、HMC1023 有"一堆寄存器"、
UHSDR 已实现该器件）在 2021 年就齐了；此后四年没人再碰。我们 2026-11 的全部对外动作都在补这段空档，
而不是在推翻它。

---

## 第二纪 · 接手七天（2026-10-30 → 11-04）

`git log --author=fe1iscurc0r next` 在动笔时（HEAD `6f4bec4`）共 **72 个提交**，本史落档那一串提交
（`0b3394e`/`d18961d` 与之后的索引改动）也记在这七天里，所以按天表读完后现算会得到更大的数——
**这个数本文不追，要用的话现跑** `git log --format=%h --author=fe1iscurc0r next | wc -l`。
下表按天，动笔时的分布（另有 Jeff Benson 1 个）：

| 日期 | 提交 | 干了什么（只列锚点，细节看总账对应章） |
|---|---|---|
| 10-30 | 5 | 开工：工单 + 评估报告 + 已验证构建脚本（`479ee18`）、新仓开工提示词（`9f07464`）；补 5 处构建缺陷使固件能在 `arm-none-eabi-gcc` 上构建（`96e06ce`）；宿主环境定案 WSL2 + 换行符 + Kali PEP668 三坑（任务 A/B 章） |
| 10-31 | 10 | 任务 B 构建通过并实测尺寸；**从 `Hardware/PSDR.asc` 提取 2.6.1 网表并四重校验**（`199d552`，391 parts / 278 nets / 1,132 pins，今日复算仍一致）；生成 KiCad 原理图、**278 网与 PADS 逐集合一致**（`59ea7f4`）；由 PADS ASCII 重建 KiCad 板并归一 Gerber（`8d410f9`）；BOM 逐位号对账（`ef45f6d`）；**PR #17 开出**（13:13:09Z）与同日在 #14 补四件 DNP 的网表证据（13:19:34Z，3h39m 后收到 "Please do!"）；顺手永久修正了本机坏掉的凭据助手配置（`61f1e20`） |
| 11-01 | 14 | **M0 立 `next` 为独立主线** + `fork-base/2026-10-30` tag（`a524e06`）；四层板补齐铺铜/真实板框/丝印，**0 断点**（`03e22f7`）；J170 第 4 个安装孔 + **795 条 DRC 逐类定性**（`1d8e9ca`）；一条命令复现链 + SHA256 清单（`a627c35`）；`Makefile.linux` 让 F7 线可复现构建（`9de9b93`）；**PR #18 开出**（2026-11-01 12:46:28Z；同日 `c858167` 记的是第三批推送与 PR #17 的评论） |
| 11-02 | 26 | 产量最大的一天：**PR #18**（BOM 位号修正，`R97,-99`/`R6,14,268`）与**上游 #19**（两处可能挡住开机固件点，只征求意见不附 PR）开出；任务 G 把 #6–#16 逐条处置；A-1 制造包逐层核对 + **锡膏母片实测**（§C-20）；A-2 SMT 贴装坐标表与 BOM/锚点双向对账；A-3 八层双向覆盖率（§C-21）；B-1 上电前检查表落地；§C-22 收口"源铺铜规则 12 mil vs EDA 实际 10 mil"；474 个上游构建产物移出版本控制（#32）；F 道规划定稿（下面单列） |
| 11-03 | 12 | 任务 H 需求边界修订；**任务 I：维护者回归的两条实权回复逐条复核**；**改基**——`next` 的固件树镜像 `upstream/PSDR_F7`（`ab2c8fd`），`.c/.h` 零改动；任务 J 委派输入包（36 份 IC 上下文 + 23 个封装原始块）；**#20 开出，#21 是同一内容的重复帖、当天自己关掉**；#16 首帖（3,361 字符）与同日两条更正（1,619 / 3,802）；7 份原厂 PDF 我方独立复算、sha256 与对方一致 |
| 11-04 | 5 | 任务 K 整合复测（把改基后失效的数字全部归位）；#18 回帖（2,823）；#16 第三条自我更正（2,353）；**`next` 推 `84f3790`、三处 `master` 快进到 `c34afebe`** |

### F 道规划（11-02 定）与实际兑现

总账 §F 当时按"不需要硬件就能验证"排了三道，今天回看：

* **A 道（可制造基线里不需硬件的那半）**：三条**全部做完** —— 制造包逐层核对（含此前没核过的锡膏与
  fabnotes）、贴装坐标表、制造包 vs 复现 `dist/kicad/fab` 全层比对。验收口径照当时写的执行：
  每条给命中/未命中计数与残差位置，不许用综合分代替。
* **B 道（M3 硬件）**：只做完了"插上就能跑的准备"——`docs/PSDR-bringup-checklist.md`；
  真板没到位 ⇒ 所有测量项按当时的规矩**如实记 SKIP**，一条没假完成。
* **C 道（对外）**：当时写的是"**不催、不重开新 issue**（边界）；#14 只在有实质新证据时补一条"。
  实际情况是 11-01 的 #18 与 11-02/11-03 的 #19/#20 都是在窗口开之后才发的——
  2026-10-31（周六）13:19:34Z 我方在 #14 补完那四件 DNP 的网表证据，**3 小时 39 分后**
  jeffersonbenson 回 "Please do!"（16:58:37Z），于是 11-01（周日）才把 PR #18 提上去。
  **这是本史里唯一一次"计划被外部条件改掉"，改动的批准都在总账 G/I/K 章逐条可查。**

---

## 第三纪 · 对外件史（截至 2026-11-04）

### 上游全部 issue / PR（21 条，实时从 REST 拉）

| # | 类型 | 状态 | 开 | 关 | 作者 | 标题（截断） |
|---|---|---|---|---|---|---|
| 1 | IS | closed | 2014-07-15 | 2017-01-07 | MichaelRColton | Create Assembly Drawing for PSDR1 |
| 2 | IS | closed | 2014-07-15 | 2017-01-07 | MichaelRColton | Create PSDR1 Assembly Notes |
| 3 | PR | closed | 2014-09-25 | 2014-09-29 | johnlaur | Updated pin definitions and initializations |
| 4 | PR | closed | 2015-02-18 | 2016-01-03 | pwarren | Firmware Build Notes |
| 5 | PR | closed | 2016-12-31 | 2017-01-19 | pwarren | Volume works, compiler warnings, newlib compilation |
| 6 | IS | **open** | 2017-01-06 | — | pwarren | S meter pinned on USB with filter bottom at 0 |
| 7 | IS | closed | 2017-01-06 | **2026-09-11** | pwarren | Project organisation: Licensing, Contributions etc |
| 8 | IS | **open** | 2017-01-06 | — | pwarren | Persistent state storage |
| 9 | IS | **open** | 2017-01-06 | — | pwarren | Proper Off menu item and 'Turn On' gesture |
| 10 | IS | closed | 2017-01-11 | 2017-01-12 | sanamon | Linux setup instructions |
| 11 | IS | closed | 2017-01-23 | 2017-01-25 | sanamon | Which tool was used to create the C arrays from the png images? |
| 12 | PR | closed | 2021-01-18 | 2021-01-27 | jeffersonbenson | Added Contributing and License, reorganized Hardware |
| 13 | IS | **open** | 2021-01-30 | — | jeffersonbenson | Obsolete parts in 2.6.1 BOM |
| 14 | IS | **open** | 2021-01-30 | — | jeffersonbenson | Missing parts in 2.6.1. BOM |
| 15 | PR | closed | 2021-02-01 | 2021-03-05 | jeffersonbenson | Reorganization changes from PSDR_Rebuild |
| 16 | IS | **open** | 2021-02-06 | — | jeffersonbenson | Enable Pre-Amp in Firmware |
| **17** | PR | **merged** | **2026-10-31** | **2026-11-03** | **fe1iscurc0r** | Add a KiCad schematic for PSDR 2.6.1 generated from the PADS netlist |
| **18** | PR | **open** | **2026-11-01** | — | **fe1iscurc0r** | Fix BOM Ref Des typos (R98, R6/R14), record the four DNP parts (#14) and … |
| **19** | IS | **open** | **2026-11-02** | — | **fe1iscurc0r** | Two firmware spots that may stop a board from booting (F7 main loop, Si5338 I2C) |
| **20** | IS | **open** | **2026-11-03** | — | **fe1iscurc0r** | Are the VNA and filtered signal paths implemented anywhere? `signalPath()` has f… |
| **21** | IS | closed | **2026-11-03** | **2026-11-03** | **fe1iscurc0r** | 与 #20 同文的重复帖，**由我们自己关闭**（`closed_by = fe1iscurc0r`，0 评论） |

一句话统计：**上游 21 条里，2026-09 之后还有动静的共 8 条**（`updated_at` 实测）——
#7、#14、#16、#17、#18、#19、#20、#21；其中 #17–#21 是我们开的，#7/#14/#16 是我们把动静带上去的。
上游最后一次"别人"的合并停在 2021-03-05 的 #15。

### 我们自己的对外动作（逐条给 id 与字节数，全部"只发一次"有前后计数取证）

| 日期 | 位置 | 动作 | 评论 id / 大小 |
|---|---|---|---|
| 2026-10-31 → 11-03 | PR #17 | 提交并**已合并**为上游 `master` 的 `c34afebe` | 3 提交 / 23 文件 |
| 2026-11-01 → | PR #18 | BOM 位号与 DNP 说明，**仍 OPEN**；head `cb6dda0`（4 提交 / 4 文件） | 13 个单元格，逐格清单在 PR 分支的 `Hardware/BOMs/PSDR_2.6.1/BOM_changes_PR18.md` |
| 2026-11-02 | issue #19 | 两处固件开机阻断点，只征求意见、不附 PR | — |
| 2026-11-03 | issue #20（+ #21 重复自关） | VNA / 滤波路径是否实现过 | — |
| 2026-11-03T01:20Z | #16 | 首帖：三片 DPDT + HMC1023 零引用 + 灵敏度线索 | `6592865486`，3,361 字符 |
| 2026-11-03T05:05Z | #16 | 路径更正（我们的 `Source_F7/` 在上游不存在） | `6595930419`，1,619 字符 |
| 2026-11-03T14:35Z | #16 | **两条公开更正** + 一个建议实测的轨压 | `6606601865`，3,802 字符（15 条计数取证） |
| 2026-11-04 | PR #18 | 回答 reviewer 的"是建议还是解决方案"：**是修，刻意不给替代件** | `6622367887`，2,823 字符（1→2 取证） |
| 2026-11-04 | #16 | 第三条自我更正：R6/R14 是**表内自相矛盾**，不是版本 delta | `6623233867`，2,353 字符（15→16 取证） |

边界（一直生效）：不合并别人的东西、不替 maintainer 关 issue、不催、**新开 issue 逐次批准**、
国产化/替代件提案只留 fork 不进上游、固件源码一行不改（注释也只写在 docs 里）。

---

## 第四纪 · 我们撤过的话（这节才是这份史最有用的部分）

接手七天里我们自己推翻了 11 条先前写下的断言。每条都给"旧说法 → 什么证据推翻 → 现在口径"。

| # | 旧断言（曾写进文档/对外） | 被什么推翻 | 现在口径 | 出处 |
|---|---|---|---|---|
| 1 | "任务 C 是 **Eagle** 转换" | 转换源实际是 PADS Layout ASCII（`Hardware/PSDR.asc`），Eagle 只在更早的交接描述里出现 | 标题保留但正文注明"转换源不是 Eagle，见 C-1" | 总账任务 C |
| 2 | 菜单"**18 个分支**" | 两棵基线树都是 **12** 个 `case`；18 这个数与任何一棵树都对不上 | 12；并把"与改基无关的老错"单独列框 | `PSDR-firmware-survey.md` §0.1/§262 更正框 |
| 3 | "`frequency_control.c:41` 的 I2C Timing 常量在改基后**消失了**" | 该文件是 `PSDR_Rebuild` 才拆出来的，`PSDR_F7` 里没有；常量本身还在 `main.c:1018`（`0x40912732`），旧镜像行号也是 `:40` 不是 `:41` | 位置写 `main.c:1018`，并给"旧路径→现基线"换算锚点表 | `PSDR-open-data-gaps.md` #2、总账 §K-7 |
| 4 | "**2.6→2.6.1 实质差异只有 `R164`**"（曾长期写在记忆里） | 逐格读两份**未修** .xls：delta 有**三处**（`R164` 270K→240K、`R6` 100R→180R、`R14` 100R→68R），且 2.6.1 表**第 45 行 `R6,14,268` Qty 已改 1、位号文本没删** ⇒ 同一份表给 R6 两个值、R14 两个值 | 先讲"表内自相矛盾（半次编辑）"，再讲版本 delta；引用行号写"电子表格第 45 行 / `item_no. 41`" | `gaps §2.1`、findings §7.3、总账 §K-11/K-13；对外在 #16 `6623233867` 已撤 |
| 5 | "U304 所在 SBB/SXB-2089 家族 50–850 MHz ⇒ 灵敏度差是因为 HF 本来就没增益" | 板上买的是 **SXB**-2089Z（另一颗）；我们**取不到它的原厂 PDF** | 公开撤回归因；5–2500 MHz 只作"镜像文本，待核"，**不当新结论** | #16 `6606601865` 第 1 条；findings §8.1 |
| 6 | "**Qorvo 已撤档**" | 我方出口直连 `qorvo.com/products/p/SXB-2089Z` 是 **429 限流**（11-04 连测两次），404 来自另一条抓取路径 | 只写"Qorvo 站点检索不到该件、我方出口被限流" | findings §7.3-3、§8.1；对外文案同步降级 |
| 7 | "`+3V3_CPU` 只有 2.90/3.01 V"（读起来像实测） | 它是**算得**的：AP3417C 原厂 `Feedback Voltage: 600mV` + 板上 `R112`=100K 与 `R113`（板文件 383K / BOM 402K） | 措辞钉死为计算值 + 已列进 M3 必量项 | `PSDR-bringup-checklist.md` B 表（"预期"列） |
| 8 | 固件 P0 有两条（含调试 `while(1)` 死循环） | 那条属 `PSDR_Rebuild` 血统；现基线 `PSDR_F7` 只剩一处：`main.c:1031-1032` 的 `while(result != HAL_OK) HAL_I2C_IsDeviceReady(...)` 无超时 | 现基线 **1 条 P0**，另一条标血统 | `README.fork.md`、`PSDR-firmware-survey.md` |
| 9 | 改基后一堆旧数字（10,686 行 / 346,049 / 119 函数 / 844 / 576 …） | 全部重测：项目代码 `Source/` 12,035 行、`Source_F7/` **10,437** 行、函数 **116** 个等 | 旧→新换算表已发布，禁止再引旧数 | 总账 §K-2/K-3 |
| 10 | `BOM_changes_PR18.md` 被当 `next` 的仓内路径引用 | `git ls-files` 在 `next` 查不到；它只在 PR 分支（`.xls`/`.csv` 三个 blob 两侧一致，另核过） | 引用必须带"只在 PR 分支 `upstream-pr/bom-2.6.1-refdes-fix`" | 总账 §K-12/K-13 |
| 11 | 外部执行方在知识库里留下的 59 个散输入文件 | 我们重做了输入包（改为 3 个合并文件 + MANIFEST 重哈希）⇒ 那批输入已过期 | 只按合并文件重委派，散文件不再当输入 | 总账 §J、`delegation/MANIFEST.csv` |

沉淀成规矩的三条（以后照办）：
1. **对外帖发完要回读自己的旧帖**——第 4、5 两条都是"新证据到手后回查旧帖"才发现的，
   旧帖不会自己变对。
2. **数字必须带口径**（算得 / 量得 / 读得 / 镜像文本），否则读者会把计算值当测量值。
3. **跨版本对表格按列名，不按列号**——2.6 的位号值在 K 列、2.6.1 在 I 列，
   按列号写脚本会得到"2.6 少了两列"这种假结论。

---

## 第五纪 · 外部项目线（#16 点名的那些，与我们的调研现状）

### #16 里实际说了什么（原话级，避免转述失真）

* uSDX：DM2NT 提，maintainer 同意"interface is lacking"，自评其 **MCU very underpowered**，
  并抛出"把 PSDR 和 uSDX 合并"的想法（"or may never happen at all"）。
* mcHF：petermccracken 提（FB 群里有人卖改件 + 4" 屏）；maintainer "**a nice project for sure**"，
  并说 **KA7OEI**（大修过 mcHF 的人）住得不远、愿意看 PSDR，但"we haven't really made it happen yet"。
* Malahit：petermccracken 提；maintainer 认为"rather different goals"。
* **UHSDR**：DM2NT 的原话只有一句与器件相关——
  "**Andreas DF8OE has already implemented the HMC1023 in his UHSDR**"，给的是
  `…/tree/active-devel/mchf-eclipse/` **目录级**链接。
  ⚠️ 需要澄清一处容易的记忆漂移：**#16 里没人说过"UHSDR 有非常棒的前端设计"**。
  这句如果以后要在对外场合引用，只能引成"HMC1023 已在 UHSDR 里实现"，
  前端好坏是我们的判断，不是线程里的事实（本纪下面那条才是可核的架构事实）。

### 我们自己核到的 UHSDR 事实（按强度分级）

| 断言 | 强度 | 出处 |
|---|---|---|
| UHSDR 里有 HMC1023 驱动，含手动细校准 | **核过到文件与 commit**：`mchf-eclipse/hardware/uhsdr_hmc1023.c`，commit `c447c2e4`，2018-10-21，提交语 "Finalized the finalized HMC1023 driver :-)"，作者 db4ple，ovi40h7 语境 | 我用 GitHub API 自核，已按文件级写进 #16（线程里 2021 年只给过目录链接） |
| UHSDR 主体是**固件**项目，跑在 mcHF / OVI40 / TRX SDR Eagle 等多块硬件上 | 核过（仓库结构 + 对方调研一致） | `delegation/answers/` 两份调研 |
| Si5338 在 UHSDR 提交里 0 命中 | 对方断言，**我方部分核** | 同上，标 `镜像`级 |
| OVI40 的 RX 架构："**direct sampling… upto 48 kHz. Above 48 kHz the RX works as a QSD**"；TX "**50 W**"、"**dual LDMOSFET design**" | **今日直取官方页面原话**（amateurfunk-sulingen OVI40 description） | 本文档；页面为项目方自述 |

这条对我们真正的意义是：**同一颗 HMC1023 可编程低通，UHSDR/OVI40 用它服务"直接采样为主、
高频段退回 QSD"的接收架构；PSDR 用它服务全程 Tayloe QSD + VNA**。所以 #16 里"寄存器一堆"这句话
不是 PSDR 独有的坑——UHSDR 用一个 commit 就把它填了，这正是我们可以借的东西：
寄存器序列、CALCK 校准时钟的驱动方式（我们的 `PSDR-HMC1023-netlist.md` 已把 U287 的 32 端子、
SPI 四线 PB12–15、校准时钟来自 Si5338、`VDDBG` 无供电这三件事定好位，缺的正是驱动与供电）。

### 调研档案的位置（今日补齐）

两份对方调研（13 项目对比表 + PSDR 2.6.1 对照表）此前**只活在临时目录**，随时会丢；
现已收进 `delegation/answers/`，文件头注明"外部断言、未逐条复核，性能数字不得直接进对外文本"。
里面已经用过的那几条基线（mcHF −126 dBm/300Hz、TRX SDR Eagle −132 dBm、TX-500 −136 dBm / BDR 129 dB、
uSDX 5.8–9.4 W / 76–93%）在 findings §4 有对应的落点与引用面。

---

## 现状快照（2026-11-04 收盘）

| 项 | 值 |
|---|---|
| fork 主线 | `next` = `6f4bec4`（`origin/next` = `84f3790` ⇒ **1 个提交未推**，回滚点 `d5ccb32`） |
| 三处 `master` | 本地 / `origin` / `upstream` 全部 = `c34afebe`（11-04 纯快进，FF 前置检查见 §K-13） |
| PR 分支工作树 | `D:/my git/PSDR-build-artifacts/bom_pr` = `cb6dda0`（#18）；`…/pr-kicad-sch` = `0d1941a`（#17，已合） |
| tag | `fork-base/2026-10-30` |
| 未推 / 待批准 | **3 个提交未推**（`6f4bec4`、`0b3394e`、`d18961d`，回滚点 `84f3790`）；`docs/PSDR-revB-workorder.md` 仍未起稿 |
| 下一轮委派已备好 | `delegation/PROMPT-recheck-taskC.md`（TASK_C 剩余 32 行，值已随新包给出）；`delegation/PROMPT-uhsdr-frontend.md`（UHSDR/OVI40 前端器件级拆解） |
| 待外部条件 | PR #18 审；#19/#20 maintainer 回复；4 只件的原厂 PDF（SXB-2089Z / MASWSS0129 / SPU0410HR5H-PB / W3062A）；M3 实测量（11 个冲突位号 + 两条轨） |

## 索引

* 施工总账：`docs/WO-psdr-takeover.md`（任务 A/B/C/D/E + §F 规划 + G/H/I/J/K，**按 §号引用**）
* 资料缺口：`docs/PSDR-open-data-gaps.md`　外部回传成果：`docs/PSDR-external-findings-2026-11-03.md`
* 固件只读审阅：`docs/PSDR-firmware-survey.md`　作者实测编目：`docs/PSDR-author-measurement-log.md`
* U287 引脚—网络—SPI：`docs/PSDR-HMC1023-netlist.md`　上电检查表：`docs/PSDR-bringup-checklist.md`
* 范围与成本：`docs/PSDR-scope-and-cost.md`　替代件提案（**仅 fork**）：`docs/PSDR-alternates-proposal.md`
* BOM 三方对账：`tools/bom_refdes_crosscheck.py` + `Hardware/BOMs/PSDR_2.6.1/BOM_refdes_crosscheck.csv`
* 委派输入包 / 答案：`delegation/`（MANIFEST 只覆盖输入）与 `delegation/answers/`（外部断言，未逐条复核）
