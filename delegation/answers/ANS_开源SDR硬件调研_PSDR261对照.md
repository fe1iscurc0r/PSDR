<!-- PROVENANCE / 取证口径（本 fork 添加，非原文一部分）
来源：外部执行方（另一账号）2026-11-03 交回的调研答案，经 IMA 知识库 psdr 文件夹取回。
状态：**外部断言**。已逐条核对的部分见 docs/PSDR-external-findings-2026-11-03.md
      （原厂 PDF sha256 对得上才升级）；未核对的性能/年份数字不得直接进对外文本。
-->

原始文件：ANS_开源SDR硬件调研_PSDR261对照.md（13578 字节，sha256 `cb3357ca6c7fee3ed6502438fe91b5b03b0ec4f84097d43a01ccf321eaa11a47`）

# 开源 HF/QRP SDR 硬件层调研 —— 对照 PortableSDR 2.6.1

- 调研日期：2026-11-03（全部数值/年份引自当日抓取的页面，标注来源；未证实处写"未找到"）
- 对照基线：PortableSDR 2.6.1 BOM（`bom_rows_PSDR261.csv`）+ 器件核实报告（`PortableSDR261_器件资料核实报告.md`）
- 注意：uSDX 原理图图片（https://github.com/threeme3/usdx/blob/master/usdx.png ）因网络 TLS 限制未取到原件，其内容按 README+OSHwLab+HF5L 文本复原，标注〔文本复原〕

---

## 1. 核心架构与芯片选型对比

| 项目 | 收发架构 | 混频/采样开关 | 时钟/LO | MCU/处理器 | ADC/CODEC | 滤波器 | PA |
|---|---|---|---|---|---|---|---|
| **uSDX** | 直接变频 QSD（Tayloe）+ Class-E | 74HC4053〔文本复原，OSHwLab〕+ 74ACT00×3 并联驱动 PA（HF5L） | Si5351A（I2C 800 kbit/s 相位调制，25MHz TCXO） | ATmega328P（部分 20MHz 超频） | MCU 内置 10bit ADC（音频/键控复用） | 分立 LPF：C0G 电容 + T37-2 磁环，按波段 | 3×BS170 标称；实测 IRF540N（80/40m）或 3×2N7000（20m） |
| **QCX/QCX+** | 直接变频 QSD + Class-E（纯 CW） | **FST3253**（预焊 SOIC）+ 74ACT00N（QRP Labs 手册 1.03） | Si5351A（27MHz 晶体，模块含 LM317L+2×BS170 电平移位） | ATmega328 DIP | 无 codec（MCU 内 ADC 做 CW 解码） | 7 元件 LPF：按波段 C0G（如 80m：39p/22p/180p/470p/1200p）+ T37-2；LM4562×6 有源滤波 | 6×BS170 + 1×MPS751；74ACT00 驱动 |
| **mcHF 0.6.3** | 直接变频 QSD + 线性 PA（48kHz I/Q） | **SN74CBT3253C**（LO=4×f） | Si570（10MHz–1.4GHz I2C XO） | STM32F407（168MHz M4） | **WM8731** 16bit/48k（ADC SNR 90dB） | 7 阶 LC BPF×4 继电器重叠波段 + 运放有源基带 LPF | 2×**RD16HHF1**（5W 标/10W 峰），数字偏置，锁存继电器切 LPF |
| **mcHF 新版 0.9** | 同上演进 | 未找到（Altium 工程内） | 未找到 | **STM32H747BIT6**（M7 480MHz + M4 DSP） | 未找到 | 未找到 | 25W（README） |
| **SoftRock Ensemble RXTX** | QSD/QSE + PC 声卡 | 74HC4053 类模拟 MUX（Tayloe） | Si570（÷4 得正交）或晶体（Lite） | ATtiny85（V-USB 控制） | PC 声卡 16bit | 分立 LPF（按波段） | ~1W FET 驱动级 |
| **Peaberry V2** | QSD/QSE + USB codec | Tayloe U6(RX)/U8(TX) | Si570（4×LO） | Cypress PSoC（peaberry.cydsn） | **PCM3060** 64× 过采样 ΔΣ（模拟 USB 声卡） | 分立（T1–T5 磁件按波段） | 1W |
| **Hermes-Lite 2** | **直接采样**（AD9866 MxFE，全双工） | AD9866 内部 | **Si510** 73.728MHz（$5） | **Intel MAX 10 FPGA**（25K LE，144-EQFP）+ 以太网 | AD9866 内置 12bit（$27–33） | **N2ADR 滤波板**：6×TX LPF（160–10m）+ 3MHz RX HPF + SWR 桥，I2C 7bit 继电器 | 5W 推挽 MOSFET + 40mW(+17dBm) 辅输出 |
| **OpenHPSDR Hermes/ANAN** | 直接采样（DDC） | — | 122.88MHz 采样时钟 | Cyclone 系 FPGA + PC（Thetis/PowerSDR） | **LTC2208 16bit @122.88MSPS**（eham ANAN-10） | 外部 LPF/天线口 | ANAN-10 10W+（PA/SWR 板） |
| **KiwiSDR 2** | 直接采样（仅 RX，网络共享） | — | 外部 ADC 时钟输入（2 版新增，可接 GPSDO） | **Artix-7 A35** FPGA + BeagleBone Green | **LTC 14bit @65MSPS**（设计评审；BOM 估 $24；〔注意〕具体型号官方 PDF 未点名） | 30MHz LPF/前端 + 保护电路（2 版：气体放电管+TVS+balun） | 无 TX |
| **TX-500（商用）** | SDR（32bit 浮点 DSP） | 未公开（闭源） | 未公开 | 未公开 | 未公开 | **11 组分立 RF BPF** + 4RX/2TX 数字滤波 | 1–10W（6m 7W） |
| **UHSDR/OVI40** | DDC/DUC 概念（目标） | 未完整公开 | 未找到 | **STM32H743（400MHz）或 STM32F767（216MHz）** | 未找到 | **HMC1023 驱动已证实**（2018-10，ovi40h7 分支） | 设计目标 50W（软件可控） |
| **PortableSDR 2.6.1（基线）** | Tayloe 类 QSD + VNA/天线分析 | **SN74CB3Q3253×2**（4:1 总线开关）+ MASWSS0129×3（DPDT RF）+ MAX4525×3 | **Si5338A**（26MHz TCXO×2 参考）+ **MC10EP52×2**（ECL D 触发器，时钟链） | **STM32F746VGT6**（M7 216MHz） | BOM 未见独立 ADC（疑用片内 ADC——未证实） | **HMC1023LP5E**（5–72MHz 可编程 LPF，6 阶 Butterworth） | BOM 未见功率级 FET；增益链为 SXB-2089Z（EOL）/HMC482（Obsolete） |

## 2. 关键性能数值

| 项目 | 灵敏度/MDS | 动态范围 | TX 功率/效率 | 抑制/杂散 | 功耗等 | 来源（年份） |
|---|---|---|---|---|---|---|
| uSDX | MDS -135dBm/200Hz@28MHz〔商用机线索〕 | BDR 123dB@20kHz / 78dB@2kHz〔同上〕 | 5W 级；HF5L 实测 5.8W/76% @3.7MHz、9.4W/78% @3.5MHz、8.8W/93% @7.1MHz（IRF540N） | 载波/边带抑制 >-45dBc，IMD3 -33dBc，RX >-50dBc（官方 README） | 13.8V 供电 | README；[HF5L](https://hf5l.pl/en/transceiver-usdx-with-arduino-nuo/)；商用资料（2021–2024） |
| QCX+ | 未找到 | 未找到 | 3–5W（13.8V） | ≥50dB 无用边带抑制；200Hz CW 滤波无振铃 | 7–16V | [qrp-labs.com/qcx](https://qrp-labs.com/qcx)（2020–2026） |
| mcHF 0.6.x | **-126dBm/300Hz**；UI 底噪 -144dBm | A/D 削波 -18dBm（同信道）；IP3≈+30dBm（估） | 5W 标 / 10W 峰 | 未找到 | RX 360mA / TX 3A @12V（11–16V） | S53DZ 状态报告（2017）；[MDPI 6(4):58](https://www.mdpi.com/2624-6120/6/4/58/htm)（2024） |
| TRX SDR Eagle | **-132dBm/300Hz** | 未找到 | 20W | 未找到 | 3.5–28MHz | [UHSDR Wiki](https://github.com/df8oe/UHSDR/wiki/Supported-Hardware)（2021 更新） |
| SoftRock | 未找到（无源前端"偏聋"，需外放） | 受 16bit 声卡限制 ~90dB 级 | ~1W | 未找到 | 12V | [sdrutah.org](http://sdrutah.org/info/rx_softrock.html)（2019） |
| Peaberry V2 | 未找到 | 两音 2kHz 间隔三阶 DR **99dB** | 1W | 未找到 | USB 130–150mA | [存档手册](https://ae9rb.github.io/peaberry) |
| Hermes-Lite 2 | 未找到 | 未找到 | 5W + 40mW；16 级功率步进 0.5dB/级 | 未找到 | 12–16V，≤2A | [james.ahlstrom.name](https://james.ahlstrom.name/hl2filter/)；BBC 俱乐部（2023） |
| Hermes/ANAN | 未找到 | 未找到 | ANAN-10 10W+；Hermes 板 500mW | 未找到 | 收 10kHz–55MHz；48/96/192kHz 谱 | eHam ANAN-10 |
| KiwiSDR 2 | 未找到（VLF/HF 优化） | 14bit ADC（设计取舍：$24 14bit vs $80 16bit） | 仅 RX | 未找到 | 5V/2A；4 路流 24/7 ≈30GB/月 | [设计评审 PDF](https://kiwisdr.com/docs/KiwiSDR/KiwiSDR.design.review.pdf)（2016） |
| TX-500 | **-136dBm**（typ，前置开）；-141dBm@14MHz〔经销商线索〕 | **BDR 129dB**（14MHz、2kHz、前置关）；RMDR 119/108/106dB@20/5/2kHz | 1–10W（6m 7W） | 载波抑制 >50dB；谐波/杂散低于载波 >50dB | RX 仅 **100mA**（13.8V） | [lab599 promo PDF](https://downloads.lab599.com/TX500/Discovery-TX500-promo.pdf)（2022 手册） |
| OVI40 | 未找到 | 未找到 | 设计 50W（软件可控） | 未找到 | 12–16V；48kHz 谱/瀑布×32 缩放 | [OVI40 wiki](https://www.amateurfunk-sulingen.de/wiki/doku.php?id=en:ovi40what:description) |

## 3. 原理图与设计文件（可直接下载）

| 项目 | 文件 | 内容要点 |
|---|---|---|
| (tr)uSDX | [Main+RF Boards with Notes v1.0n PDF](https://dl2man.de/wp-content/uploads/2022/10/truSDX_Main-RF_Boards_with_Notes_v1.0n.pdf)（2022） | **全标注原理图+LPF 元件表**：20m=L11 400nH(10T/T37-2)+L12 196nH(7T)+C10 68p/C12·C14·C18 470p/C16 150p；30m=L21 576nH(8T)+L22 256nH…；80m–6m 完整表（3×BS170 条件）；L1=50µH≈12T FT37-43 Class-E 扼流圈；G6KU-2 锁存继电器经 TCA9555；警告：震动会误切继电器、10m 4 匝密绕 vs 均绕差 5MHz 陷波点 |
| uSDX Sandwich 组装手册 | [DL2MAN Building Manual PDF](https://dl2man.de/wp-content/uploads/2021/01/1_2_uSDX-Building-Manual-DL2MAN.pdf)（2021） | Class-E PA 图；80m–6m LPF 计算表（C1/C2/L2/C3/C5/L3/C4，负载 12Ω）：如 20m：C1 128p、C2 472p、L2 0.52µH、C3=C5 446p、L3 0.21µH、C4 154p |
| WB2CBA LPF | [antrak.org.tr](https://antrak.org.tr/blog/usdx-multiband-low-pass-filter/)（经 HF5L 引） | 80m/40m/20m 分立值：80m C1 680p/L2·L3 15T；40m C1 360p/12T·10T；20m C1 100p/8T·7T（T37-2） |
| QCX+ | [组装手册 1.03 PDF](http://qrp-labs.com/images/qcxp/manual1.03.pdf) | **逐波段 BOM**（80m/60m/40m/30m/20m/17m 电容值表）+ 全部半导体清单（FST3253、Si5351A、74ACT00、LM4562×6、BS170×6、MPS751） |
| QCX-mini | [组装手册 1.03 PDF](http://www.qrp-labs.com/images/qcxmini/manual_1_03.pdf) | 波段电感表（80m 2.4µH=25T/T37-2 … 17m 0.55µH=13T/T37-6；T1 5+5+5+n T50-2） |
| mcHF | [m0nka/mcHF](https://github.com/m0nka/mcHF)（Altium + Gerber rev6/7/8 + 结构件）；[UHSDR 组装 Wiki](https://github.com/df8oe/UHSDR/wiki/Building-Your-Very-Own-mcHF) | RF 板：CX2074NL 1:4 balun、G6KU-2FY 继电器、RD16HHF1、LM2941CT(8V)、MC7805；IZ6MAF 载波抑制改进 |
| SoftRock | [wb5rvz.com/sdr](https://wb5rvz.com/sdr)（分页原理图/分阶段 BOM）；[Ensemble RXTX 原理图 3 页](https://www.giga.co.za/ocart/index.php?route=product/product&tag=tx&product_id=54) | QSD/QSE/驱动 PA 分级 BOM（按波段） |
| Peaberry | [Peaberry V2 Full PDF](https://ae9rb.github.io/assets/peaberry/Peaberry%20V2%20Full.pdf) | PSoC+Si570+PCM3060 全装配手册；磁件绕制规范（BN-43-2402、T1–T5 双线） |
| Hermes-Lite 2 | [N2ADR 滤波板页](https://james.ahlstrom.name/hl2filter/)（原理图/BOM/KiCad/Gerber）；[HL2 wiki](https://github.com/softerhardware/Hermes-Lite/wiki/Hermes-Lite-2.0) | 滤波板 LPF 电容 630V NP0 1206 建议、功率传感器 10:1 磁环；Mouser 预置购物车 |
| KiwiSDR | [KiwiSDR 1](https://kiwisdr.com/docs/KiwiSDR/KiwiSDR.design.review.pdf) / 2 / 2rev1.1 原理图 PDF（kiwisdr.com） | 设计评审：KiCAD 捕获（layout 存在但未公开发布 Gerber）；$24 14bit ADC 取舍论述 |
| OVI40 | [amateurfunk-sulingen OVI40](https://www.amateurfunk-sulingen.de/wiki/doku.php?id=en:ovi40what:description)（UI 板 CERN OHL 1.2） | DDC/DUC 目标、2200m–2m、50W |
| TX-500 | 仅用户手册/promo PDF（闭源） | 11 BPF、性能表 |
| uSDX 原图 | [usdx.png](https://github.com/threeme3/usdx/blob/master/usdx.png) | 网络限制未取到原件（curl/PowerShell 均 TLS 失败） |

## 4. 与 PortableSDR 2.6.1 的芯片级对照与设计启示

1. **HMC1023——现成固件参考**：UHSDR 在 OVI40-H7 语境下有完整驱动（2018-10 多笔提交：driver、manual fine calibration、fixes，[例 1](https://github.com/df8oe/UHSDR/commit/c447c2e4c00026d23dec43cccf173a7267a638a2)）。SPI 寄存器/校准流程可直接借鉴。ADI 官方页另提供 **HMC1023 Gerber、Eval PCB 原理图、评估软件**（[analog.com/HMC1023](https://www.analog.com/HMC1023)）。⚠️ **ADI 已标 HMC1023 "Obsolete"**——与你上午的 EOL 清理同性质，建议同步规划替代/囤货。Si5338：全表项目无一使用（UHSDR 提交 0 命中），属自研空白区。
2. **Tayloe 开关族谱**：mcHF=SN74CBT3253C、QCX=FST3253、SoftRock/uSDX=74HC4053，你用 **SN74CB3Q3253×2**（CB3Q：5V 容忍、更低 Ron/Cio，且双颗可分 RX/TX 或双通道）——选型比全场都新一档；上午已实测 CBTLV3253 的 Cio(OFF)（A 20.5pF/B 5.5pF），可与 CB3Q 数据手册对照确认裕量。
3. **正交 LO 路径全场特异**：其余全部走 Si570/Si5351 + ÷4（uSDX 用 800kbit/s I2C 相位调制做软件 DDS）；PSDR2.6.1 走 **Si5338（双 26MHz TCXO 参考）→ MC10EP52 ECL D 触发器链**。注意按上午结论：SY10/100EP52V 是 D 触发器而非 ÷2 芯片（÷2 是 EP32V）——÷2 需 D-FF 反馈接法，正交相位靠触发器链对称性保证，布局等长要严格。
4. **LPF 数值可直接抄作业**：(tr)uSDX/QCX 的逐波段 C0G+T37-2 表（见 §3）是 5W 级 Class-E 最成熟的公开数值；若 PSDR 后续加切换 LPF，注意 (tr)uSDX 的两条教训：锁存继电器抗振问题（震动误切换软件无感知）与磁环绕制密度对陷波点的 MHz 级影响（NanoVNA 校准）。
5. **PA 缺位提示**：PSDR2.6.1 当前 BOM 无功率级 FET（只见 SXB-2089Z/HMC482 增益块，且两颗均 EOL/Obsolete）。参考路线二选一：mcHF 线性（2×RD16HHF1，数字偏置，5–10W）或 uSDX/QCX Class-E（BS170/IRF540N + 74ACT00×3 并联驱动 + 50µH 扼流圈，效率 76–93%）。
6. **GPS 路线**：KiwiSDR 用分立 MAX2769B + 软件 GPS（Andrew Holme 方案）做频率驯服/TDoA；PSDR2.6.1 的 RXM-GPS-RM 模块（MT3337E）+ W3062A 无源天线是"省事路线"，可借鉴 KiwiSDR 的 GPS 驯服晶振思路提升频率精度。
7. **VNA 仍是独门**：13 个项目中仅 PortableSDR 血统（AD8302+阻抗桥）带 VNA/天线分析；TX-500 只有 SWR 监测、QCX+ 只有电压/功率/频率计。保持此差异化即可。
8. **性能天花板参照**：QSD 体制的天花板是 mcHF（-126dBm/300Hz、IP3≈+30dBm）与 Peaberry（两音 DR 99dB）；直接采样体制是 Hermes（16bit@122.88MSPS）与 TX-500（BDR 129dB）。PSDR2.6.1 若走 QSD+片内 ADC，动态范围受 12bit 片内 ADC 限制（未证实架构，仅提示核算）。

## 5. 未证实/未找到清单

- uSDX 原理图原件（网络 TLS 拦截；内容为文本复原）
- KiwiSDR ADC 具体型号（官方 PDF 只写 "LTC 14-bit 65 MHz ADC"；网传 LTC2208 与官方"$80 16bit/130MSPS 未采用"论述矛盾，不采信）
- HL2/Hermes/KiwiSDR/SoftRock 的完整 MDS/BDR 数值（未找到公开实测汇总）
- mcHF 新版 0.9 的混频器/codec 选型（Altium 未展开）
- QCX 阻塞动态范围（未找到）
