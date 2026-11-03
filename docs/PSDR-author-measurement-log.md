# 作者自述的装配与实测记录（fork-only 汇编）

日期：2026-11-03。用户提示"2016 年前后有人打板、焊装并做过一系列测试"，据此把上游提交信息里
**作者本人写下的装配状态与实测数字**逐条捞出来编目。目的是纠正我们自己两处过头的说法，
并把散落的信息变成可引用的台账。

## 0. 这些记录的证据强度（先说边界）

- 全部来自 **commit message 的自述**（`git log --all`），**不是仪器日志、不是测试报告**；
  没有原始数据、没有测量条件（带宽/调制/检波方式都没写）。
- ⇒ 可以当作"**作者当时观察到什么、他怎么判断**"的一手材料；
  **不可以**当作"已验证"。涉及具体 dBm 的每一条都要按 §5 的条件去复测才算数。
- 每条都给 sha + 日期 + 作者 + **该提交在哪些 ref 里**（用 `git merge-base --is-ancestor` 实测），
  免得下次又把某棵树的结论当成全库结论。

## 1. 打板与装配（这部分是硬事实，不是估计）

| sha | 日期 | 原话要点 | 在哪些 ref |
|---|---|---|---|
| `817dcff` | 2014-09-28 | 外壳 3D 文件、装配图与**装配指南**入库 | 全（含 master） |
| `1890b25` | 2016-04-18 | **"PSDR 2.5 prototypes are assembled."** 屏亮、大部分件在 work、频率合成还没上；并说"想改/想改进的事项记在**原理图的 notes 区**" | 全（含 master） |
| `8ad6b3c` | 2016-06-08 | "PCB 2.6v is complete and **prototypes will get here on Friday!**" | master=N、PSDR_F7=Y、Rebuild=Y |
| `468dc41` | 2016-07-31 | **"PSDR 2.6.1 PCB complete. Updates to BOM in preparation for order."**（就是我们转换与对账用的那份板） | master=N、PSDR_F7=Y、Rebuild=Y |
| `c2b94dd` | 2016-11-07 | "Fixes very basic transmit support. **Adds assembly instructions.**" | 同上 |
| `e4dabf0` | 2016-11-07 | 特意把 `.hex` 提交进库，"让大家不用自己编译也能烧 PSDR" | 同上 |

⇒ **三层判断要改**：我们此前把"第三层（射频验证过的整机）"记成**全空白**，这过头了。
准确表述是：**有作者本人的实测记录与逐条状态自述，但没有留下原始数据/日志/条件，
且这些记录只存在于提交信息里**；本文件就是把它们搬到可引用的地方。

## 2. 实测数字与功能状态（作者一手观察）

| sha | 日期 | 数字 / 状态 | 为什么对我们重要 |
|---|---|---|---|
| `2c1530d` | 2016-05-07 | "the PSDR can now tune from **2.5MHz to 175MHz**!"；灵敏度"around **-90dbm on 7MHz** and about **-80-85dbm on 146.4MHz**" | ①与固件 VFO 夹取 `main.c:1730-1731` 完全对上 ⇒ **2.5–175 MHz 是当年实测出来的**，不是随手写的数；②这是全库唯一一处带数字的接收灵敏度自述 |
| `8b02d73` | 2016-05-01 | 新二极管环混频器"Seems to be working!"；但 "**Reception in 2m seems very weak... might need a preamp or something?**" | **#16（前放）问题的起点**，比 2021 年那条抱怨早五年 |
| `59e59d7` | 2016-04-21 | GPS 模块在讲话、UART 丢字符；办公室里 GPS 一直**没锁**；他自问"天线够用吗？天线匹配呢？" | GPS 从 2016 起就是"能收但没验证过定位性能"——与我们 §GPS 降本需要四项对照同源 |
| `b3ee5db` | 2016-04-30 | I2C 又出问题、ADC 值可疑；他明确怀疑"**也可能是 F7 板的装配问题**" | 同一症状后来在 #16 出现；装配因素一直没被排除 |
| `a211a0b` | 2016-04-21 | I2C 与合成器已起来、分频在分，但**信号过不通**；怀疑变压器或混频器 | 前放/滤波路径的硬件疑点早有记录，不是 2021 才冒出来 |
| `7f0b215` | 2014-10-01 | F4 时代："PSDR2 接收良好、**镜像抑制好**、增益电位器有效；耳机能出声，**扬声器明显失败**（他注明是硬件）" | 镜像抑制当年是好的 ⇒ 若现在镜像/灵敏度差，先怀疑前端而不是 DSP |
| `d04d784` | 2014-10-06 | 初版发射可用、内置麦克风、触摸传感器工作；他自己说"发射比看起来**噪得多**，怀疑 DSP 问题" | TX 频谱纯度从第一天就是已知弱项 |
| `2a0a65c` | 2016-11-17 | 改成**两块桨叶都要按下才发射** | 与我们在 `#9` 待机那条发现的 PA0 冲突无关，属独立事实 |
| `4b2fd07` | 2017-01-01 | pwarren："**Power Off works!** click Reset button to power on" | 上游 `#9` 的来历；函数**已在**我们镜像（`Source_F7/src/main.c:294 teardownPeripheralPower()`），所以 #9 缺的不是这段代码，见 §4 第 3 条 |

## 3. 2019 的下一代架构：**库里有，我们从没审过**（我们的一处实质错误）

| sha | 日期 | 原话要点 | 在哪些 ref |
|---|---|---|---|
| `b78769a` | 2019-05-24 | "major architectural change… based on **STM32CubeMX** building a Makefile project… **includes FreeRTOS**… I've already got **DMA video working pretty much perfectly** (though not 100% optimized and tested)… **BUT! It can't do any radio like things yet**, none of that is implemented at all, no interface, no audio" | master=N、**PSDR_F7=N**、**Rebuild=Y**（⇒ 也在我们 `next`） |

落地位置（都在我们 `next` 里，实测清点）：

```
TestingMakeFile/PSDR/            785 个 .c（项目级 36）  PSDR.ioc + .mxproject，无 makefile
TestingMakeFile/PSDRestore/PSDR/ 395 个 .c              makefile + STM32F756VGTx_FLASH.ld
TestingMakeFile2/PSDR/           390 个 .c（项目级 17）  Makefile + STM32F746VGTx_FLASH.ld ← 芯片正是 2.6.1 的 F746
FreeRTOS 实体：TestingMakeFile*/PSDR/Middlewares/Third_Party/FreeRTOS/Source/{include,tasks.c,timers.c,portable/...}
真的在起内核：TestingMakeFile/PSDR/Src/main.c:137 MX_FREERTOS_Init();  :140 osKernelStart();
             + Src/freertos.c + Drivers/CMSIS/RTOS/ + stm32f7xx_hal_timebase_TIM.c（RTOS 配套时基）
```

⇒ **两处更正**：
1. 我们审阅里写过"全树没有任何 FreeRTOS（`xTaskCreate` 全树 0）"——**口径错了**：我的 grep 只覆盖
   `Source/` 与 `Source_F7/` 两棵应用树。对这两棵树的**应用代码**成立，对**整库不成立**。
2. 我们架构建议写过"不值得为此换到 FreeRTOS"——**不能这么表述**：作者 2019 年**已经选了 FreeRTOS，
   并且把他当年最头疼的 DMA 视频做到了"基本完美"**。我们的建议只对"在现有裸机树上不引 RTOS"成立。

**顺带影响第 2 步计划**：验证"能不能无头编 F7"之前，`TestingMakeFile2/PSDR` **已经带 CubeMX 生成的
Makefile 与 F746 链接脚本**——这条路可能比"把我们的 `Makefile.linux` 移植到 `PSDR_F7`"更快拿到
一个能编的 F7（代价是它没有 radio 代码，作者自述）。这两条路哪条更值，等实测完再定。

## 4. 由此立案的三件待查

1. **20 dB 落差**：2016 年作者自述 **-90 dBm@7 MHz**，2021 年 #16 里却是 **-70 dBm、"缺 50 dB"**。
   三个候选解释，按"不需仪器就能先查"排序：
   a) **板版本不同**（2.5/2.6 原型 vs 2.6.1 量产）；库里已知 2.6→2.6.1 只差 `R164` 270K→240K
      （`docs/PSDR-open-data-gaps.md` §2.1）——先确认这只电阻在不在前放偏置路径上；
   b) **档位/配置不同**：当年那台是"开发板 + 他手写的测试码"，量产板 LPF/前放从未配起来；
   c) 测量条件不同（带宽/检波方式/天线/噪声环境），他没写，所以**不能直接相减当退化**。
2. **原理图 notes 区里的"我想改的东西"清单**：`1890b25` 明说记录在"the notes section of the schematic"。
   库里有 `Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf` ⇒ 抽文即可（本机用 WSL `pdftotext`，
   Windows 侧无 `pdftotext`/`pypdf`；二进制输出先落文件再读）。**这是作者设计意图的第一手，我们还没挖。**
3. **pwarren 的待机/关机线到底缺不缺？**（已核，**结论是"不缺代码"**）
   `4b2fd07`(2017-01-01 "Power Off works! click Reset button to power on") 与 `3ecebbd`
   ("Nicely teardown peripheral's before StandBy") 都在 `PSDR_F7` 与 `PSDR_Rebuild` 血统里
   （实测 `next=Y master=N PSDR_F7=Y Rebuild=Y`），而且函数**就在我们镜像里**：
   `Source_F7/src/main.c:294 void teardownPeripheralPower()`（`PSDR_F7:Source/src/main.c:294` 同一只函数），
   调用点 `:1255`， standby 入口 `:2161 HAL_PWR_EnterSTANDBYMode()`。
   ⇒ `#9` 要的不是这段代码，而是**不用按 Reset 就能唤醒**——这是唤醒源问题，不是缺实现。
   正好与我们已经握着的那条硬证据对上：**PA0 既是待机唤醒脚（`PA0_WKUP`，U121.22）
   又是 U16 的 `AMP_SWITCH_A` 控制脚**（网表 + `signalPath()` 两边都用到），
   所以待机时 PA0 的电平同时决定"能不能醒"和"前放开关停在哪一挡"——
   这才是 `#9` "关不断/费电"的物理解释，也是**我们唯一还没对外说的一条硬证据**（发不发等批准）。

## 5. 复测这些数字需要的条件（写清楚才算可证伪）

灵敏度这类数字要按同一口径重做才可与 2016 对比：源 = 信号发生器（CW/单音，或两条 700/1500 Hz 双音做 SSB 等效），
50 Ω 端接 + 已知衰减器步进，检波 = 同一 FFT 带宽与同一 S 表刻度，记录"能看清瀑布上信号"的最小输入；
环境噪声必须一起记（作者 2021 年自己说过他那儿"S9+ 常年在响"，那 -70 dBm 可能是**噪声限制**而不是灵敏度限制）。
⇒ 没有这些条件，**任何"退化了 20 dB"的结论都不许写**。

## 6. 关联

- `docs/PSDR-firmware-survey.md` §1 的两处更正（RTOS 口径、"不值得换 FreeRTOS"）
- `docs/WO-psdr-takeover.md` §I-7（本轮 2016/2019 记录的发现过程与命令）
- `docs/PSDR-scope-and-cost.md` §8（调谐范围与 VFO 夹取）、§5（GPS 四项对照）
- `docs/PSDR-open-data-gaps.md` #1…#10（数据手册缺口，本文件新增原理图 notes 一条待补）
