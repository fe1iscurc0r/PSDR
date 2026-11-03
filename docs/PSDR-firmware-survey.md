# PSDR 固件源码状况与模块审阅（只读，未改一字）

日期：2026-11-02。对象：本仓库 `Source/`（F4 线）与 `Source_F7/`（F7 线）。
**本轮没有修改任何源码**，本文是注释与审阅的载体；验证方法见 §0.3。

## 0. 范围、口径与承诺

### 0.1 读到了什么深度

- 逐行读了：`main.c` 的主循环与菜单入口、`frequency_control.c`（全文 81 行）、`dds.c`（全文 86 行）、
  `signalPath()`、`processStream()`/`drawWaterfall()`/`drawSMeter()` 的关键段、
  `si5338.c` 的 `setFreq` 区域、`adc.c`、`timer`/`queue` 小模块。
- 结构化扫描了：两棵树全部 `.c/.h`（函数索引 149 + 119 个定义），以及中断向量与 ISR 入口。
- **没有**逐行审阅：厂商 `system/`（HAL/CMSIS，33 万行）与 `DSP_Lib`（CMSIS-DSP），
  这两部分只按其公开语义使用；`si5338.c` 里 695 行寄存器表按"数据手册驱动"对待，未逐条比对。

### 0.2 统计口径

行数只算 `.c/.h/.s`，排除 `build_linux*`/`obj` 等构建目录（否则 `Debug/` 里 362 个 `.o` 会把数字搞乱）。

| 树 | 总行数 | 项目自有 (`src/` + `include/`) | 厂商 (`system/`) | CMSIS-DSP (`DSP_Lib/`) |
|---|---|---|---|---|
| `Source/`（F4） | 341,318 | **12,035** | 194,934 | 134,349 |
| `Source_F7/`（F7） | 346,049 | **10,686** | 153,932 | 181,431 |

结论第一句：**真正属于这个项目的代码只有约 1 万行/棵**，其余 96% 是 ST 的 HAL/CMSIS 与 ARM 的 DSP 库。
所以"读源码"是可行的事，而不是 34 万行的深渊。

### 0.3 如何确认我没改源码

```bash
git -C . diff --stat -- Source Source_F7          # 应为空
git log --oneline -1 -- Source Source_F7           # 仍指向并入时的提交
```

本轮只新增本文档与 `docs/WO-psdr-takeover.md` 的记录。任何以"注释"为名的源码改动都没有做——
这是用户明确的边界（不改源码、不做 vibecoding）。

**但"主线里没有源码改动"这句不许说**（2026-11-03 自查，命令与结果都在这儿）：`next:Source_F7/`
相对 `upstream/PSDR_Rebuild:Source/` 有 **6 行 `.c` 改动**，是为了让 GCC 13 能编而加的 include 修正，
在 `Source_F7/Makefile.linux` 头部第 (e) 条与本总账 §E-7 都有记录，不是暗改：

```
$ git diff --stat upstream/PSDR_Rebuild:Source next:Source_F7
 .gitignore              |   1 +
 Makefile.linux          | 112 +++++++++++++++++++++++++++++++++++++
 src/frequency_control.c |   1 +
 src/si5338.c            |   5 ++++
 4 files changed, 119 insertions(+)
$ git rev-parse next:Source_F7/src/main.c upstream/PSDR_Rebuild:Source/src/main.c
def78a44... def78a44...        ← 主文件逐 blob 相同（i2c.c / dds.c 同）
```

⇒ 准确表述：**审阅与注释全部写在 `docs/` 里，`.c/.h` 只有上述 6 行编译必需的 include 修正**；
"没改一行源码"这种话以后不许写。

## 1. 两棵树的文件构成

| 文件 | F4 行数 | F7 行数 | 说明 |
|---|---|---|---|
| `src/main.c` | 1,946 | 2,166 | 主循环、菜单、频谱、S 表、信号路径 |
| `src/hal.c` | 1,432 | 1,439 | 板级引脚/时钟/外设的薄封装 |
| `src/ILI9341_t3.c` | 912 | — | 另一套 ILI9341 驱动，**F4 里没有任何调用点（死代码）** |
| `src/Adafruit_ILI9340.c` | 733 | 844 | 实际使用的显示驱动 |
| `src/Adafruit_GFX.c` | 547 | 576 | 图形/文字基础层 |
| `src/images.c` + `glcdfont.c` | 1,115 | 1,130 | 位图与字模（数据，不是逻辑） |
| `src/i2c.c` | 825 | 138 | F4 把 Si5338 驱动塞在 `i2c.c`；F7 拆出去了 |
| `src/si5338.c` | — | 695 | 时钟合成器寄存器表与写序列（F7 新增） |
| `src/frequency_control.c` | — | 81 | 频率合成的对外接口（F7 新增） |
| `src/uart.c` | 565 | — | F4 自写的串口收发；F7 改用 HAL，文件不存在 |
| `src/TinyGPS.c` | 609 | 609 | GPS NMEA 解析（第三方 TinyGPS 的精简版） |
| `src/spi.c` | 197 | 230 | 显示/DAC 的 SPI |
| `src/adc.c` | 187 | 202 | ADC 初始化与 DMA 配置 |
| `src/stm32f*xx_it.c` | 263 | 167 | 中断入口；F4 有 TIM3 等，F7 只剩 fault 类 |
| `src/misc.c` | 250 | — | F4 的 CMSIS `NVIC_*` 兼容层；F7 用 HAL 不需要 |
| `src/queue.c` | 126 | 126 | 8 位环形缓冲（串口用） |
| `src/dds.c` | 86 | 86 | **只有 `freqToReg()` 是活的**，位操作驱动全被注释掉 |
| `src/Timer.c` | 53 | 53 | GNU ARM Eclipse 模板（作者 Liviu Ionescu），SysTick 延时 |
| `src/_initialize_hardware.c` / `BlinkLed.c` / `uart_hal_stub.c` | 138/29/46 | 182/29/— | 启动与杂项；`uart_hal_stub.c` 是我们补的链接桩 |

**纠正两处我自己写错的描述（2026-11-03 第二轮）**：

1. 我在施工记录 §E-7 里把 F7 线称作"CubeMX + FreeRTOS 重写"，随后又在本文件写"实测 F7 树里
   **没有任何 FreeRTOS**（`xTaskCreate` 全树 0 处）"。**前半句的更正过头了**：
   - 对 `Source/`（F4）与 `Source_F7/`（= `PSDR_Rebuild` 的 `Source/`）两棵**应用树**成立——
     应用代码里没有 RTOS 调用，两条线都是裸机超级循环；
   - **对整库不成立**：同一血统里有作者 2019-05-24 的 CubeMX + **FreeRTOS** 重建
     （`b78769a`，在 `PSDR_Rebuild` 里、**不在 `PSDR_F7` 里**，故也在我们 `next` 里），落在
     `TestingMakeFile/PSDR`（785 个 `.c`，项目级 36）、`TestingMakeFile/PSDRestore/PSDR`（395，带
     `makefile` + `STM32F756VGTx_FLASH.ld`）、`TestingMakeFile2/PSDR`（390，项目级 17，带
     `Makefile` + **`STM32F746VGTx_FLASH.ld`**——芯片正是 2.6.1 的 F746）。
     FreeRTOS 是真在跑的：`TestingMakeFile/PSDR/Src/main.c:137 MX_FREERTOS_Init(); :140 osKernelStart();`
     ＋ `Src/freertos.c` ＋ `Drivers/CMSIS/RTOS/` ＋ `stm32f7xx_hal_timebase_TIM.c`（RTOS 配套 HAL 时基）。
     我当时的 grep 只覆盖两棵应用树，所以"全树 0 处"是**口径错误**。
2. 由此，本文 §5 的"不值得为此换到 FreeRTOS"**不能按原话读**：作者 2019 年已经选了 FreeRTOS，
   并且把他最头疼的 DMA 视频做到"pretty much perfectly"，只是**radio 一行没移植**（他自述
   "It can't do any radio like things yet… no interface, no audio"）。该建议的适用范围见 §5 的更正。

F7 相对 F4 的真实差别（不变）：换 CubeMX 生成的 HAL 骨架、加 Si5338 频率合成、拆分 I2C 驱动、
补外设断电函数（`teardownPeripheralPower`，`main.c:294`）。详见 `docs/PSDR-author-measurement-log.md` §3。

## 2. 模块级中文注释与审阅

下面每一节就是"源码注释"的内容（因为不能改源码，注释写在这里，按 `文件:行号` 定位）。

### 2.0 先看架构：这是 SDR，不是模拟超外差

从网表反推整条信号链（每步都有位号可查）：

```
Si5338(U241，3225 晶振 Y237/Y182 作参考) → 本振
      → 两路二极管环形混频器 L41/L81（封装名 MIXER_DIODE-RING_ADE-2ASK，Mini-Circuits ADE-2ASK）
      → 基带低通 HMC1023(U287)，旁路/滤波经 74CBTLV3253(U211/U298) 双 4:1 选择
      → 增益/相位检波 AD8302(U314) → MAGNITUDE/PHASE 两路模拟量
      → STM32F746(U121) 片内 ADC → CMSIS-DSP 的 FFT/FIR（固件里 processStream/drawWaterfall）
      → 音频 TPA0253(U199)
```

要点：

1. **没有独立 DSP 芯片**——"DSP"就是 STM32F746 本身（CMSIS-DSP 库），所以"换 DSP"不是解决缺料的杠杆。
2. **没有模拟晶振/VFO**——调谐靠 Si5338 数字合成器，3225 晶振只是参考，不决定频率。
3. 这是一台**正交采样/直接变换 SDR**：I/Q 两路混频 → 基带滤波 → MCU 采样 → 软件频谱。
4. 因此射频前端的"可替换性"取决于**频段与控制方式**，而不取决于"这台机器是不是 SDR"。

### 2.1 启动与主循环 `main.c`

**设计意图**：单线程"超级循环"——初始化外设 → 屏幕/菜单/瀑布图/S 表刷新 → 读桨叶 → 收发切换，全部在 `main()` 里。

**现状（F4，`Source/src/main.c`）**：
- 初始化序列在 `Setup()` 里：`setupPeripheralPower()`(264) → `hal_setupPins()` → `spi_init()` → `configDMA()`(276)
  → `initAdc()` → `setGainPot()`(666) → 主循环 `while(1)` 在 917，内含
  `updateMenu()`(939) / `updateDisplay()` / `drawWaterfall()`(941) / `drawSMeter()`(942)，
  再画 4 个桨叶状态方块、跟一次 GPS_PPS 到红灯。
- 主循环里**没有任何节拍控制**：帧率完全由"画一帧要多久"决定；也没有看门狗喂狗。

**现状（F7，`Source_F7/src/main.c`）**：
- 初始化更完整：`initFrequencySynth()`(997) → `setFreq(vfoAFrequency)`(999) → `timer_start()` → `populateCoeficients()`(1009)
  → `initDac1()` → `Encoder()`(1012) → 显示初始化。
- **但 1021-1032 行有一个无条件的 `while(1)`，只做 `fillScreen(BLACK)`/`fillScreen(BLUE)`**，
  没有 break、没有 `#if 0` 包裹 ⇒ 按当前提交的源码，**真正的 1065 行主循环永远到不了**。
  这是作者当年查 DMA 显示问题时留下的调试循环（对应上游提交"this DMA thing is killing me"）。
  注意：这不等于"2018 年的 hex 一定有这个问题"——hex 只能验证向量表与尺寸（§B），
  无法反证行为；但**仓库里的这份源码**是自洽地卡住的。
- 主循环体 (1065-1124)：`updateMenu`/`updateDisplay`/`drawWaterfall`/`drawSMeter` + 桨叶读 +
  `if(双桨都按下) signalPath(transmit_no_amp_no_filter) else signalPath(recieve_no_filter)`，
  `tone = 0`（没有侧音）。

**问题**：主循环 = UI 刷新 + 业务逻辑耦合；无时间片；F7 还有阻断级死循环（见 §3 P0-1）。

**改进**（按代价排序）：
1. 删掉 F7 的调试 `while(1)`（一行级改动，但按边界本轮不做）；
2. 主循环引入"时间预算"：先读输入、再处理、最后按固定节奏刷屏（例如 20-30 Hz），
   避免菜单响应被瀑布图绘制拖慢；
3. 喂狗：独立看门狗 + 关键路径心跳；
4. 把 `processStream()` 从 ISR 里挪出来（见 2.5），主循环只消费结果。

### 2.2 板级抽象 `hal.c`（1432/1439 行）

**意图**：把"引脚、时钟、外设句柄"集中定义，`main.c` 里用 `HAL_GPIO_ReadPin(PADDLE_THUMB_NC.port, ...)` 这样的形式访问。

**现状**：本质是"巨型全局变量表 + 引脚宏"，不是驱动抽象：`main.c` 直接操作具体引脚名，
换板就要改 `main.c`。`signalPath()`(F7:823) 里 10 个引脚逐个写死，注释还带着"I think!"与"always reverse of above"。

**改进**：把"信号路径 → 引脚状态表"抽成数据表（见 2.7），`main.c` 只调用 `path_apply(mode)`；
把引脚定义收进一个 `board.h`，业务代码不再出现具体引脚名。

### 2.3 显示栈（三套驱动并存）

**意图**：ILI9340（320×240 TFT）+ Adafruit GFX 图形库，实现菜单、瀑布图、S 表、位图。

**现状**：
- `Adafruit_ILI9340.c` + `Adafruit_GFX.c` 是实际使用的一套；
- `ILI9341_t3.c`（912 行）在 F4 里**没有任何调用点**——死代码，且与在用的驱动功能重叠；
- `images.c`（845/860 行）+ `glcdfont.c`（270 行）是纯数据；
- `drawSMeter()`(F7:1129) 用 `10*log(passBandRms*1e6+1)` 直接把一个浮点 RMS 映射成像素宽度，
  没有 dB 标定、没有参考电平、没有平滑——**S 表"钉住"（issue #6）的软件侧就长这样**。

**改进**：
1. 删 `ILI9341_t3.c`（先确认无调用点，已有 grep 证据）；
2. S 表：ADC 满量程标定 + 峰值保持 + 指数平滑；把"dBm → 像素"独立成纯函数便于离线测试；
3. 显示写入：把逐像素 `fillRect` 合成一条建立窗口 + 连续写（驱动已有 `setAddrWindow`），
   必要时用 DMA（F4 的 `configDMA` 已把 SPI 挂上 DMA，但显示路径没用满）；
4. 瀑布图：滚动区域用 ILI9340 的垂直滚动命令（`setVertialScrollStartAddress` 已实现），
   避免整屏重绘。

### 2.4 菜单与交互 `updateMenu()` / `Encoder()`

**意图**：旋转编码器选择菜单项并调值；菜单项 11（F4）/12（F7）个：
音量、模式、频率 6 位（MHz…Hz）、滤波上下限、（F7 新增）关机。

**现状**：`Encoder()`(F7:403) 在初始化里被调用一次，之后**轮询**计数（`menuEncoderTicks/2`）；
`updateMenu()`(F7:1173) 是一个**18 个分支的大函数**，每个分支直接访问全局变量并立即调 `setFreq`。

**问题**：逻辑与 UI 混在一起；加一个菜单项要改 3 处；没有"确认/取消"、没有长按、没有范围约束集中定义。

**改进**：表驱动菜单——`{id, label, getter, setter, min, max, step}` 数组 + 一个通用渲染/编辑函数；
编码器事件用"增量 + 按键"抽象；关机项接到真正的 standby（见 #9，受边界限制暂不动）。

### 2.5 采样与频谱 `processStream()` / `drawWaterfall()`

**意图**：ADC 双通道采 I/Q，做 FIR 滤波与 FFT，画瀑布图并算带内 RMS 给 S 表。

**现状（重要）**：
- `samplesA/B/C` 是 `float[FFT_BUFFER_SIZE]`，I/Q 交织写入（`main.c:503-513`，同时做直流偏置扣除与 AGC 电平跟踪）；
- **`processStream()`(F7:1577) 只被 `TIM4_IRQHandler`(F7:2013-2018) 调用**——FFT、滤波、RMS 全在**定时器中断**里跑；
- 更糟的是 `arm_cfft_radix4_init_f32()` 在 `processStream()` 内部被调用（F7:1590/1617/1643），
  每进一次中断就重新初始化一次 FFT 实例（CMSIS 里 `init` 会重建位反转表/标志），这批开销本可只做一次；
- `drawWaterfall()`(F7:1496) 在主循环里读 `samplesA` 做绘制，与 ISR 之间**没有双缓冲/原子保护**。

**改进**（收益最大的一处）：
1. `static arm_cfft_radix4_instance_f32` 在初始化阶段建一次；
2. 中断里只做"搬运 + 置标志"，FFT/RMS 移到主循环或独立任务（双缓冲）；
3. 实数信号用 `arm_rfft_fast_f32` 替代复数 radix-4，运算是复杂度减半量级；
4. 明确采样率与定时器周期的对应关系并写进注释（目前散落在魔数里）。

### 2.6 滤波器设计 `populateCoeficients()` / `applyCoeficient()`

**意图**：在频域构造 FIR 系数（矩形/窗函数），实现可变带宽与中心频率的带通。

**现状**：`populateCoeficients()`(F7:155) 用 FFT 生成系数（`arm_cfft_radix4_f32` at 217），
`applyCoeficient()`(F7:261) 逐样本卷积；带宽由 `filterUpperLimit - filterLowerLimit` 控制。

**问题**：只在频率/滤波菜单变化时重算（合理），但**没有系数归一化与溢出检查**的可见代码，
浮点逐样本卷积在 216 MHz 的 F7 上尚可，在 F4 上就是帧率瓶颈；窗口类型固定。

**改进**：加归一化与旁瓣检查（离线就能验：把系数导出，画频响）；把"频率/带宽 → 系数"做成纯函数 + 单测；
必要时改 Q15 定点。

### 2.7 射频与信号路径 `signalPath()`（仅 F7 有）

**意图**：用继电器/开关切换接收、发射、放大、滤波、阻抗桥、VNA 口。

**现状**：`signalPath()`(F7:823) 的 `switch` 里，`recieve_no_filter` 与 `transmit_no_amp_no_filter` 完整；
**`recieve_with_filter` 是空 case（860-862 行）**——滤波路径根本没实现。
驱动的引脚与网表完全对得上（本轮交叉核对过）：

| 固件里的名字 | 网表网络 | MCU 引脚 |
|---|---|---|
| `AMP_SWITCH_A/B` | `AMP_SWITCH_A/B` → U16 V1/V2 | **PA0**(U121.22) / **PE6**(U121.5) |
| `IMP_BRIDGE_SWITCH_A/B` | `IMP_BRIDGE_SWITCH_A/B` → U24 V1/V2 | **PC1**(U121.16) / **PA6**(U121.30) |
| `TX_RF_SWITCH_A/B` | `TX_RF_SWITCH_A/B` → U30 V1/V2 | **PB2**(U121.36) / **PA7**(U121.31) |
| `FILTER_S0/S1` | `FILTER_S0/S1` → U211/U298 | 网表见上 |
| `DAC_MUX` / `TRX_SWITCH` / `AMP_POWER` / `FIVE_VOLT_REGULATOR_ENABLE` | 同名网络 | — |

注释里的 "I think!"、"always reverse of above" 说明**极性没有被验证过**——这正是 issue #16 里
"前放不通"的一半原因（另一半是 Si5338/滤波器 IC 的寄存器配置）。

**改进**：把每个模式写成一张 `{pin, level}` 表（数据），并加一条运行期自检：
"A/B 两脚必须互补，否则报错"；`recieve_with_filter` 补全前，菜单里不应暴露该模式；
极性问题必须上电实测（B-1 的 4.1 项已经按这个设计好了）。

### 2.8 频率合成 `si5338.c` / `frequency_control.c` / `dds.c`

**意图**：Si5338 产生本振（LO）；`dds.c` 是更早的 AD98xx 类 DDS 位操作驱动，已被 Si5338 取代。

**现状**：
- `frequency_control.c`：`initFrequencySynth()` 配 I2C2（**Timing 常量注释写着"不确定怎么算的，抄自 EVAL 例程"**，41 行），
  然后 **`while(result != HAL_OK) HAL_I2C_IsDeviceReady(...)`（54-55 行）——无超时的阻塞重试**：
  Si5338 不应答 ⇒ **开机永久卡死**，屏幕都不会亮。`setFrequency()` 只是转调 `setFreq()`。
- `si5338.c`：寄存器表 + 写序列（`sendRegToSi5338`/`writeMultiSynthParameters`/`setFreq`），
  695 行里大部分是数据；`i2cSetup()` 与 `frequency_control` 里的初始化有重叠职责。
- `dds.c`：`ddsPrefix/sendToDds/ddsSuffix` 的函数体**全部被注释**，只剩 `freqToReg()`（28 位相位累加器换算，参考 75 MHz）。
  ⇒ 死模块，但保留着容易被误认为在用。

**改进**：
1. 给所有阻塞重试加超时并降级（例如 I2C 不通就跳过射频初始化、UI 照常起来并提示）；
2. 把 I2C 时序常量换成按 PCLK 计算的值，或者至少写清出处与适用范围；
3. 合并 `i2cSetup()` 与 `initFrequencySynth()` 的职责，保留一个入口；
4. 删除 `dds.c` 的死函数或移到 `legacy/`（**本轮不改**，仅建议）；
5. 频率设置增加回读校验（`read_Si5338` 已存在）。

### 2.9 采样前端 `adc.c` / `initDac1()` / `setGainPot()`

**意图**：ADC 采 I/Q（含直流偏置扣除）、DAC 输出音频、数字电位器控增益。
**现状**：`adc.c`（187/202 行）里 ADC+DMA 配置与采样处理耦合，魔数多；`setGainPot()`(F7:702) 通过 SPI 写电位器。
**改进**：采样率/偏置/增益做成显式常量并写注释；`setGainPot` 增加读回（若器件支持）。

### 2.10 GPS `TinyGPS.c`

**意图**：解析 NMEA，提供时间/位置/卫星数。**现状**：标准 TinyGPS 精简版，23 个函数，质量尚可；
串口轮询在 F4 由 `uart.c` 的环形缓冲支撑，F7 改 HAL 后由中断收字节。
**改进**：把"字节流→语句"与"语句→字段"分离便于离线测试（喂一段录制的 NMEA 即可回归）。

### 2.11 基础设施：`spi.c` / `i2c.c` / `uart.c` / `queue.c` / `Timer.c` / `misc.c`

- `spi.c`：SPI1/2 初始化与 `spi_readWrite`；显示与 DAC 共用，缺少总线仲裁/互斥（超级循环下恰好安全）。
- `i2c.c`：F4 里是 Si5338 驱动（825 行）；F7 只剩 `HAL_I2C_MspInit` + `clearStuckBusyFlag`（138 行，后者应对 I2C 卡死）。
- `uart.c`（F4）：自写收发 + 环形队列，F7 弃用。
- `queue.c`：8 位环形队列，`queue8_*` 语义清晰，可复用。
- `Timer.c`：GNU ARM Eclipse 模板（SysTick 延时）。
- `misc.c`（F4）：旧版 CMSIS 的 `NVIC_*` 兼容层，F7 不需要。

### 2.12 中断 `stm32f*xx_it.c`

F4：14 个入口，含 `TIM3_IRQHandler` 等业务中断；F7：只有 fault 与 SysTick（业务中断在 `main.c` 里，
例如 `TIM4_IRQHandler`(2013) 直接定义在 `main.c`），**ISR 位置不统一**。

**改进**：所有 ISR 收进 `*_it.c`，`main.c` 只保留回调；这样"中断里做了什么"一眼可查。

## 3. 缺陷清单

### P0（阻断/会砖机）

| # | 位置 | 现象 | 说明 |
|---|---|---|---|
| P0-1 | `Source_F7/src/main.c:1021-1032` | 无条件 `while(1)` 只刷屏，`main()` 到不了 1065 行主循环 | 调试残留；按现状源码，上电后停在蓝黑交替刷屏。**分支归属（2026-11-03 复核）：这条只在 `PSDR_Rebuild` 血统里有**——我们镜像的 `Source_F7/` 与 `PSDR_Rebuild:Source/src/main.c` 逐 blob 相同（`def78a44`），而维护者的 `PSDR_F7` 树里这段已被注释掉 |
| P0-2 | `Source_F7/src/frequency_control.c:54-55` | `while(result != HAL_OK)` 无超时 | Si5338 不应答时开机永久阻塞，先于显示初始化。**这条不是 Rebuild 专属**：`PSDR_F7` 树没有 frequency_control.c，同一圈无上限重试在 `PSDR_F7:Source/src/main.c:1031-1032`（维护者 2026-11-03 说"我2棵里 i2c.c 结构不同"，结构确实不同，但等待本身仍在） |

### P1（功能缺失/明显错误）

| # | 位置 | 现象 |
|---|---|---|
| P1-1 | `Source_F7/src/main.c:860-862` | `recieve_with_filter` 空 case——滤波接收路径未实现 |
| P1-2 | `Source_F7/src/main.c:1590/1617/1643` | `arm_cfft_radix4_init_f32` 在中断里每帧重初始化 |
| P1-3 | `Source_F7/src/main.c:2013-2018` + 1577 | FFT/FIR/RMS 全部在 TIM4 中断里执行，主循环与 ISR 共享 `samplesA/B/C` 无保护 |
| P1-4 | `Source_F7/src/main.c:838-847` 注释 | 继电器极性"我认为/总是相反"未验证——与 issue #16 的"前放不通"直接相关 |
| P1-5 | `Source/src/ILI9341_t3.c` | 912 行死驱动（无调用点），与在用驱动并存 |

### P2（可维护性/卫生）

| # | 位置 | 现象 |
|---|---|---|
| P2-1 | `src/dds.c` | 只剩 `freqToReg()`，其余全是注释掉的死代码 |
| P2-2 | `main.c` 菜单 18 个分支 | 加菜单项要改多处；无范围/步进集中定义 |
| P2-3 | `main.c` 里定义 ISR（F7:2013） | 与 `stm32f7xx_it.c` 职责分裂 |
| P2-4 | 两棵树大量重复文件 | `TinyGPS.c`/`queue.c`/`Timer.c`/`images.c`/`glcdfont.c` 完全相同却各存一份 |
| P2-5 | `si5338.c` 与 `frequency_control.c` 职责重叠 | 两个入口都能初始化 I2C/器件 |
| P2-6 | 主循环无看门狗、无节拍 | 帧率随负载漂移；卡死无自恢复 |

## 4. 架构判断：要不要换？

**结论：不要重写。** 理由与代价：

1. **代码量不支持"重写"这个选项**：项目自有逻辑仅约 1 万行，缺陷集中在少数位置（P0 两处、P1 五处），
   一次外科手术式修补就能拿到 80% 的收益；重写会把"已验证的 391 件/278 网/1132 脚"以外的
   所有历史经验（菜单手感、滤波器系数、显示时序）全部作废。
2. **两条线已经分叉**：F4（自写 HAL 层 + 自写 uart/misc）与 F7（CubeMX HAL + Si5338 拆分 + 信号路径表）。
   **F7 的结构明显更好**（驱动分层、外设断电、频率合成独立），应当以 F7 为演进主线，
   F4 保持"能构建、能对锚点"的冻结状态，不再加功能。
3. **要不要上 RTOS？**（**2026-11-03 限定适用范围**——原话"不值得为此换到 FreeRTOS"是
   在我没看过 `TestingMakeFile*/` 的情况下写的，收回）
   - 事实：`Source/`(F4) 与 `Source_F7/`(= `PSDR_Rebuild` 的 Source) 两棵**应用树**是超级循环；
     而同一血统里作者 **2019 年已经建了 CubeMX + FreeRTOS 的重建**（`b78769a`，
     `main.c:137 MX_FREERTOS_Init(); :140 osKernelStart();`，`TestingMakeFile2/PSDR/Makefile` +
     `STM32F746VGTx_FLASH.ld`），他自述 **DMA 视频"基本完美"、但 radio 一行没移植**。
   - 所以问题不是"该不该引 RTOS"，而是 **"要不要沿用他自己选定的那条下一代线"**。
     对**现有裸机树**做演进，我的建议不变：主循环 + 定时器中断 + 双缓冲 + 状态机就够，
     引 RTOS 会带来栈/优先级/竞态的新问题，而我们没有实测条件去驾驭它。
   - 若要**向作者的下一代靠拢**，正确动作是先审 `TestingMakeFile*/`（36/17 个项目级文件、
     `freertos.c` 的线程表、DMA 显示路径），量出"把 radio 代码搬过去"的真实工作量——
     **而不是**由我们从零再设计一套 RTOS 结构。见 `docs/PSDR-author-measurement-log.md` §3。
   ⇒ **推荐：`Source_F7/` 保持裸机做结构性三件事（§5 第 1-3 项）；改基/演进另立一线，先审后说。**
4. **真正需要"换架构"的是射频控制**：`signalPath()` 的散装 GPIO 写法必须换成"模式表 + 极性自检"，
   否则 #16 永远无法收敛。这是数据/接口层重构，不是固件重写。

## 5. 改进路线（不写代码，按收益/风险排序）

| 顺序 | 动作 | 收益 | 风险 | 需要实物？ |
|---|---|---|---|---|
| 1 | 删除 F7 的调试 `while(1)`；给 Si5338 初始化加超时与降级 | 把"砖机"变"能开机" | 低 | 否（可静态验证） |
| 2 | FFT 实例只初始化一次；把 `processStream` 移出 ISR（双缓冲） | 帧率与稳定性同时改善 | 中 | 是（需实测帧率） |
| 3 | 显示驱动收敛为一套；删 `ILI9341_t3.c`；S 表标定与平滑 | 少 900 行死代码；S 表可用 | 低 | 是（目视） |
| 4 | `signalPath` 改模式表 + A/B 互补自检；补 `recieve_with_filter` | 直接服务 #16 | 中 | **是**（极性必须实测） |
| 5 | 菜单表驱动化；ISR 收进 `*_it.c`；树间重复文件收敛 | 可维护性 | 低 | 否 |
| 6 | 状态持久化（#8） | 体验提升 | 中 | 是 | 

第 1 项是唯一"不改也能说清、改了必然更好"的；第 4 项必须等实物，否则改完也无法验证——
这也是本项目一直守的口径：**没有实测就别声称修好了**。

## 6. 附录

### 6.1 复算统计

```bash
python tools/fw_stats.py Source Source_F7                 # 目录级行数（排除构建目录）
python tools/fw_funcindex.py Source/src Source_F7/src      # 函数索引
```

### 6.2 函数索引摘要（每文件前几个）

- F4：`main.c` 25 个定义（`SystemClock_Config@101` … `drawWaterfall@1330`）；
  `TinyGPS.c` 23；`ILI9341_t3.c` 21；`Adafruit_GFX.c` 16；`stm32f4xx_it.c` 14；`uart.c` 13；
  `Adafruit_ILI9340.c` 12；`queue.c` 7；`i2c.c` 6（含 `setFreq@729`）；`dds.c` 4；`spi.c` 2；`adc.c` 1。
- F7：`main.c` 33（多出 `Encoder@403`、`teardownPeripheralPower@294`、`drawSMeter@1129`、
  `updateMenu@1173`、`drawWaterfall@1496`、`processStream@1577`、`TIM4_IRQHandler@2013`）；
  `si5338.c` 6（`setFreq@607`）；`frequency_control.c` 2；其余与 F4 同源。

### 6.3 本轮没覆盖的

- `system/` 与 `DSP_Lib/` 只按公开语义使用，未审阅；
- `si5338.c` 的 695 行寄存器表没有逐条对数据手册；
- 未做编译级验证（本轮只读；构建结果见 §E-7 与 `evidence/firmware_builds_2026-11-02.json`）；
- 未在任何实物上运行——本文所有"行为"判断都来自源码阅读，凡属猜测均已在文中标注（如 hex 不代表行为）。
