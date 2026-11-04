<!-- PROVENANCE / 取证口径（本 fork 添加，非原文一部分）
来源：外部执行方（另一账号）2026-11-03 交回的调研答案，经 IMA 知识库 psdr 文件夹取回。
状态：**外部断言**。已逐条核对的部分见 docs/PSDR-external-findings-2026-11-03.md
      （原厂 PDF sha256 对得上才升级）；未核对的性能/年份数字不得直接进对外文本。
-->

原始文件：ANS_器件资料核实报告.md（28929 字节，sha256 `c64642215d8954d465bc7eac74340d6827c94f3436293e1dc696ee3c8bc5df88`）

# PortableSDR 2.6.1 器件资料核实报告

- 核实日期：2026-11-03
- 规则：每条结论附「文档名+版本+页码/表名」+英文原文摘录；读不到原文 = 未证实；经销商/媒体转述仅作线索（标注〔线索〕）；与提问前提矛盾处直接指出。
- 本地留存原始 PDF：`datasheets/`（SXB2089Z、SBB2089Z、HMC482、SY10EP52V 待补、SN74CBTLV3253、MASWSS0129、Si5338、AD8302、ES0290、STM32F7_errata_revZ）

---

## 1. SXB2089Z / SBB2089Z / HMC482ST89

### 1.1 SXB2089Z（Qorvo/RFMD）

| 项目 | 结论 |
|---|---|
| 频率范围 | 5–2500 MHz |
| 封装 | SOT-89 |
| 供电 | 器件电压 5V 级；测试条件 Vs=8V + RBIAS=20Ω，VDEVICE=5.2V，ID=120/135/150 mA（min/typ/max） |
| 生命周期 | **Discontinued**；EOL 公告 2019-07-18（PCN 19-0122），LTB 2020-01-29；官方推荐替代 TQP7M9101 |

证据：
- 《SXB2089Z 5MHz to 2500MHz MEDIUM POWER InGaP/GaAs HBT AMPLIFIER》DS110610，首页标题：*"5MHz to 2500MHz MEDIUM POWER InGaP/GaAs HBT AMPLIFIER... Package: SOT-89"*；电气表：*"Device Operating Current 120 135 150 mA VS=8v, RBIAs=20Ω, VDEVICE=5.2V"*。
- Qorvo 产品页（Data Sheet 06/10/2011）：*"5 - 2500 MHz InGaP / GaAs HBT Medium Power Amplifier Discontinued > End of Life announced July 18, 2019 (PCN 19-0122). Last Time Buy: January 29, 2020 Recommended replacement for new designs: TQP7M9101"*。

### 1.2 SBB2089Z（Qorvo/RFMD）

| 项目 | 结论 |
|---|---|
| 频率范围 | 50–850 MHz（可级联有源偏置增益块） |
| 封装 | SOT-89 |
| 供电 | 单电源 5V，ID=82/90/98 mA，VD=5.0/5.3 V |
| 生命周期 | **Discontinued**；EOL 公告 2025-06-11（PCN 25-0092），LTB 2025-12-21；官方推荐替代 TQP3M9018 |

证据：
- 《SBB2089Z 50MHz to 850MHz, CASCADABLE ACTIVE BIAS InGaP HBT MMIC AMPLIFIER》DS130718（©2006 RFMD），p.1 标题与电气表：*"50MHz to 850MHz, CASCADABLE ACTIVE BIAS InGaP HBT MMIC AMPLIFIER... Device Operating Voltage 5.0 5.3 V... Device Operating Current 82.0 90.0 98.0 mA"*。
- Qorvo 产品页（Data Sheet 07/16/2024）：*"Discontinued End of Life announced June 11, 2025 (PCN 25-0092). Last Time Buy: December 21, 2025 Recommended replacement for new designs: TQP3M9018"*。

### 1.3 与 SBB2089Z 是否同颗？→ **不是同一颗**

两者均属 RFMD/Qorvo、InGaP HBT、SOT-89，但：
- SXB2089Z = 中功率放大器（Medium Power Amplifier），5–2500 MHz，外部 RBIAS 偏置（Vs=8V）；
- SBB2089Z = 可级联 5V 增益块（Cascadable Active Bias），50–850 MHz，内置有源偏置直供 5V。

证据（同一段两份手册标题即自证）：*"MEDIUM POWER InGaP/GaAs HBT AMPLIFIER"* vs *"CASCADABLE ACTIVE BIAS InGaP HBT MMIC AMPLIFIER"*。
⚠️ 矛盾指出：若板上以为二者可互换，电气条件（偏置、频率、线性度）均不同，不能按同颗处理。另外注意：短波（<30 MHz）使用时 SBB2089Z 标称下限 50 MHz（其 Return Loss 规格 *"50 to 850 MHz Minimum 10dB"*），50 MHz 以下未规格化；SXB2089Z 标称 5 MHz 起。两者低频端的实际增益需实测。

### 1.4 输入脚是否允许直流？

**不允许直流馈入输入脚；官方要求外接隔直电容。**

证据：
- SXB2089Z DS110610，Pin Function 表：*"1 RF IN — RF input pin. This pin requires the use of an external DC blocking capacitor and matching components chosen for the frequency of operation."*；输出脚同样带直流：*"3 RF OUT/BIAS — RF output pin. This pin requires the use of an external DC blocking capacitor, choke, and matching components as shown in the Application Schematic."*
- SBB2089Z DS130718，Pin Function 表：*"1 RF IN — RF input pin. This pin requires the use of an external DC blocking capacitor chosen for the frequency of operation."*；*"3 RF OUT/BIAS — RF output and bias pin. DC voltage is present on this pin, therefore a DC blocking capacitor is necessary for proper operation."* 测试条件栏亦注明 *"Tested with Bias Tees"*。

### 1.5 HMC482ST89（ADI/Hittite）

| 项目 | 结论 |
|---|---|
| 频率范围 | DC–5 GHz |
| 封装 | SOT-89（3-Lead） |
| 供电 | 单电源 +6V 至 +12V，Icq=110 mA |
| 输入直流 | 引脚内部 DC 耦合，**必须**外加隔直流电容 |
| 生命周期 | Obsolete（PDN 16_0010，2016-03-03 停产通知） |

证据：
- 《HMC482: SiGe HBT Gain Block Amplifier SMT, DC - 5 GHz》ADI obsolete datasheet（04/25/2017 归档）：*"The HMC482ST89(E) is a SiGe Heterojunction Bipolar Transistor (HBT) Gain Block MMIC SMT amplifier covering DC to 5 GHz... Single Supply: +6V to +12V"*；Pin Descriptions：*"1 RFIN — This pin is DC coupled. An off chip DC blocking capacitor is required."*；规格表：*"Supply Current (Icq) 110 mA"*。

---

## 2. SY100EP52 /（板上）SY10EP52V

### ⚠️ 与前提矛盾（重要）

**SY10EP52V 不是 ÷2 分频器，而是 D 触发器。** ÷2 分频器是 SY10/100EP32V。官方不存在名为 "SY100EP52" 的独立 ÷2 器件（该料号 未证实）；SY10EP52V 是 5V/3.3V 差分数据+时钟 D 触发器。

证据：
- 《ECL Pro™ SY10EP52V, 5V/3.3V DIFFERENTIAL DATA AND CLOCK D FLIP-FLOP》Micrel，Rev.: F / M9999-092305，Issue Date: September 2005，p.1：*"The SY10EP52V is a differential data, differential clock D flip-flop. The device is functionally equivalent to the EL52 device."*
- 对照《SY10EP32V SY100EP32V, 5V/3.3V ÷2 DIVIDER》（Rev D, Sept 2005）才是 ÷2。

### 2.1 AC 表有无最低输入频率 fmin？

**AC 表没有 fmin 规格——未证实存在 fmin 行。** AC 表只保证最高翻转频率：

证据（SY10EP52V Rev F，AC ELECTRICAL CHARACTERISTICS 表，PECL/NECL 两档）：
> *"fMAX Maximum Toggle Frequency(2) — Min. 4 GHz"*（−40/25/85°C 三档均 Min 4）
> 注 2：*"fMAX guaranteed for functionality only. VOL and VOH levels are guaranteed at DC only."*

其余 AC 参数：tPLH/tPHL 250–410 ps、tS/tH 50 ps min、tPW 450 ps typ、tJITTER 0.2/1.0 psRMS、VDIFF 150/800/1200 mV。翻转器级器件工作下限由 tPW（450 ps 脉宽）约束，手册未给 fmin。

### 2.2 能否 DC 耦合？

**可以 DC 耦合（ECL/PECL 电平本就含完整 DC 规格），但注意：SY10EP52V 无 VBB 引脚**（VBB 是 EP32V 的功能，用于单端参考/AC 耦合再偏置）。EP52V 的 DC 规格（同手册 DC ELECTRICAL CHARACTERISTICS 表）：VIHCMR = VEE+2.0V ~ VCC（差分共模范围）；VIH/VIL 单端门限随 VCC 1:1 变化。AC 耦合方式官方未给参考电路 → 未证实。开路输入有钳位：*"The EP52V employs input clamping circuitry so that under open input condition (pulled down to VEE) the outputs of the device will remain stable."*

### 2.3 官方是否给出 quadrature ÷2 接法？

**官方手册未给出。** 该手册仅 7 页（描述/引脚/真值表/DC 表/AC 表/封装图），无应用章节，无 ÷2、无 quadrature 接法内容 → 未证实。
（业界用 D-FF 接 ÷2：Q̄→D；quadrature ÷2 用两片分别正/负沿触发——属通用做法，非本手册内容，此处仅提示不作为官方证据。）

---

## 3. SN74CBTLV3253（TI）

证据：《SN74CBTLV3253 Low-Voltage Dual 1-of-4 FET Multiplexer/Demultiplexer》，TI 文档号 SCDS039K – DECEMBER 1997 – REVISED JULY 2026。

### 3.1 真值表（每个 1-of-4 单元，Table 1 "Function Table"）

| OE | S1 | S0 | 功能（原文） |
|---|---|---|---|
| L | L | L | A port = B1 port |
| L | L | H | A port = B2 port |
| L | H | L | A port = B3 port |
| L | H | H | A port = B4 port |
| H | X | X | Disconnect |

即：S1:S0 = LL→B1、LH→B2、HL→B3、HH→B4 通 A。原文：*"L L L A port = B1 port; L L H A port = B2 port; L H L A port = B3 port; L H H A port = B4 port; H X X Disconnect"*。

### 3.2 Ron（§5.5 Electrical Characteristics，D/DBQ/DGV/PW/RGY 封装，−40~85°C）

| 条件 | Typ | Max | 单位 |
|---|---|---|---|
| VCC=2.3V（TYP at VCC=2.5V），VI=0，II=64mA | 5 | 8 | Ω |
| 同上，II=24mA | 5 | 8 | Ω |
| VCC=2.3V，VI=1.7V，II=15mA | 27 | 40 | Ω |
| VCC=3V，VI=0，II=64mA | 5 | 7 | Ω |
| VCC=3V，VI=0，II=24mA | 5 | 7 | Ω |
| VCC=3V，VI=2.4V，II=15mA | 10 | 15 | Ω |

原文行：*"ron (3) VCC = 2.3V, TYP at VCC = 2.5V VI = 0 II = 64mA 5 8..."*（DYY/BQB 125°C 档 Max 放宽到 10/9/20 Ω）。

### 3.3 关断电容（Cio(OFF)，原表 p.5）

- A port：**20.5 pF**（Typ）；B port：**5.5 pF**（Typ）；条件：*"VO = 3V or 0, OE = VCC"*。
- 另有 Ci（控制输入）3 pF；Ioff（断电隔离）15 µA。

### 3.4 隔离度及频率相关性

**数据手册未给 dB 隔离度、串扰、-3dB 带宽随频率的规格** → 未证实。CBTLV 系列只用电特性（Ron/Cio(OFF)）表征，"isolation" 一词仅出现在断电隔离（*"The device has isolation during power off"*）。开关时间（§5.7）：tpd 0.15–0.25 ns；ten/tdis（S）1–5.5 ns；ten/tdis（OE）1–5.5 ns。若需要隔离度-频率曲线，只能实测。

---

## 4. HMC1023LP5E（ADI/Hittite）

证据：《HMC1023LP5E 72 MHz DUAL PROGRAMMABLE LOW PASS FILTER WITH DRIVER》，文档版本 **v01.0113**，Register Map 章节 Table 15–22；Pin Descriptions Table 6。

### 4.1 寄存器映射（Table 15–22 摘要）

| 寄存器 | 名称 | 要点（原文） |
|---|---|---|
| 00h | Chip_ID（读）/ 读地址（写） | *"Chip_ID 24 D7780"*；写：*"Register Read Address... Soft Reset 1: Soft reset"* |
| 01h | Enable | *"cal_enable... filter_I_enable... filter_Q_enable... force_cal_code... doubler_enable... LSB_Zinput_select"* |
| 02h | Settings | *"opamp_bias[1:0]... drvr_bias[1:0]... gain_10dB... bypass_filter... coarse_bandwidth_code[3:0]... MSB_Zinput_select"* |
| 03h | Calibration | *"fine_bandwidth_code[3:0]... fine bandwidth setting override bits"* |
| 04h | Calibration/RC-BIST Strobe | *"Writing to any bit in this register starts a calibration cycle."* |
| 05h | Clk Period | *"clock_period[14:0]... Clock period entered is in pico seconds. i.e. 1/40 MHz clock =25000ps"* |
| 06h | Measure Adjust | *"Correction value used to adjust RC Calibration result."* |

### 4.2 截止频率档位表（Reg 02h [9:6] coarse_bandwidth_code）

原文：*"0000 - 5 MHz; 0001 - 7 MHz; 0010 - 10 MHz; 0011 - 14 MHz; 0100 - 20 MHz; 0101 - 28 MHz; 0110 - 40 MHz; 0111 - 50 MHz; 1000 - 72 MHz"*。
细调（Reg 03h [3:0]）：*"0000 - Minimum frequency ... 1011 - Maximum frequency"*（12 档，须 force_cal_code=1）。整机 3dB 截止 5–72 MHz 任意可编程，校准后精度 ±2.5%（*"Exceptional 3 dB Bandwidth Accuracy: ±2.5%"*）。

### 4.3 CALCK 要求频率（Reg 01h doubler_enable 位说明）

原文：*"0-- Doubler Disabled. RC Calibration clock 40 MHz<RC calibration clock<80 MHz; 1 -- Doubler Enabled. RC Calibration clock 20 MHz<RC calibration clock<40 MHz. Note: calibration clock duty cycle must be within 50% +/- 10%"*。
特性栏：*"Filter calibration is accomplished with any reference clock rate from 20 to 80 MHz."* CALCK 为 pin 11：*"Calibration clock input"*。

### 4.4 VDDBG(28) 与 VBG(29)（Table 6 Pin Descriptions）

- pin 28 VDDBG：*"Bias 5V Supply. Must be locally decoupled to GND."*（偏置电源，须本地去耦到地）
- pin 29 VBG：*"1.2V Bandgap output (testing only)"*（1.2 V 带隙基准输出，**仅供测试**，外部不要当基准负载用）

---

## 5. Si5338（Skyworks，原 Silicon Labs）

证据：《Si5338 I2C-Programmable Any-Frequency, Any-Output Quad Clock Generator》，**Rev. 1.6，August 29, 2021**。

### 5.1 关于"Si5338DN"的订货号

**"Si5338DN" 作为完整订货号 未证实。** 官方按速度档区分后缀（§8 Device Pinout by Part Number）：
> *"Si5338A/D/G/K/N have a maximum output clock frequency limit of 710 MHz. Si5338B/E/H/L/P have a maximum output clock frequency of 350 MHz. Si5338C/F/J/M/Q have a maximum output clock frequency of 200 MHz."*

即 D 与 N 同属 710 MHz 档（正式订货号形如 Si5338A-B00133-GM / Si5338P-B01597-GMR）。

### 5.2 各输出最低/最高频率与 VCO/分频组合限制（Rev 1.6）

- 输出（Features）：*"LVPECL/LVDS: 0.16 to 710 MHz; HCSL: 0.16 to 250 MHz; CMOS: 0.16 to 200 MHz; SSTL/HSTL: 0.16 to 350 MHz"*（上限随速度档 200/350/710 MHz 截断）。
- VCO：*"a high frequency analog phase-locked loop (APLL) which multiplies the input stage clock to a frequency within the range of 2.2 GHz to 2.8 GHz"*。
- MultiSynth：*"the output of each MultiSynth to produce any frequency from 5 to Fvco/8 MHz"*；旁路模式：*"integer divide ratios of 4 and 6... output frequencies of Fvco/4 and Fvco/6 MHz, which translates to 367–473.33 MHz and 550–710 MHz"*；且 *"Only two unique frequencies above Fvco/8 can be output: Fvco/6 and Fvco/4"*（同一 VCO 下所有输出共享约束）。
- 输出分频 R0–R3：*"configurable as divide by 1 (default), 2, 4, 8, 16, or 32"*（R≠1 时该路相位对齐失效）。
- ⚠️ 版本差异：旧版 datasheet 写 *"any frequency between the range of 5 to 350 MHz"*（下限 5 MHz）；Rev 1.6 改为 0.16 MHz 起。引用时注意版本。

### 5.3 I2C timing 与"寄存器计算方法"

I2C 总线时序（Rev 1.6，I2C DC/AC 表）原文：
> *"Data Rate Standard Mode 100 400 kbps; Hold Time (Repeated) START Condition tHD:STA 4.0 — 0.6 — µs; Set-Up Time for a Repeated START Condition tSU:STA 4.7 — 0.6 — µs; Data Hold Time tHD:DAT 100 — 100 — ns; Data Set-Up Time tSU:DAT 250 — 150 — ns"*
> 注：*"Must write register 27[7] = 1 if the I2C bus voltage is less than 2.5 V"*；*"I2C Bus Time out — Timeout Enabled 25 35 ms"*。

寄存器（频率配置）计算方法（§3.5）：
> *"ClockBuilder Pro™ Software... can be used to easily configure register map files... Alternatively, the register map file can be created manually with the help of the equations in the Si5338 Reference Manual."*

即：官方路径是 ClockBuilder Pro 导出寄存器映射；手工计算需按《Si5338 Reference Manual》的 MultiSynth 方程（N 反馈分频 + M 输出分频 + R 输出分频）。**"常见 PCLK 推荐值表"在官方数据手册/参考手册中 未证实存在**（PCLK 一词未出现在手册；若指像素时钟推荐表，属具体项目/应用笔记范畴，需另行指明出处）。

---

## 6. MASWSS0129TR（MACOM）

证据：《MASWSS0129 GaAs Broadband DPDT Diversity Switch DC - 6.0 GHz》，**Rev. V6**，Electrical Specifications 表 + Truth Table。

### ⚠️ 与前提矛盾

- 它是 **DPDT**（双刀双掷天线分集开关），不是 SPDT。
- 控制脚是 **VC1/VC2**，不是 V1/V2。
- 用户若按"SPDT+V1/V2"前提做真值表会错。

### 6.1 插损 / 隔离 / 切换时间（TA=25°C, Z0=50Ω, Vc=0/3V, 8pF 隔直）

| 参数 | 频率 | Typ | Max |
|---|---|---|---|
| Insertion Loss | 2.4 GHz | 0.70 dB | 1.30 dB |
| | 2–4 GHz | 0.75 dB | — |
| | 4–5 GHz | 0.90 dB | — |
| | 4.9–6 GHz | 1.00 dB | 1.55 dB |
| Isolation (on/off 或 off/on) | 2.4 GHz | 43 dB | — |
| | 4.9–6 GHz | 30 dB | （Min 25 dB） |
| Isolation (on/on 或 off/off) | 2.4 GHz | 11 dB | — |
| | 4.9–6 GHz | 20 dB | — |
| Trise / Tfall（10–90% RF） | — | 35 / 60 ns | — |
| Ton, Toff（50% ctrl→90%/10% RF） | — | 90 ns | — |
| Control Current（\|Vc\|=3V） | — | 6 µA | 25 µA |

原文（节选）：*"Insertion Loss 4 2.4 GHz... 0.70... 1.30...; Isolation (on/off or off/on) 2.4 GHz... 43... 4.9 - 6 GHz 25 30...; Trise, Tfall... 35 60 nS; Ton, Toff... 90 nS"*。
另注 3：*"For positive voltage control, external DC blocking capacitors are required on all RF ports."*

### 6.2 VC1/VC2 真值表（是否须互补驱动）

| Control Vc1 | Control Vc2 | ANT1-Rx | ANT1-Tx | ANT2-Tx | ANT2-Rx |
|---|---|---|---|---|---|
| 1 | 0 | On | Off | On | Off |
| 0 | 1 | Off | On | Off | On |
| 1 | 1 | Off | Off | Off | Off |
| 0 | 0 | Off | Off | Off | Off |

原文：*"1 0 On Off On Off; 0 1 Off On Off On; 1 1 Off Off Off Off; 0 0 Off Off Off Off"*；注 7/8：*"1 = +2.9 V to +5 V, 0 = 0 V +0.2 V. Differential voltage, V(state 1) - V(state 0), must be 2.7 V minimum and must not exceed 8.5 V."*
→ **有效通路只存在于 10/01 两态，必须互补驱动**；11/00 全关断。

### 6.3 生命周期与替代

- 数据手册正文标注 *"ADVANCED/PRELIMINARY"* 免责段（历史遗留），Features 行：*"RoHS Compliant Version of MASWSS0094"*。
- 生命周期：多家分销商标注 **Obsolete**〔线索〕；MACOM 官方页面未给出在产声明/替代型号 → **官方替代型号 未证实**。
- 第三方建议换 PE42423（Peregrine，需改版）〔线索〕；**pin-compatible 替代 未证实**。

---

## 7. Coilcraft WBC2-1TL(+B/C)

证据：Coilcraft《Mini Wideband Transformers — WBC》，Document 424-1（Revised 02/17/09 / 09/13/11 / 07/01/15 各版行一致）；官网 wbc2-1tl 页面现行动态表。

| 项目 | WBC2-1TL | WBC1-1TL |
|---|---|---|
| 阻抗比 | 1 : 2 | 1 : 1 |
| 带宽 | **0.200–500 MHz** | **0.250–750 MHz** |
| 插损 max | 0.50 dB | 0.58 dB |
| L min（pri / sec） | 10 / 20 µH | 9.5 / 9.5 µH |
| DCR max（pri / sec） | 120 / 150 mΩ | 75 / 75 mΩ |
| DC imbalance max | **8.5 mA** | 36 mA |
| 额定电流 | 250 mA | — |
| 隔离电压 | 300 Vrms | — |

原文行（Doc 424-1 表）：*"WBC2-1TL_ B 1 : 2 0.200 – 500 0.50 10 120 20 150 8.5 Red"*；官网列名：*"Current rating (mA) 250 ... Insertion loss (db) 0.5 ... DC imbalance 8.5 ... Bandwidth (MHz) 0.2 — 500 ... Isolation Voltage (Vrms) 300"*。
- 后缀：*"B = Less than full reel... C = 7″ machine-ready reel"*（即 WBC2-1TLB / WBC2-1TLC，电气相同）。
- **与 WBC1-1TL 不同带宽**（0.25–750 vs 0.2–500 MHz），且阻抗比不同（1:1 vs 1:2）。
- ⚠️ 用语纠正：手册里 "DC imbalance" 是**直流不平衡电流**（引脚 1、3 电流差，mA），不是幅度/相位不平衡度；"额定值"对应 current rating 250 mA 与 isolation 300 Vrms。

---

## 8. AD8302（ADI）

证据：《AD8302 LF-2.7 GHz RF/IF Gain and Phase Detector》，**Rev. B**（©2018），SPECIFICATIONS 表 + ABSOLUTE MAXIMUM RATINGS + "THEORY OF OPERATION" 公式 8/9/11/12。

| 项目 | 结论 |
|---|---|
| 频率范围 | >0 至 2700 MHz |
| 测量范围 | 增益 ±30 dB；相位 0–180°（±90°） |
| 输入电平（工作） | AC 耦合 −60 至 0 dBm（50Ω）；−73 至 −13 dBV；最佳参考 −30 dBm / −43 dBV |
| 最大输入（绝对最大） | −3 dBV ≈ **+10 dBm**（re. 50Ω） |

原文：*"Input Frequency Range >0 2700 MHz; Gain Measurement Range... ±30 dB; Phase Measurement Range... ±90 Degree"*；*"Input Voltage Range AC-Coupled... –73 –13 dBV... re: 50 Ω –60 0 dBm"*；ABS MAX：*"INPA, INPB Maximum Input –3 dBV Equivalent Power Re. 50 Ω 10 dBm"*。

**VMAG/VPHS 与 MSET/PSET 关系式**（测量模式 VMAG 短接 MSET、VPHS 短接 PSET）：
> 式 8a：*"VMAG = RF·ISLP·log(VINA/VINB) + VCP"*（600 mV/decade = 30 mV/dB，中心 VCP=900 mV 对应 0 dB，满幅 0–1.8 V 对应 −30…+30 dB）
> 式 9：*"VPHS = −RF·IΦ(|Φ(VINA)−Φ(VINB)| − 90°) + VCP"*（10 mV/degree，中心 900 mV 对应 90°，1.8 V↔0°、0 V↔180°）
> 控制器/比较器模式阈值式 11/12：*"VMSET(V) = 30 mV/dB × GainSP(dB) + 900 mV"*；*"VPSET(V) = −10 mV/° × (|PhaseSP(°)| − 90°) + 900 mV"*。

精度（动态范围/误差）：*"PHASE OUTPUT Dynamic Range Less than ±1 Degree Deviation from Best Fit Line"*（145°/143°/128°/115° @ 900/1900/2200 MHz 等档）；幅度误差以 TPC 7–9（900/1900/2200 MHz 三西格玛分布）形式给出，手册无单一"±x dB"数值行。ADI 技术文章〔线索〕称 900 MHz 下 40 dB 范围内 <0.2 dB、60 dB 范围 <1 dB、相位 <1°。

---

## 9. RXM-GPS-RM-T 与 W3062A

### ⚠️ 与前提矛盾（重要）

**RXM-GPS-RM(-T) 不是 u-blox 产品**，是 Linx Technologies（现 TE Connectivity）RM 系列 GPS 模块，核心芯片为 **MediaTek MT3337E**。料号 -T 为编带包装。

证据：《RM Series GPS Receiver Data Guide》Linx Technologies（Revised 10/6/2016）：*"The RM Series GPS receiver module is based on the MediaTek MT3337E chipset... 66 channels... track up to 22 satellites"*；TE/distributor 订货信息：*"RXM-GPS-RM-T Active TE Connectivity Linx RF RCVR GPS 1575.42MHZ MODULE"*〔线索〕。

### 9.1 是否内置天线

**无内置天线。** 原文：*"requires no programming or additional RF components (except an antenna)"*；*"No external RF components needed other than an antenna"*。RFIN 为 pin 19。

### 9.2 外部有源天线接法（原文，RM Series Data Guide "Antenna Considerations" / Figure 36）

> *"For active antennas, a 300 ohm ferrite bead can be used to connect the VOUT line to the RFIN line. This bead prevents the RF from getting into the power supply, but allows the DC voltage onto the RF trace to feed into the antenna. A series capacitor inside the module prevents this DC voltage from affecting the bias on the module's internal LNA."*

引脚表：*"17 VOUT — 2.8V output for an active antenna"*。即：VOUT(2.8V) → 300Ω 磁珠 → RFIN，给有源天线馈电；模块内置串联电容隔离内部 LNA 偏置。

### 9.3 灵敏度 / TTFF

- Tracking sensitivity **−161 dBm**；Cold start sensitivity **−143 dBm**（Linx Data Guide / 产品规格）。
- TTFF：*"In a cold start, the receiver takes up to 30 seconds to acquire its position... a hot start... takes 1 second"*；1PPS 精度 ±11 ns；辅助：*"EASY™ is a function to generate orbit predictions for faster cold and warm starts"*（仅 1 Hz NMEA）。
- 供电 3.0–4.3 V，跟踪电流 12 mA，待机 135 µA，封装 15×13×2.2 mm，UART NMEA 0183。

### 9.4 W3062A 是什么天线

**Pulse Electronics（YAGEO 集团）1.575 GHz GPS 陶瓷贴片（chip）天线，无源（不含 LNA）。**

证据：《W3062A 1.575GHz GPS Ceramic Chip Antenna》，Pulse Finland Oy，Preliminary (10/09)：
> *"1.575GHz GPS Ceramic Chip Antenna (Ground cleared under antenna, clearance area 7.80 mm x 5.25 mm)... Compact size W x L x H (7 x 1.6 x 1.6 mm)... GPS L1 band - 1.575 GHz... RHCP Gain 0 (peak)... Linear Max Gain 2.5 (peak) dBi... Return loss min -10 dB... 50 Ω... -40 to +85°C"*。

中心 1575.42±10 MHz，线极化增益 2.5 dBi（RHCP 0 dBic 峰值），SMD 焊接，与"有源天线"无关。

---

## 10. STM32F746 勘误表（SPI+DMA / I2C2 BSY / ADC+DMA / TIM/SAI）

### 10.0 前提澄清

- "STM32F746V6" 非 ST 官方订货号（V=100 脚封装，常见 STM32F746VE/VG 等）→ 按 STM32F746xx 处理。
- 现行勘误：**ES0290 Rev 7（18-Jul-2019）《STM32F74xxx STM32F75xxx device limitations》**，Table 2/3 适用 **silicon Rev Z and 1**。状态列只有一列"Rev. Z and 1"，含义：下列条目在 Z 与 1 两版硅片中**均存在**（未在 rev 1 修复）。Status：A=有 workaround，N=无，P=部分。

### 10.1 SPI+DMA

**无"SPI+DMA"专门条目 → 未证实。** SPI/I2S 章节（2.11）只有两条（见下）；DMA 相关条目在 DAC 章节（2.6.1/2.6.2）。

### 10.2 "I2C2 BSY" —— 与前提矛盾

现行 ES0290 Rev 7 中 **BSY 条目属于 SPI 不属于 I2C**：
- §2.11.2 *"BSY bit may stay high at the end of a data transfer in Slave mode"*（Status A）。原文：*"The BSY flag may sporadically remain high at the end of a data transfer in slave mode. This occurs upon coincidence of internal CPU clock and external SCK clock provided by master... As a conclusion, the BSY flag is unreliable for detecting the end of data transactions."* Workaround：NSS 标志 / RXNE / BSY+timeout / *"Write last data... Poll TXE... Disable SPI by clearing SPE... Poll the BSY bit"*。
- 旧版《STM32F74xxx/75xxx silicon limitations》DocID027162 Rev 3 把同一条目编在 I2C 小节 **2.3.2**（标题同为 BSY），但其正文条件写：*"It is related to the end of data transfer detection while the SPI is enabled at slave mode"* —— 历史编排错误，容易被误记为"I2C2 BSY"。
- 现行 I2C 章节 2.9 实际条目（均 Status A）：2.9.1 tSU;DAT 小于一个 I2CCLK 周期采样错误（*"the previous SDA value is sampled instead of the current one"*，workaround：提高 I2CCLK，SM≥4MHz/FM≥10MHz/FM+≥20MHz）；2.9.2 主机模式虚假 bus error；2.9.3 10-bit 主机模式首字节 NACK 后无法重启（修订史标注 *"I2C2 limitation... Added Section 2.9.3"*）；2.9.4 reload 模式末字节丢失。
- 修订史 Rev 6：*"I2C limitations... Updated limitations in line with I2C2 errata sheet"* —— 存在独立 "I2C2 errata sheet" 的说法，但该独立文档本体 **未证实**（本次未取到）。

### 10.3 ADC+DMA

**无"ADC+DMA"专门条目 → 未证实。** 最近似：
- §2.2.1 *"Missed ADC triggers from TIM1/TIM8, TIM2/TIM5/TIM4/TIM6/TRGO or TGRO2 event"*（Status A）。条件：PCLK2 分频器开启、TIMxCLK=2×ADCCLK 且 MMS 为 reset/update/compare pulse、或 TIMxCLK=4×ADCCLK。Workaround 原文：*"For TIM1 and TIM8... select the trigger detection on both the rising and falling edges. The EXTEN[1:0] or JEXTEN[1:0] bits must be set to 0x11 in the ADC_CR2 register. For TIM2/TIM4/TIM5/TIM6... enable the DAC peripheral clock in the RCC_APB1ENR register."*
- §2.5.1 *"ADC sequencer modification during conversion"*（A）：软件 SWSTART 启动后改 SQRx/JSQRx 会复位当前转换且不自恢复（*"the current conversion is reset and the ADC does not restart a new conversion sequence automatically"*）；硬件触发不受影响。
- DAC 的 DMA 条目（若关心 DMA 通路）：2.6.1 DMA underrun 后 DMA 不自动停（*"the DMA is not disabled by DMAUDR=1"*）；2.6.2 *"DMA request not automatically cleared by clearing DMAEN"*（A）。

### 10.4 TIM/SAI

- TIM：仅出现在 §2.2.1（作为 ADC 触发源，见上），无独立 TIM 章节条目。
- SAI：**ES0290 全文无 SAI 条目 → 未证实存在 SAI 勘误**（目录 2.1–2.14 无 SAI 节）。

### 10.5 是否已在硬件修复

Table 3 状态列 = "Rev. Z and 1"，以上条目两版硅片均带（A/N/P），即 **rev 1 未修复**；此后硅片修订（若有）需查更新版勘误（本 ES0290 Rev 7 发布于 2019-07-18，是否已随新 revision 关闭 **未证实**）。

---

## 11. 国产替代线索（均为〔线索〕，未做 pin-to-pin 核实）

> 以下来自厂商推广页/行业媒体/分销商，**不能当官方证据**；引脚兼容性、电气等效性均未证实，选用前必须自测。

| 原器件 | 国产线索 | 出处性质 |
|---|---|---|
| SBB2089Z / SXB2089Z | 官方替代是 Qorvo TQP3M9018 / TQP7M9101（非国产）。国产：GaAs HBT 代工（三安集成 H10HP56、海威华芯）有工艺能力〔线索〕；**无已证实 pin-to-pin 短波增益块** | Qorvo 页 + 行业报告〔线索〕 |
| HMC482ST89 | 同类 SiGe/GaAs 增益块国产选型 **未证实** | — |
| SY10EP52V（ECL D-FF） | 未检索到可信国产 ECL/PECL D-FF 替代 → 未证实 | — |
| SN74CBTLV3253 | 国产总线开关/多路复用（如 TI 兼容逻辑厂）**未证实**具体型号 | — |
| HMC1023LP5E | 国产可编程 LPF + ADC 驱动组合 **未证实** | — |
| Si5338 | 扬兴可编程时钟（宣称替代 Si5351/Si5338，1–800 MHz）〔线索〕；奥拉半导体（时钟发生器/抖动衰减）、大普通信 DP98xx、SYKG 系列（宣称 pin-to-pin 替代 TI/Silabs/IDT）〔线索〕 | 媒体/推广页 |
| MASWSS0129TR | 卓胜微（射频开关国内龙头）、昂瑞微、慧智微〔线索〕；DPDT 0–6 GHz 具体兼容型号未证实；第三方建议 Peregrine PE42423（非国产，需改版）〔线索〕 | 行业报告/分销商 |
| WBC2-1TL | 国产宽频传输线变压器/巴伦（顺络、铭普等）是否有 1:2 同规格 **未证实** | — |
| AD8302 | 国产增益/相位检测器同类 **未证实** | — |
| RXM-GPS-RM | 国产 GPS 模块（中科微 ATGM336H、和芯星通等）为常见替代方向〔线索〕，封装/协议不兼容，需改板；**未做规格比对** | — |
| W3062A | 国产 GPS 陶瓷天线（嘉康电子、艾尔信等）常见 25×25/18×18 贴片，7×1.6×1.6 同尺寸同频段型号 **未证实** | — |
| STM32F746 | 国产 MCU（GD32F4 系列、CH32V3 等）为生态替代方向〔线索〕；外设勘误对应关系未比对 | — |

---

## 12. 核实方法与局限

1. 原始 PDF 本地留存于 `datasheets/`，关键表格经页面图像与文本双向核对（SN74CBTLV3253 电气表、MASWSS0129 电气表/真值表均逐列核对过原页）。
2. 未能下载原 PDF 而仅取到 HTML 镜像全文的：HMC1023LP5E（DigiKey/天天IC 镜像的 v01.0113 文本）、SY10EP52V（digchip/microchip 文件服务器文本镜像）、Linx RM Series（alldatasheet/手动手册文本镜像）——摘录与镜像页码已注明，但建议以原厂 PDF 复核页码。
3. 全部"未证实"条目如需闭环，请提供对应原厂 PDF 或指明出处版本。
