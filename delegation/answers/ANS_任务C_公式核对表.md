<!-- PROVENANCE / 取证口径（本 fork 添加，非原文一部分）
来源：外部执行方（另一账号）2026-11-03 交回的调研答案，经 IMA 知识库 psdr 文件夹取回。
状态：**外部断言**。已逐条核对的部分见 docs/PSDR-external-findings-2026-11-03.md
      （原厂 PDF sha256 对得上才升级）；未核对的性能/年份数字不得直接进对外文本。
-->

原始文件：ANS_任务C_公式核对表.md（20096 字节，sha256 `ee4cabe55c86a76f4cfe1224c89a3bdbb92cbc165dc15b75c5d842e0226b5551`）

# PortableSDR 2.6.1 任务 C — 外接件公式/推荐值核对表

- 日期：2026-11-03
- 口径：判定仅由 ic_context 给出的板上值 × 官方手册公式/推荐值推出；无手册/无值 = 信息不足；不补"典型值"、不按常识补。
- `<file>:<row>` 以**正文头位号**为准（ima 上传批次文件名↔内容整体错位 4 位，见文末附注），文件名按 pack 规范 `ic_context/<ref>.md`，row 为本表内该文件的行序。
- 板上值解码：`CSM-X5R-22U-20P-10V-1210`=22µF X5R 20% 10V；`CSM-X5R-10U0-10P-25V-0805`=10µF 25V；`CSM-X5R-10U0-10P-10V-0805`=10µF 10V；`2U2H_INDUCTOR_NR6028T2R2N`=2.2µH；`IND_4.7UH_...CDRH4D28CNP-4R7PC`=4.7µH。**通用名（RES_0603/CAP_0603）不带值 → 实际值未知**。
- 手册版本：AD8302 Rev. B；AP3417C DS36516 Rev. 3-3（2019-07，NRND）；SSM2167 Rev. G；TPA0253 TI 2002 SLTS；AD8131 Rev. B；SN74LVC1G3157 TI；MASWSS0129 Rev. V6；HMC482 ADI 2017-04 归档；ADP1612/1613 Rev. A（2009-09）。

---

## 主表

| IC | 引脚/功能 | 手册公式（原文） | 手册推荐条件 | 板上实际值 | 判定 | 出处 | `<file>:<row>` |
|---|---|---|---|---|---|---|---|
| U314 AD8302 | VMAG（13）测量模式传递函数 | "VMAG = RF·ISLP·log(VINA/VINB) + VCP"（式 8a）；"VMAG = (RF·ISLP/20)(PINA−PINB) + VCP"（式 8b） | 斜率 30 mV/dB（600 mV/decade），VCP=900 mV，满幅 0–1.8 V ↔ −30…+30 dB；测量模式须 VMAG 短接 MSET | VMAG—R313(RES_0603)—MSET，R312(RES_0603) 并联支路；**非直接短接**，为 Fig. 8/9 斜率修正拓扑；阻值未知 | 信息不足（R312/R313 值未编码） | AD8302 Rev. B, p.15–16 式 8a/8b；p.18 "Modifying the Slope and Center Point" | U314.md:1 |
| U314 AD8302 | VMAG 斜率修正 | "NEW SLOPE = 30mV/dB × (1 + R1/(R2‖20kΩ))"；R2=20kΩ 接 VREF 时 "simplified to 1 + R1/10 kΩ" | MSET/PSET 输入阻抗 20 kΩ ±20% 须计入；修正后量程按比例缩小 | R313=R1（VMAG–MSET 串）、R312=R2（对地/参考支路）；值未知 | 信息不足（值未给） | AD8302 Rev. B, p.18, Fig. 8 / Fig. 9 | U314.md:2 |
| U314 AD8302 | VPHS（9）相位传递函数 | "VPHS = −RF·IΦ(\|Φ(VINA)−Φ(VINB)\| − 90°) + VCP"（式 9） | 斜率 10 mV/degree，VCP=900 mV 对应 90°，1.8 V↔0°、0 V↔180° | VPHS—R311(RES_0603)—PSET，R310(RES_0603) 支路；值未知 | 信息不足（值未给） | AD8302 Rev. B, p.15 式 9、p.16 Fig. 5 | U314.md:3 |
| U314 AD8302 | MSET（12）/PSET（10）控制器模式阈值 | "VMSET(V) = 30 mV/dB × GainSP(dB) + 900 mV"（式 11）；"VPSET(V) = −10 mV/° × (\|PhaseSP(°)\| − 90°) + 900 mV"（式 12） | 仅控制器/比较器模式（断开 VMAG–MSET、VPHS–PSET 反馈）时适用 | 板上 VMAG/VPHS 与 MSET/PSET 之间经电阻相连（测量模式变体），阈值公式不直接适用 | 一致（接法属测量模式族，式 11/12 不适用） | AD8302 Rev. B, p.18–19 式 11/12 | U314.md:4 |
| U314 AD8302 | INPA（2）/INPB（6）输入耦合 | 无公式 | "Must be ac-coupled"；输入阻抗 ≈3 kΩ‖2 pF（中频段） | C322(CAP_0603) 串 INPA、C309(CAP_0603) 串 INPB | 一致（隔直电容存在）；容值未知 | AD8302 Rev. B, p.11 Pin Descriptions、p.17 "Interfacing to the Input Channels" | U314.md:5 |
| U314 AD8302 | OFSA（3）/OFSB（5）偏置补偿 | "fHP (MHz) = 2/CC(nF)"，CC 为 OFSA/OFSB 对地总电容（含内部 10 pF） | 内部 10 pF → 默认 fHP≈200 MHz；外接电容可降低拐点 | C318、C315（CAP_0603，值未知） | 信息不足（CC 值未知，fHP 算不出） | AD8302 Rev. B, p.17 | U314.md:6 |
| U314 AD8302 | MFLT（14）/PFLT（8）输出滤波 | "T (ns) = 3.3 × CAVE (pF)"，CAVE=内部 1.5 pF‖外接 CFLT | "recommended that 1 pF minimum value external capacitors be added to the MFLT and PFLT pins" | C320、C307（CAP_0603，存在）；值未知 | 信息不足（值未知，≥1 pF 无法核） | AD8302 Rev. B, p.16 式 7 后 | U314.md:7 |
| U314 AD8302 | VPOS（4）供电 | 无公式 | VS = 2.7 V – 5.5 V | VPOS 经 R319(RES_0603) 供电 + C316 去耦；供电电压值未知 | 信息不足（电压值未给） | AD8302 Rev. B, p.11、p.3 SPECIFICATIONS | U314.md:8 |
| U114 AP3417C | FB（5）输出电压设定 | **手册未印显式方程**；仅 "The output voltage can be adjusted from 0.6V to 0.9\*VIN using an external resistor divider" + Table 1 选值表（EC：VFB=0.6 V，0.588–0.612） | Table 1：VOUT=3.3→R1/R2=450k/100k；2.5→320k/100k；1.8→200k/100k；1.2→100k/100k；1.0→66k/100k | R112/R113 = RES_0603 通用名，值未知 | 信息不足（R112/R113 值未编码） | AP3417C DS36516 Rev. 3-3, p.7 "Setting the Output Voltage" + Table 1 | U114.md:1 |
| U114 AP3417C | LX（3）电感 L109 | 无公式 | Table 1 全部推荐 **L = 2.2 µH**；EC 条件 L = 2.2 µH | L109 = 2U2H_INDUCTOR_NR6028T2R2N = **2.2 µH** | **一致** | AP3417C DS36516 Rev. 3-3, p.7 Table 1；p.5 EC 表 | U114.md:2 |
| U114 AP3417C | VIN（4）输入电容 | 无公式 | EC 测试条件 CIN = 4.7 µF；"the input capacitor should close to IC"；无 min/max 范围 | C163 = 22 µF（1210）、C83 = 10 µF（0805）在 V_SUPPLY | 信息不足（手册未给允许范围，仅给测试条件 4.7 µF） | AP3417C DS36516 Rev. 3-3, p.5 EC、p.7 | U114.md:3 |
| U114 AP3417C | 开关频率 | 无公式 | "1.5MHz Constant Frequency Operation"；fOSC 1.2/1.5/1.8 MHz (min/typ/max) | 固定内部频率，无外接设定件 | 一致（无外接件） | AP3417C DS36516 Rev. 3-3, p.1、p.5 | U114.md:4 |
| U314/U114 共网 | V_SUPPLY 轨 | — | AP3417C VIN 范围 2.5–5.5 V | C163=22µF、C83=10µF、L84=4.7µH、U161/U85/U114 共网；轨电压值未给 | 信息不足 | AP3417C p.1 Features | — |
| U189 SSM2167 | VDD（10）供电 | 无公式 | "Supply Voltage VSY 2.5 5.5 V"（Table 1） | +3V3 | **一致** | SSM2167 Rev. G, p.3 Table 1 | U189.md:1 |
| U189 SSM2167 | AVG_CAP（6）CAVG | "rms detector filter time constant is approximately given by 10 × CAVG milliseconds where CAVG is in µF" | "For optimal low frequency operation of the level detector down to 10 Hz, the value of the capacitor should be 2.2 µF"；"electrolytic capacitors are recommended here … in the range of 2 µF to 22 µF" | C188 = CSM-X5R-10U0-10P-25V-0805 = **10 µF**（X5R 陶瓷） | **一致**（10 µF ∈ 2–22 µF）；注：手册推荐电解，板上为陶瓷 | SSM2167 Rev. G, p.9 "LEVEL DETECTOR" | U189.md:2 |
| U189 SSM2167 | BUFOUT（4）→VCAIN（2）隔直 C2 | 无公式 | "An external blocking capacitor (C2) must be used … typically between 4.7 µF and 10 µF" | C192 = CSM-X5R-10U0-10P-25V-0805 = **10 µF** | **一致**（10 µF 在 4.7–10 µF 上界内） | SSM2167 Rev. G, p.8 "SIGNAL PATH" | U189.md:3 |
| U189 SSM2167 | CMPRS_RTIO（8）RCOMP | 无公式（Table 4 选值） | Table 4：1:1→0 Ω；2:1→15 kΩ；3:1→35 kΩ；5:1→75 kΩ；10:1→175 kΩ；">5 kΩ recommended"，<5 kΩ 可能被判短路 | R190 = RES_0603，值未知 | 信息不足（压缩比设不出） | SSM2167 Rev. G, p.9 "SETTING THE COMPRESSION RATIO" + Table 4 | U189.md:4 |
| U189 SSM2167 | GATE_THRS（7）RGATE | 无公式（Table 5 选值） | Table 5：−40 dBV→0 Ω；−48→1 kΩ；−54→2 kΩ；−55→5 kΩ；">5 kΩ 不推荐" | R187 = RES_0603，值未知 | 信息不足 | SSM2167 Rev. G, p.10 + Table 5 | U189.md:5 |
| U189 SSM2167 | OUTPUT（9）输出隔直 | 无公式 | "nominal output dc voltage … approximately 1.4 V; therefore, a blocking capacitor for grounded loads must be used"；负载 >5 kΩ | C139(CAP_0603) 隔直存在；值/负载未知 | 一致（隔直存在）；值信息不足 | SSM2167 Rev. G, p.8 | U189.md:6 |
| U199 TPA0253 | RIN（5）/LIN（9）增益设定 | "AV = – RF/RI"（输入级，RF=50 kΩ 内部）；"overall gain … 62.5 kΩ/RI in SE mode and 125 kΩ/RI in BTL mode" | RI 由用户选定；无 min/max | R204、R194 = RES_0603，值未知 → 增益算不出 | 信息不足 | TPA0253 (TI, 2002), p.1 产品描述 | U199.md:1 |
| U199 TPA0253 | VDD（3）供电 | 无公式 | "2.5 V to 5.5 V"；abs max 6 V | VDD 经 L141(ISM-0805-10U)=10 µH 磁珠供电，轨电压未知；C142/C143=22 µF、C147=10 µF 去耦 | 信息不足（供电电压值未给） | TPA0253, p.1 Features、p.3 Abs Max | U199.md:2 |
| U199 TPA0253 | 输出功率（vs 供电与负载） | 无公式（规格值） | "1 W Into 8-Ω From 5-V Supply；0.3 W Into 8-Ω From 3-V Supply" | SPEAKER(2403-260-00107) 阻抗未编码；供电值未知 | 信息不足（负载阻抗与 VDD 值均未给） | TPA0253, p.1 | U199.md:3 |
| U199 TPA0253 | RO/MO+（6）、LO/MO−（10）输出耦合 | 无公式 | BTL 输出可直驱；SE 模式/接地负载需隔直 | C152、C151 = CSM-X5R-22U-20P-10V-1210 = 22 µF 串联输出 | 一致（有隔直，22 µF 大于常规音频耦合需求；手册未给值范围） | TPA0253, p.1/应用图 | U199.md:4 |
| U30/U24/U16 MASWSS0129TR | V1（3）/V2（7）控制电平 | 无公式（真值表） | Truth Table 注 7/8："1 = +2.9 V to +5 V, 0 = 0 V +0.2 V. Differential voltage, V(state 1) - V(state 0), must be 2.7 V minimum and must not exceed 8.5 V"；仅 10/01 两态导通，须互补驱动 | TX_RF_SWITCH_A/B ← U121(STM32F746) GPIO.36/.31；GPIO 电平值未在表中给出（MCU 供电 +3V3_CPU） | 信息不足（GPIO 电平值未给）；注：若 GPIO 摆幅=3.3 V 则满足 +2.9–5 V | MASWSS0129 Rev. V6, Truth Table 注 7/8 | U30.md:1 |
| U30/U24/U16 MASWSS0129TR | ANT1（4）/Rx（10）/Tx（12）RF 口隔直 | 无公式 | 注 3："For positive voltage control, external DC blocking capacitors are required on all RF ports."；典型曲线用 8 pF；注 4："Insertion loss can be optimized by varying the DC blocking capacitor value" | C35、C27、C306（CAP_0603）分别串于 ANT1/Rx/Tx → 隔直存在 | 一致（三口均有隔直）；容值未知（8 pF 系典型曲线条件，非强制值） | MASWSS0129 Rev. V6, Electrical Spec 注 3/4 | U30.md:2 |
| U30 MASWSS0129TR | ANT2（6）RF 口 | 同上注 3 | 全部 RF 口均需隔直 | **pin 6 未出现在 ic_context 表**（表缺一行） | 信息不足（ANT2 网络未给出，无法核对） | MASWSS0129 Rev. V6 注 3 | U30.md:3 |
| U37 SN74LVC1G3157 | VCC（5）供电 | 无公式 | "1.65V to 5.5V VCC operation" | +3V3 | **一致** | SN74LVC1G3157 (TI), p.1 Features | U37.md:1 |
| U37 SN74LVC1G3157 | A/B1/B2 信号摆幅 | 无公式 | "allows signals with amplitudes of up to VCC (peak) to be transmitted in either direction"；I/O 绝对最大 −0.5…VCC+0.5 V | MIC 音频小信号（mV 级）经 A/B1/B2 | 一致（摆幅远小于 VCC） | SN74LVC1G3157, p.1、Abs Max 表 | U37.md:2 |
| U37 SN74LVC1G3157 | A–B 通路电阻 rON | 无公式 | "typically approximately 6Ω (VCC = 4.5V)"；DCK 封装 rON(over signal range) 200 Ω max @1.65 V | 通路串 R 外接件无；rON 随 VCC=3.3 V 变化（手册仅给 1.65/2.3/3/4.5 V 档表值） | 信息不足（3.3 V 档 rON 需查表插值，属"需曲线/表读出"） | SN74LVC1G3157, EC 表 rON/range 行 | U37.md:3 |
| U37 SN74LVC1G3157 | S（6）控制极性 | 无公式（Function Table） | 提取文本未完整捕获 Function Table → 需原页核对 | MIC_SELECT ← U121.57 | 信息不足（真值表未抄出，不自估） | SN74LVC1G3157 Function Table（待原页） | U37.md:4 |
| U253/U260 AD8131 | 增益 | "requiring no external components for a fixed gain of 2"；"Gain ΔVOUT,dm/ΔVIN,dm … 1.97/2/2.03 V/V" | 固定 G=2，无需增益电阻 | 板上无增益设定件（R221/R250/R249 为输入端网络） | 一致（固定增益 2） | AD8131 Rev. B, p.1、p.3 Table 1 | U253.md:1 |
| U253 AD8131 | V+（3）/V−（6）供电 | 无公式 | "Power supply range +2.7 V to ±5 V"；单电源表：VS=5 V | V+=+3V3，V−=GND | **一致**（3.3 V ∈ 2.7–5.5 V） | AD8131 Rev. B, p.1 Features、p.6 单电源表 | U253.md:2 |
| U253 AD8131 | VOCM（2）输出共模 | 无公式 | "The common-mode level of the differential output is adjustable by a voltage on the VOCM pin"；单电源 ADC 驱动推荐共模=中点 | HALF_VCC（1/2VCC 网络，≈1.65 V 若 VCC=3.3 V） | 一致（共模取半轨，与单电源 ADC 驱动用途相符；手册未给强制值） | AD8131 Rev. B, p.2、p.17 "Setting the Output Common-Mode Voltage" | U253.md:3 |
| U253 AD8131 | +DIN（8）/−DIN（1）端接 | 无公式 | 单端输入电阻 1.125 kΩ、差分 1.5 kΩ（Table 1） | R221/R250/R249 = RES_0603，值未知 | 信息不足（端接电阻值未给） | AD8131 Rev. B, p.3 Table 1 INPUT CHARACTERISTICS | U253.md:4 |
| U253 AD8131 | +OUT（4）/−OUT（5）耦合 | 无公式 | 输出摆幅（5 V 单电源）1.0–3.7 V；无隔直强制条款 | C252、C251(CAP_0603) 串联输出 | 一致（有耦合电容；手册无强制） | AD8131 Rev. B, p.6 | U253.md:5 |
| U304 HMC482ST89 | RFIN（1）输入隔直 | 无公式 | "This pin is DC coupled. An off chip DC blocking capacitor is required." | C13(CAP_0603) 在 RF_AMP_IN 网；C13 另一端网络未展开 | 一致（隔直件存在）；值未知 | HMC482 (ADI), Pin Descriptions "1 RFIN" | U304.md:1 |
| U304 HMC482ST89 | 供电（经 RFOUT/BIAS 偏置） | 无公式 | "Single Supply: +6V to +12V"；Icq=110 mA | L19(220 µH) 偏置馈电，**偏置电压未在 context 给出** | 信息不足（若偏置<6 V 则不一致，现无法判定） | HMC482 (ADI), p.1 Features/规格表 | U304.md:2 |
| U304 HMC482ST89 | 频带 | 无公式 | "DC to 5 GHz" | 用于 RF 通路 | 一致（带宽覆盖用法） | HMC482 p.1 | U304.md:3 |
| U287 HMC1023LP5E | VDDBG（28）去耦 | 无公式 | "Bias 5V Supply. Must be locally decoupled to GND." | C292(CAP_0603) 接 VDDBG 网（本地去耦存在） | 一致（去耦存在）；值未知 | HMC1023LP5E v01.0113, Table 6 Pin Descriptions | U287.md:1 |
| U287 HMC1023LP5E | VBG（29） | 无公式 | "1.2V Bandgap output (testing only)"，勿作外部基准负载 | **pin 29 未接**（context 无此脚） | 一致（悬空=不作负载） | HMC1023LP5E v01.0113, Table 6 | U287.md:2 |
| U287 HMC1023LP5E | CALCK（11）校准时钟 | 无公式 | "RC Calibration clock 40 MHz<RC calibration clock<80 MHz（doubler off）/ 20–40 MHz（doubler on）"；"duty cycle must be within 50% +/- 10%"；特性："any reference clock rate from 20 to 80 MHz" | C283(CAP_0603) 在 CALCK 网（疑串联耦合），时钟频率值未给 | 信息不足（时钟频率未知） | HMC1023LP5E v01.0113, Reg 01h doubler 位说明 + 特性栏 | U287.md:3 |
| U185 RXM-GPS-RM-T | RFIN（19）天线接法 | 无公式 | "requires no programming or additional RF components (except an antenna)"；有源天线：*"a 300 ohm ferrite bead can be used to connect the VOUT line to the RFIN line"*（VOUT=2.8 V 有源馈电） | GPS_ANTENNA=W3062A（无源陶瓷天线）经 C186(CAP_0603) 入 RFIN；无 VOUT 馈电网络 | 一致（无源天线方案，不需馈电/磁珠；手册仅要求"有天线"）；C186 值未知 | Linx RM Series Data Guide（2016-10-06）Antenna Considerations / Fig. 36 | U185.md:1 |
| U185 RXM-GPS-RM-T | VCC（12）供电 | 无公式 | 3.0–4.3 V（Data Guide 规格） | 经 Q126(MOSFET) 开关供电，电压值未给 | 信息不足 | Linx RM Series Data Guide | U185.md:2 |
| U58/U131/U216/U47 FAN4174 | 电源/输出摆幅/滤波接法 | — | **手册未取得**（onsemi 官网 403/拒绝） | +V=+3V3；OUT 与 −IN 间 C217/C223 网络（滤波/增益级） | 信息不足（缺手册，不自估公式） | — | U47.md / U131.md / U216.md |
| U255/U272 MCP6N11 | VFG（1）增益设定 | — | **手册未取得**（Microchip WAF 拒绝下载；先前误下 DS22192=MCP3901 已弃） | VFG 接 U15(MAX5388) 电位器抽头 + R254/R266 → 电压设定增益拓扑；"外接电阻设增益"的前提可能不成立 | 信息不足（缺手册；且问题前提与板上 VFG 电压设定拓扑存在出入，待手册裁定） | — | U255.md / U272.md |
| U161 MCP73871 | PROG1/2/3、THERM、VPCC | — | **手册未取得**（Microchip WAF 拒绝） | R162/R167/R168/R164/R165 均 RES_0603 值未知；PROG2 直接接 +3V3_CPU | 信息不足（缺手册+值未知） | — | U161.md |
| U15 MAX5388 | LA/LB/WA/WB 增益接法、SPI | — | **手册未取得**（ADI/Maxim 404） | LB/WB 与 MCP6N11 VFG 组电位器；LA/WA 同理（I/Q 两路） | 信息不足（缺手册） | — | U15.md |
| U4/U18 MAX4525CUB+ | 供电/Ron/Coff/摆幅 | — | **手册未取得**（ADI/Maxim 404） | DPDT 模拟开关用于 IQ 通路切换 | 信息不足（缺手册） | — | U4.md / U18.md |
| U32 SPU0410HR5H-PB | 供电/灵敏度/与前置接法 | — | **手册未取得** | pin1=+3V3、pin2/3=GND、pin4 出经 C33(CAP_0603) | 信息不足（缺手册） | — | U32.md |
| U211/U298 SN74CBTLV3253 | S0/S1 功能表 | 无公式（Table 1） | "L L L A port = B1 port; … H X X Disconnect"（Table 1 Function Table） | S0/S1 接 MCU GPIO（控制逻辑值未给） | 一致（真值表为逻辑规格，无外接件公式）；GPIO 时序信息不足 | SN74CBTLV3253 (TI) SCDS039K, §5.2 Table 1 | U211.md:1 |
| U211/U298 SN74CBTLV3253 | A/B 口 Ron、Cio(OFF) | 无公式 | Ron：VCC=2.3 V→5/8 Ω typ/max，VCC=3 V→5/7 Ω；Cio(OFF)：A 口 20.5 pF、B 口 5.5 pF typ | VCC=+3V3 | 一致（3 V 档 Ron 5/7 Ω 为表值，不涉外接件） | SN74CBTLV3253 §5.5 Electrical Characteristics | U211.md:2 |
| U279/U280 SY10EP52V | 最低输入频率 | 无公式 | **AC 表无 fmin 规格**（仅 fMAX 4 GHz min）；tPW 450 ps typ 约束脉宽 | 用作时钟路径 | 信息不足（手册未给 fmin → 未证实存在） | SY10EP52V Rev F, AC ELECTRICAL CHARACTERISTICS | U279.md:1 |
| L39/L82 WBC2-1TL | 巴伦参数 | 无公式 | 0.200–500 MHz；插损 max 0.50 dB；DC imbalance max 8.5 mA；额定 250 mA | 用作 1:2 巴伦 | 一致（带宽/用途；无外接件公式） | Coilcraft Doc 424-1 WBC 表 | L39.md:1 |
| L41/L81 ADE-2ASK | 混频器 | — | **手册未取得**（Mini-Circuits） | 二极管环混频器 ×2 | 信息不足（缺手册） | — | L41.md / L81.md |
| U121 STM32F746 | 外设勘误 | 无设计公式 | ES0290 Rev 7：BSY 条目属 SPI slave（非 I2C2）；无 SPI+DMA/ADC+DMA/SAI 专门条目 | — | 见《器件资料核实报告》§10（勘误类，非外接件公式） | ES0290 Rev 7 (2019-07-18) | U121.md |

---

## 缺手册清单（判定全部落"信息不足"的根因）

| 器件 | 官方来源尝试 | 结果 |
|---|---|---|
| MCP6N11 (DS22233) | ww1.microchip.com 多路径 + DigiKey 镜像 | WAF Access Denied / 404（注：DS22192 是 MCP3901，非本器件） |
| MCP73871 (DS20002090) | ww1.microchip.com 多路径 | WAF Access Denied |
| MAX5388/MAX5389 | analog.com、datasheets.maximintegrated.com | 404 |
| MAX4525/MAX4526 | 同上 | 404 |
| FAN4174 | onsemi.com/pdf/datasheet/fan4174-d.pdf | 403 Access Denied |
| SPU0410HR5H-PB | Knowles | 未尝试（等补） |
| ADE-2ASK(+) | Mini-Circuits | 未尝试（等补） |
| SY10EP52V 原厂 PDF | 本地为 HTML stub（已删）；正文引自镜像文本 | 建议补 Micrel/ON 原厂 PDF 复核页码 |

## 缺 ic_context 清单（U58/U85/U86 + parts_census.csv）

- ic_context U58(FAN4174)、U85(ADP1613)、U86(MAX4525) 三份未传 → 对应行只有手册侧、无板上值。
- ADP1613 手册已取得（ADP1612/1613 Rev. A）：式 1 **"VOUT = 1.235 × (1 + R1/R2)"**，电感推荐 "4.7 µH to 22 µH"（小于该范围须满足式 7），fSW 650 kHz(FREQ=GND)/1.3 MHz(FREQ=VIN)。待 U85 context 到位即可判 FB 分压。
- parts_census.csv 真身仍缺（同名件正文是 U47 context）→ 通用名 RES_0603/CAP_0603 的值无法反查，是本表大量"信息不足"的直接原因。

---

## 附注：ima 上传文件名↔内容错位（已实锤）

正文按位号字典序相对文件名前移 4 位：U114.md→L39、U121.md→L41、…、U85.md→U37、U86.md→U4；txt/csv 同样移位（AD8131.txt→bom_rows、74CBTLV3253.txt→README）。本表 `<file>` 一律取**正文头 refdes**。消费方如按文件名取数会整表错位。
