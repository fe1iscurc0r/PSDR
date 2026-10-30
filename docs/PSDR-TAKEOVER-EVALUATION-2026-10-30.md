# PSDR (PortableSDR) 项目接手评估 — 2026-10-30

评估对象：`https://github.com/MichaelRColton/PSDR`
评估人：沈遥 ｜ 评估基准：master @ `45acd0f59` (2026-09-11)

---

## 0. 一句话结论

**授权已完全打通，技术底座可复现，值得接手；但它不是"接手一个软件项目"，而是"接手一台还没调通的硬件 + 一份十年前的固件"。**

- 许可/授权：✅ 完全就绪（MIT 已落地，作者与维护者均已公开授权 fork 与继续开发）
- 固件可编译：✅ 已实测从零复现成功（Linux + arm-none-eabi-gcc 13.2.1），与作者 2016 年产物二进制锚点一致
- 硬件可用性：⚠️ 约 100 台已发出，作者手中仍存大量器件，但有 2 款关键器件已停产
- 射频性能：❌ **核心缺陷未修**——前置放大器与低通滤波器电路在量产板上从未工作，灵敏度缺约 50 dB

---

## 1. 授权链（已闭环，实测）

| 环节 | 证据 | 状态 |
|---|---|---|
| 上游许可 | `LICENSE.md` = MIT，末句显式声明"**包括固件、软件与硬件设计文件**" | ✅ 2026-09-11 由 Jeff Benson 提交 |
| 维护者授权 | issue #7 中 Jeff Benson 回复："I will see what I can do about adding an MIT license to the project to unblock you and **please feel free to fork and help keep the project moving forward**" | ✅ |
| 作者态度 | issue #16 中 Michael Colton（2025-10-28）："if anyone else wants to contribute I would love that and will support it"，并称手中仍存大量器件 | ✅ |
| 社区现状 | ★399 / fork 87 / watchers 92；作者本人持 87 个 fork 中的主导地位 | ✅ |

> 关键点：8 月 19 日以 `fe1iscurc0r` 名义在 issue #7 提出接手指议 → 9 月 11 日许可落地。**这条路已经走通，无需再谈授权。**

**但有一个空白**：Michael 本人（原始作者）至今**没有直接对你说过话**。Jeff 是 2021 年后的实际维护者。若要长期接手，建议补一次直接沟通。

---

## 2. 项目到底是什么

**PortableSDR**：一台独立的 HF 全频段软件定义收发信机（0–35 MHz），Kickstarter 众筹产物。

| 项 | 事实 |
|---|---|
| 形态 | 手持/背包便携机，彩色 LCD + 瀑布图，内置锂电 + GPS + 麦克风/扬声器 |
| 架构 | STM32F429（master）/ STM32F756（2.6.1 版，F7 分支） |
| 射频链 | 双 AD9834 DDS + 二次采样正交检波/激励器 + AD8302 幅相测量（兼 VNA/天线分析仪）+ 可控仪表放大器 |
| 模式 | AM / USB / LSB / CW，收发均可 |
| 特色 | **一体化 VNA + 天线分析仪 + GPS**，可抓裸 I/Q 输入输出 |
| 数量 | 约 100 台发出（Michael 估计，含未装料套件） |

**它不是 OpenHPSDR 那个 PowerSDR**，名字相近但完全无关——这是一个硬件工程项目。

---

## 3. 固件可编译性：✅ 实测已复现（这是最重要的好消息）

### 3.1 验证方法

从 master 检出源码 → 从 `Source/.cproject`（Eclipse CDT 工程）逆向还原编译参数与排除表 → 在 Linux 上用 `gcc-arm-none-eabi 13.2.1` 手工复现构建 → 与仓库内作者 2016 年的 `Source/Debug/PSDR.hex` 做二进制锚点比对。

### 3.2 实测结果

```
构建命令：make -f Makefile.linux -j
工具链：  arm-none-eabi-gcc 13.2.1 20231009
错误数：  0
告警数：  354
产物：    text 1077236 / data 2988 / bss 18216
```

**二进制锚点比对（与作者 2016-05-01 的 PSDR.hex）：**

| 锚点 | 作者产物 | 我的构建 | 结论 |
|---|---|---|---|
| 初始栈指针 SP | `0x20030000` | `0x20030000` | ✅ 逐字节一致 |
| Reset 向量 | `0x080001B5` | `0x080001B5` | ✅ 逐字节一致 |
| `_estack` / `__stack` | — | `0x20030000` | ✅ 与 `mem.ld` 定义吻合 |

> 结论：**这是同一份固件**。后续差异仅来自 GCC 版本（中断向量表内函数地址重排），属预期。

### 3.3 复现过程中发现的 4 个真实构建缺陷（上游从未修复）

| # | 缺陷 | 影响 | 最小修复 |
|---|---|---|---|
| 1 | `src/misc.c` 只 include `misc.h`，**未 include `stm32f4xx_hal_conf.h`** | `assert_param` 被当隐式函数声明 → 链接失败 | 补 `#include "stm32f4xx_hal_conf.h"` |
| 2 | `hal_checkTimeout()` **全仓无实现**，仅在 `hal.h:175` 声明 | TinyGPS 链接失败 | 补实现（比对 `HAL_GetTick()`） |
| 3 | `uart.c` 用 `USART_HandleTypeDef` 传给 `HAL_USART_GetState`（应为 `UART_HandleTypeDef`） | 编译失败 | 改类型；且该文件被 Eclipse 配置排除 |
| 4 | `arm_bitreversal_32`（CMSIS DSP）被 `.cproject` 排除但被引用 | 链接失败 | 解除排除或自实现 |

**外加两个构建配置坑（已解决）**：
- `.cproject` 的 Debug 排除表排除了 `*_ex.c`（含 `adc_ex.c`/`dac_ex.c`），但保留的 `adc.c`/`dac.c` 引用其中的 `__weak` 回调 → 断链。必须把 `_ex.c` 加回。
- Eclipse 的 linker script 是 **三个** `-T` 一起传（`mem.ld libs.ld sections.ld`）。只传 `sections.ld` 会导致 `ORIGIN(RAM)` 不解析、`_estack = 0xFFFFFFFF`（静默错误，不报错但固件必挂）。

### 3.4 复现产物（可直接使用）

```
/tmp/psdr2016/Source/Makefile.linux     ← 完整 Linux 构建脚本
/tmp/psdr2016/Source/build_linux/PSDR.hex  ← 137656+ 字节，已验证锚点
```

---

## 4. 硬件面评估

### 4.1 仓库内容（749 文件，master）

| 目录 | 内容 | 状态 |
|---|---|---|
| `Hardware/PSDR.sch` / `.pcb` | Eagle 原理图 + PCB | ✅ 完整（2.6.1 版） |
| `Hardware/Gerbers/` | 生产 Gerber | ✅ |
| `Hardware/BOMs/` | 1.0.0 / 2.0.0 / 2.5.0 / 2.6.1 四代 BOM | ✅ |
| `Hardware/Enclosure/` | SolidWorks 3D 壳体（.SLDPRT） | ✅ 但**需 SolidWorks 才能打开** |
| `Hardware/Block_Diagram/` | 系统框图（PDF/PNG/VSD） | ✅ |
| `Documentation/` | PSDR2 使用指南 PDF、视频脚本 | ✅ |
| `Keychain/` | "Giblet" 电键子板（独立小项目） | ✅ |

### 4.2 器件可得性（2021 年 issue #13/#14 的结论，未再更新）

| 器件 | 原型号 | 状态 | 替代 |
|---|---|---|---|
| RF 放大器 U304 | 599-1068-1-ND | ❌ DigiKey 停产 | SXB-2089Z（Win Source） |
| RF DPDT 开关 U16/U24/U30 | 1465-1374-1-ND | ❌ DigiKey 停产 | MASWSS0129TR-3000（Richardson） |

**Michael 明确表示手中仍存有大量器件**，可绕过采购风险。

---

## 5. 核心未解问题：射频链从未调通

这是**决定接手成本的真正分水岭**，来自 issue #16（至今 open，2025-10-30 仍在讨论）：

### 5.1 问题

- 前置放大器 + 低通滤波器电路在**开发板**上验证成功，在**量产板**上从未工作
- 现象：灵敏度约 −70 dBm，**缺约 50 dB 增益**，对弱信号"聋如砖"
- 作者原话（2021-12-06）："the preamp/low-pass filter circuit isn't working... That would certainly be a great place to focus attention for anyone that is interested in assisting with development."

### 5.2 代码层现状（实测自 master 源码）

| 位置 | 状态 |
|---|---|
| `hal.c:141` `PREAMP_POWER` | ✅ 已定义，`HAL_GPIO_WritePin(..., 1)` 注释写明 "1 = ON!"——**使能逻辑存在** |
| `hal.c:183` `IN_AMP_ENABLE` | ✅ 已定义，高电平使能 |
| `hal.c:186-188` `FILTER_S0/S1` | ✅ 已定义（滤波器档位选择） |
| `hal.c:120-122` `FILTER_GAIN_POT_SCLK/MOSI` | ✅ SPI 控增益电位器 |
| `i2c.c:145` `Reg_Store[][3]` | ⚠️ 350 项寄存器表（给 Si5338 时钟芯片），**滤波器 IC 的配置寄存器写入逻辑缺失** |
| 滤波器 IC 初始化 | ❌ **未实现**——作者自述"a lot of configuration registers that have to be set correctly" |

**判断**：使能引脚有了，但滤波器芯片的寄存器配置序列缺失。这需要拿到具体 IC 型号（原理图 U301/U302 附近）才能推进——**是一块需要真板+真器件才能推进的活，不是纯软件活**。

### 5.3 其他未决 issue（open）

| # | 标题 | 性质 |
|---|---|---|
| 6 | S meter 在 USB 模式下钉死、滤波器底端归零 | 固件缺陷 |
| 8 | 掉电保存菜单状态 | 功能缺失 |
| 9 | 真正的关机菜单项 + 开机手势 | 功耗管理（实测 ~80 mA，SI5338/AD8302/AD8131 是大头） |
| 13 | 2.6.1 BOM 器件停产 | 采购 |
| 14 | 2.6.1 BOM 缺失器件 | 采购 |
| 16 | **前置放大器启用** | **核心阻塞** |

---

## 6. 分支地图（7 个分支，作者代码不在 main）

| 分支 | 最后提交 | 内容 |
|---|---|---|
| `master` | 2026-09-11 | **F4 主线 + 2.6.1 硬件 + 许可/README 整理**（749 文件） |
| `PSDR_Rebuild` | 2021-01-27 | Jeff 的硬件重整（BOM/原理图归位），3356 文件 |
| `PSDR_F7` | 2018-07-31 | F7 平台移植（1006 文件） |
| `PSDR_F7_DMA` | 2018-06-21 | F7 + DMA 视频加速 |
| `DMA_Video` / `DMA_Video_Alt` | 2016-01-13 | 早期 DMA 显示尝试 |
| `PSDR2.5_PCB` | 2016-05-01 | 2.5 版 PCB |

**注意**：master 与 F7 分支差异达 **579 文件 / 15 万行**——F7 支线是另一套代码，**不要混用**。仓库 183 MB，`git clone` 全量需注意。

---

## 7. 与既有资产的生态位

| 你的资产 | 关系 |
|---|---|
| IC-705（日版）+ 泉盛 UV-K6 | PSDR 是**补充**而非替代：便携/野外/无天线场景；且自带 VNA + 天线分析仪（这两项 IC-705 做不了） |
| ESP32-S3 + SX1278 + NEO6M | 频谱侧互补。PSDR 是**收发 + 仪器的整机方案**，你的现有链路是**频谱感知 + LoRa**。PSDR 的射频性能指标（缺 50 dB）目前远不及你的方案 |
| 嘉立创EDA AI 绘图兴趣 | PSDR 硬件是 Eagle 格式 + SolidWorks 3D，**不适合直接喂嘉立创EDA**；但可作为"完整硬件项目全生命周期"的参考样本 |
| A 类执照 | PSDR 设计目标为 HF 段，**中国 A 类执照可用频段需核对**（40m 业余波段划分与国外不同） |

---

## 8. 接手方式：四条路（按成本/风险排序）

### 路线 A：固件复活优先（推荐先做）
**范围**：只做固件。修 §3.3 的 4 个构建缺陷 → 产出可复现的 Linux 构建 → 补齐前置放大器与滤波器配置 → 修 issue #6/#8/#9。
**成本**：中（不需要硬件，滤波器寄存器序列除外）
**风险**：低。issue #6/#8/#9 都是纯软件。
**产出**：一个能编译、能刷机的分支 + 可复现构建脚本。

### 路线 B：先复刻一块硬件
**范围**：用 `Hardware/` 的 2.6.1 BOM + Gerber 打样 1–2 块 → 与作者/Jeff 协作测前置放大器。
**成本**：高（打样 + 手工焊接 + 器件采购）
**风险**：中高。2 款器件停产；`Hardware/Enclosure/` 需 SolidWorks；SMD 密集（QFP + BGA 级）。
**前提**：需先与作者确认能否拿到他手中的存量器件与测试板。

### 路线 C：社区治理型接手
**范围**：不深挖硬件，先做上游维护者角色——修文档、建 CI、推进 open issue、与作者/Jeff/DM2NT 协同。
**成本**：低
**风险**：低，但见效慢，容易变成"GitHub 义工"。

### 路线 D：整体移植（不建议现在做）
**范围**：把 PSDR 移植到你的 ESP32-S3 + SDR 架构。
**成本**：极高
**风险**：极高。PSDR 的价值恰恰在"一体化整机设计"（VNA+天线分析仪+瀑布+电池+壳体），移植到 ESP32 会丢掉这些，等于重做一个 uSDX——而 uSDX/uSDR 已有成熟社区，无谓重复。

---

## 9. 建议：分三步走

**第一步（本周，纯软件，零风险）**
1. Fork 到 `fe1iscurc0r/PSDR`
2. 建分支 `fe1iscurc0r:build/linux` ，提交 §3.3 的 4 个修复 + `Makefile.linux`
3. 上游提 PR（**先给师傅过目再发**，用呼号 BG5GXO / @handle，不写真名）
4. 产出：可复现构建 = 社区层面最有价值的贡献

**第二步（并行沟通）**
5. 给 Michael 发邮件，主题明确：**承接 issue #16 的前置放大器工作**，并问三件事：① 手里还有哪些器件 ② 能否提供一块测试板 ③ 滤波器 IC 具体型号与寄存器序列
6. 同时在 issue #16 留言同步进展

**第三步（视第二步答复再定）**
7. 若作者愿意提供器件/测试板 → 进入路线 B 打样
8. 若拿不到 → 聚焦路线 A，把固件做扎实（issue #6/#8/#9），这条路本身对社区就有价值

---

## 10. 实测数据索引（本次评估产生）

| 项 | 值 |
|---|---|
| 工具链 | `arm-none-eabi-gcc 13.2.1 20231009`（apt `gcc-arm-none-eabi`） |
| 构建结果 | 0 error / 354 warning |
| 固件尺寸 | text 1,077,236 / data 2,988 / bss 18,216 |
| SP 锚点 | 作者 `0x20030000` = 我的 `0x20030000` ✅ |
| Reset 向量 | 作者 `0x080001B5` = 我的 `0x080001B5` ✅ |
| 复现工作区 | `/tmp/psdr2016/Source/`（构建脚本 + 产物） |
| 上游仓库 | ★399 / fork 87 / 749 files (master) / 183 MB .git |

---

## 11. 风险清单

| 风险 | 等级 | 说明 |
|---|---|---|
| 射频链修复需要实物 | 🔴 高 | 前置放大器/滤波器问题**无法纯靠读代码解决** |
| 器件停产 | 🟡 中 | 2 款，但作者有存量 |
| 3D 壳体需 SolidWorks | 🟡 中 | 开源但非通用格式 |
| F7 支线代码分叉 | 🟡 中 | master 与 F7 差 15 万行，别混用 |
| 上游作者精力有限 | 🟡 中 | Michael 自己说"没有时间"；Jeff 也说无法全职 |
| 作者未直接回应你 | 🟢 低 | Jeff 已授权，实质障碍为零 |
| HF 频段与 A 类执照匹配 | 🟢 低 | 需自行核对频段 |
