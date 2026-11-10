# PSDR 替代件/采购研究记录（2026-11-10，fork-only）

范围：#55 U304 前放替代、#56 Amp 板备料、#59 GPS 国产降本、#60 MASWSS0129 T/R 开关替代；
§7 附记当日 100 W 开关功放设想的口径结论（设想已搁置）。
口径：**只研究，不采购、不改板、不动固件**；测试板（2.6.1 revB）已发货，DFM 不再追。
证据分级：原件级（原厂 PDF/官网产品页）> 协议文档级 > 分销快照级 > 社区转述级；查不到写"未证实"。
结论性表述已同步进 `docs/PSDR-alternates-proposal.md` §2.2/§4.1；本文存证据细节与来源。

## 1. U304 前放替代（#55）——收敛到两只，都要 R6 DNP

结论表见提案 §2.2。这里记证据：

**原件级手册（已存档 `datasheets/`，URL/sha256 见其 README）**：

- **ZDH3020 V1.2.3**（北京中电宏业，GaAs MMIC）：5MHz–3000MHz；3–8V 单供、典型 5V；
  IDD 60–120mA 可调（R1=N/C→110mA，15K→90mA，5.1K→60mA）。**5–300MHz 应用电路段：
  增益 22dB、平坦度 ±0.1dB、NF≤1.7dB、S11/S22 −18dB、P1dB 21dBm、OIP3 37dBm**；
  900–3000MHz 段增益 17–18dB、NF 2.4–3.1dB。SOT-89，脚3=RFOUT/VDD（输出偏置），极限 VDD 10V。
  HF 段（0.1–30MHz）落在 5–300MHz 应用电路覆盖内，是全部候选中 HF 参数最好的。
- **GALI-4+ REV. T**（Mini-Circuits，InGaP HBT 达林顿）：**保证规格 DC–4GHz**（低频下限由外部
  隔直电容决定）；增益 14.4dB@0.1GHz；NF 4.0dB@1GHz；P1dB +17.5dBm、OIP3 +34dBm；
  65mA 时器件电压 +4.2/+4.6/+5.5V（min/typ/max）⇒ **5V 轨可用**；Rbias 必需，
  5V 时约 (5−4.6)/0.065 ≈ **6.2Ω**（手册给 7–20V 的表，5V 需外推，取 1% 精度）；极限电流 85mA。
  SOT-89（DF782），脚1 需外部隔直、脚3=RF-OUT & DC-IN。
- **ZDH3003 V1.2.3**：5MHz–3GHz、17dB@5–300MHz、NF≤2.4，全面弱于 ZDH3020，同厂备胎。
- **ZDH3157 V1.2.0**：手册 **500MHz–3GHz** ⇒ HF 排除（官网表格写"DC"是营销错误，留档作证）。

**通用阻断（本轮关键发现）**：GALI/ZDH/TQP36918x/SBB 全部是输出脚偏置 + 输入脚要求外部隔直；
本板 `RF_AMP_IN` 节点有 `L11(220µH)`+`R6` 从 `+5V_AMP` 馈入直流（dossier U304 §1）⇒
**任何现代增益块换上去都必须 R6 DNP**，偏置改经现有 `L19` 从输出侧注入。R6 DNP 是 BOM 级改动、
不动走线，在允许范围内；但"免改版直接换"不存在。GALI-4+ 还要把 Rbias 按 5V 重算进偏置路径。

**排除项**：TQP7M9101（SXB-2089Z 官方后续，400MHz 起步）；GALI-5+（LCSC 页工作电压 4–4.9V，
5V 轨超限）；国产 SOI/GaAs 其它标"DC"件一律以 PDF 复核（中电宏业官网表格不可信）。

**价格（全部未证实，采购前询价）**：ZDH3020/ZDH3003 官网只留 sales@cemaxrf.com / 010-88420275，
无公开价；GALI-4+ 仅见 DigiKey 专题页起价 $42.17（快照 2024-06-06，非现价）；
TQP369182 官网 429 取不到手册，同族 TQP369184 华秋快照"库存 0 可订货 ¥13.195@1+"（分销级）。

## 2. MASWSS0129 T/R 开关替代（#60）——ZDH5438 满足"性能更好"，属路线 B 延后

用户口径："性能更好的话肯定要做"。本轮判定：**HF 段性能确实更好，但不是 pin 兼容，
随"改版范围到时候再看"延后**，当前发货板不动。

**ZDH5438 V1.2.0 原件级**（`datasheets/ZDH5438_v1.2.0.pdf`）：

| 维度 | ZDH5438 | MASWSS0129（公开值/dossier） |
|---|---|---|
| 频段 | DC–6000MHz | DC–6GHz |
| 结构 | DPDT，互补双控制 V1/V2 | DPDT，13 焊盘 |
| 封装 | **DFN1.5×1.5-6**（1 ANT1/2 V2/3 ANT2/4 RX/5 V1/6 TX） | 13 焊盘 ⇒ **不 pin 兼容** |
| 隔离@10MHz | **68–72dB**（四通路） | 无 HF 公开值；2.4GHz 43dB |
| 隔离@500MHz | 43–48dB | — |
| 插损 | 1.0dB@10MHz、0.6dB@500MHz、1.0–1.1dB@2.5GHz | 0.70dB@2.4GHz |
| P1dB/OIP3 | 37dBm@2.4GHz/5V、51dBm@2450MHz | — |
| 控制电平 | 高 +1.8…+5V、低 0…+1.0V；极限 6V | 板上控制轨实测计算 2.898–3.012V ⇒ 兼容 |
| 切换时间 | 55ns（ON/OFF） | — |

真值表：V1=1,V2=0 → ANT1-RX + ANT2-TX 通；V1=0,V2=1 → ANT1-TX + ANT2-RX 通。
应用电路要求四个 RF 口各串 10nF 隔直。链路带宽由 ADE-2ASK 混频器限到 ≈1GHz（提案 §4.3），
HF 只需 0.1–30MHz ⇒ 6GHz 能力远超所需，隔离度才是真收益。

**若将来采用（全部延后）**：①封装/布局局部改版（U16/U24/U30 三处）；②固件冻结 ⇒
`signalPath()` 控制脚映射必须先逐脚重核（见 `docs/PSDR-signalpath-pinmap.md`）；③重测插损/隔离。

**其它检索结果**：国产 SOI DPDT 全部 HF 排除——FM1022/LX1022（矽源特，619–5925MHz）、
MXD8646A（0.4–3.8GHz，LCSC 270823）、SKY5A1007（0.4–5.9GHz）。
MACOM 官网 `DataSheets/MASWSS0129.pdf`（及 0143/0202）2026-11-10 复核全部 404，撤档确认，
误存的三个错误页已删。路线 A 原货（作者存量/Rochester/贸易商）**未证实**（检索被 SEO 页污染，
无可核库存/价格）。

## 3. GPS 国产降本（#59）——ATGM336H-5N31 过全部兼容门（需一次性配置）

### 3.1 板侧事实（网表实测，`dist/netlist/PSDR_2.6.1_netlist.csv`）

原件 U185 = **Linx RXM-GPS-RM-T**（15×13mm LCC-22，2016 BOM $20.38；TE 文档断链，无原厂手册）。
连接：脚12 VCC 经 **Q126（IRLML6401 P-MOS）开关从 +3V3_CPU 供电**；脚11 VBACKUP ← `VBAT_BKP`
（U172 MCP1802 3V3 LDO，与 STM32 VBAT 共轨）；脚8 \RESET ← `GPS_RESET`（U121 脚62；
网表脚名 PD15，`.ioc` 标签 PE15，两处不一致，GPS 休眠本轮不追）；脚4 TX/脚5 RX 经 R201/R200
串阻；脚3 1PPS 经 R202；脚19 RFIN 经 C186 接 **W3062A 无源陶瓷贴片天线**。
板上有 `GPSTX`/`GPSRX`/`GPSR` 三个 1mm 测试点 ⇒ **可在不改固件的情况下经 UART 配置模块**。

### 3.2 固件门（已核，冻结不动）

`Source/src/TinyGPS.c:29-30` 只认字面量 **"GPRMC"/"GPGGA"**；9600 baud；`hal.h` MEDIATEK_MODULE；
GPS UART 初始化被注释（功能休眠）。⇒ 国产模块必须能输出 **GP  talker** 语句。

### 3.3 候选判定

**ATGM336H-5N31（杭州中科微 AT6558，LCSC C90770）——首选**：

- 规格（分销/手册页级）：GPS+BDS 双模，10.1×9.7mm SMD，2.7–3.6V，25mA@3.3V，UART/I2C，
  默认 9600，NMEA0183，跟踪 −162dBm，2.5m CEP50；支持有源/无源天线、天线检测与短路保护、
  PPS、VBAT 备份（与板侧 Q126 开关供电、VBAT_BKP、无源天线三条都对得上）。
- **talker 门**：双模默认输出 **GN** 语句（社区实测多处一致）⇒ 固件不认。解法（CASIC 协议，
  同族协议文档级 + 社区实测，**中科微原厂 CASIC PDF 未取到**）：
  发 `$PCAS04,1*18`（单 GPS）→ 输出 GP 语句；`$PCAS00*01` 保存进 Flash（断电不丢）；
  可选 `$PCAS05,9` 切单 GPS NMEA0183 v2.2 协议。经板上 GPSTX/GPSRX 测试点一次性配置即可，
  **不需要改固件**。配置后实际语句仍需实物复核（未证实项）。
- 价格（LCSC 目录页快照，2026-11-10 检索，非实时）：
  ¥19.72@1+ / 17.52@10+ / 16.39@30+ / 12.92@100+ / 12.15@1000+，库存 4969；
  另一快照 ¥20.47@1+ / 13.41@100+，库存 2394。对比原件 $20.38（2016 价）⇒ **约半价以下**。
- 封装差：10.1×9.7mm ≠ 15×13mm LCC-22 ⇒ **不是 drop-in**，换装属改版范围（延后）；
  本轮只完成选型与兼容门。-5N-31 是官方推荐变体（Flash/TCXO/天线检测）。

**UM220-IV NL（和芯星通 UFirebird）——备选，不推荐**：BDS B1+GPS L1（官网另列 Galileo E1），
支持单系统独立定位，NMEA **V4.1**，市场参考价 **¥40–60**（分销页）。双模 talker 行为无手册级
证据（V4.1 倾向 GN 前缀），单 GPS 模式是否输出 GP 未证实 ⇒ 兼容门没过。
UMD220-IV NL 是单北斗变体（BD 语句）⇒ 直接排除。

**剩余缺口**：中科微原厂 CASIC 协议 PDF；配置后实物语句复核；国产 GNSS 天线选型（W3062A 无手册）；
改版 footprint。GPS 功能在固件里休眠，以上都不阻塞当前发货板。

## 4. Amp 板备料核查（#56）——LM3410 在产；HMC482 停产无官方替代

Amp 板（`Hardware/Amp/`）是作者的**实验性外接增益板**，不在 2.6.1 订货范围。
原理图 PDF 作者原注："两 HMC482 串联供电"、"LM3410 做恒流源（电压约 6V）"、
"电感值只是猜的"、"主板这些脚上已有隔直电容"。R4/R5=1R74 设流（LM3410 FB 基准 200mV ⇒ ≈115mA，
与 HMC482 的 110mA 档一致）。

| 件 | 状态（2026-11-10） | 依据 |
|---|---|---|
| **HMC482ST89**（U1/U2） | **ADI 官网确认 Obsolete，无官方替代**；SiGe DC–5GHz、20dB、+6…+12V、P1dB +22dBm、OIP3 +36dBm | analog.com 产品页（原件级）；Partstat ADI EOL 表无 HMC482 行；华秋"国内交货 0"；dzsc 贸易商声称有 HMC482ST89ETR 现货但**无可核价格（未证实）** |
| **LM3410XMF/NOPB**（U3） | **TI Active Production**（SOT-23-5），无需替代 | ti.com 可订货表（原件级）；LCSC C 编号/价格检索被贸易商页污染，**未证实**，建议 TI 官网或授权分销询价 |

**替代方向（若真要做这块实验板）**：约束是 ~115mA 恒流馈电 + SOT-89。GALI-4+ 极限 85mA，
直接顶上去会过流 ⇒ 必须改 R4/R5 设流（BOM 级）才谈得上换；没找到 pin 兼容件。
作者 BOM 自相矛盾已在 `Amp_Board_v1_BOM_flat.csv` 标注（L3 料号 10U/描述 15µH；
L1/L2 料号 10U/值 2u2；R4/R5 值 1R74/描述 0603 但料号 0805）——做板前先向作者口径对齐。
**本轮结论：备料核查完成；这块板是否做、何时做，等用户决定。**

## 5. 价格快照汇总（全部非实时，采购前复核）

| 件 | 价格 | 渠道/URL | 快照日期 | 级别 |
|---|---|---|---|---|
| ATGM336H-5N31 | ¥19.72@1+…¥12.15@1000+（另一快照 ¥20.47@1+） | LCSC C90770，list.szlcsc.com/catalog/940.html | 2026-11-10 检索 | 分销快照 |
| UM220-IV NL | ¥40–60（市场参考价） | corechipinc.com 分销页 | 2026-11-10 检索 | 分销参考 |
| GALI-4+ | 起价 $42.17 | digikey.cn Mini-Circuits 专题页 | 页面快照 2024-06-06 | 旧快照，非现价 |
| TQP369184 | ¥13.195@1+，库存 0 可订货 | hqchip | 2026-11-10 检索 | 分销快照 |
| ZDH3020 / ZDH5438 | 无公开价 | cemaxrf.com 只留销售联系 | 2026-11-10 | 未证实 |
| HMC482ST89 | 无可核价 | 贸易商声称现货 | 2026-11-10 | 未证实 |
| LM3410XMF/NOPB | 未取到 | TI 在产；LCSC 未证实 | 2026-11-10 | — |

## 6. 未证实清单（下一步要仪器/实物/询价才能闭环）

1. ZDH3020/GALI-4+ 在 0.5–30MHz 的实测增益/NF（G3 门）；+5V_AMP 轨压实测（G2 门）。
2. U304 实装身份（G1 门）：SXB-2089Z 还是 HMC482，靠实物丝印/作者记忆。
3. ATGM336H 配置后实际 talker 语句、中科微原厂 CASIC 协议 PDF。
4. ZDH5438 若采用：三处布局改版 + signalPath() 逐脚重核 + 重测（全部随改版范围延后）。
5. ZDH3020/ZDH5438 询价；GALI-4+ 现价；HMC482 原货渠道真伪。
6. GPS_RESET 的 MCU 脚位两处记录不一致（网表脚62/PD15 vs .ioc PE15）。

## 7. 100 W PWM/Class-E 功放设想（2026-11-10 讨论，当日搁置）

用户与作者邮件里讨论的功放设想；**只存档结论，不采购、不设计、不改板**（用户当日明确"先不用管，目前做不起来"）。

**设想要点**（用户原话）：STM32F746 定时器+DMA 出 PWM → 栅极驱动 → Class-E MOSFET；SSB 用 PWM 占空比直接做包络；2–35 MHz、100 W 目标；自称 90% 效率、-45 dBc；靠 APD+DPD 把 -33 调到 -45；成本 300–500 元。

**口径更正（本轮关键）**：设想里的 **-45 dBc 指三阶互调（IMD3），不是杂散**。最初评估按 FCC §97.307(d) 的短波杂散限值（<30 MHz、2003 年后安装 ≥43 dB 低于基波；-30 dB 仅是"2003 年前安装且平均功率 <5 W"的豁免档）——**指标用错了**：

- 杂散限值管的是谐波/杂散域；IMD3 的 `2f1−f2`、`2f2−f1` 落在主信号旁几 kHz，属带外产物。FCC 对 splatter 只有定性要求（§97.307(b)：不得产生 splatter/键控干扰邻频），**没有 -43 dBc 这个数字**；国内的"43+10lg(PEP) 或 50 dBc 取较低"同属杂散域，同样不适用。
- 因此 KX3 的 -30 dBc（若指两音 IMD）与 -45 dBc **不矛盾**：前者是便携机常见档位，后者是高出一大截的目标。

**IMD3 量级（两音法，相对 PEP）**：

| 水平 | IMD3 |
|---|---|
| 商用短波机典型 | -30…-36 dBc |
| 干净机型 | ≈ -40 dBc |
| **-45 dBc** | 很好（比 -30 好 15 dB ≈ 互调功率低 ~32 倍） |
| uSDX 类 Class-E QRP | 常见 -25…-30 dBc |

**结论**：-45 dBc IMD3 本身是**高目标**（不是法规底线），难点在"90% 效率 + -45 dBc"的组合：Class-E/PWM 非线性，IMD3 天然在 -25…-30 档，全靠 APD/DPD 的环路精度、带宽与记忆效应补偿，效率-线性-带宽互相拉扯。对 100 W 短波功放，-45 dBc 属"很好"档。

**比较前要统一的口径**：相对 PEP 还是相对单音（差 6 dB）；两音间隔（ARRL 常用 700 Hz/1 kHz，间隔变 IMD 也变）；测点在天线口还是功放级。

**未证实**：KX3 的 -30 dBc 官方原件——Elecraft 官网改版后规格页为 JS 渲染，PDF 链接与 Wayback 均未取到；按便携机常见档位对待，待补原件后核对。

## Sources（本轮检索，2026-11-10）

- [ATGM336H-5N NMEA 解析与移植要点（GN 语句坑、引脚表）](https://m.blog.csdn.net/weixin_29195615/article/details/165563757)
- [激光雷达授时：PCAS04,1 切单 GPS 实测出 GPRMC](https://m.blog.csdn.net/weifengdq/article/details/106412016)
- [Air530Z 设计指导手册（CASIC PCAS04/PCAS05 协议字段）](https://www.cnblogs.com/luat/p/14667102.html)
- [DX-GP21 教程：PCAS00 保存配置到 Flash](https://blog.csdn.net/weixin_48829767/article/details/158892643)
- [ATGM336H-5N 用户手册（sekorm 镜像页）](https://www.sekorm.com/doc/2227444.html?p10=7&p11=1096)
- [ATGM336H-5N 介绍（天线检测 GPTXT、无源/有源）](https://www.cnblogs.com/WENG123/p/17788896.html)
- [LCSC 卫星定位模块目录（C90770 价格/库存快照）](https://list.szlcsc.com/catalog/940.html)
- [ATGM336H-5N31 商品页（JS 混淆，价格取自目录快照）](https://item.szlcsc.com/940720.html)
- [UM220-IV NL 官网产品页](http://www.unicorecomm.com/products/detail/25)
- [UM220-IV NL 分销页（市场参考价 ¥40–60）](https://www.corechipinc.com/product/%E5%B7%A5%E8%A7%84%E7%BA%A7%E6%8A%97%E5%B9%B2%E6%89%B0GNSS%E5%AF%BC%E8%88%AA%E5%AE%9A%E4%BD%8D%E6%A8%A1%E5%9D%97.html)
- [TI LM3410 可订货表（Active Production）](https://www.ti.com/lit/gpn/LM3410)
- [TI LM3410XMF/NOPB 产品页](https://www.ti.com.cn/product/cn/LM3410/part-details/LM3410XMF/NOPB)
- [ADI HMC482 产品页（Obsolete）](https://www.analog.com/en/products/hmc482.html)
- [华秋 HMC482（国内交货 0）](https://m.hqchip.com/ic/HMC482/)
- [dzsc 贸易商 HMC482ST89ETR 声称现货（未证实）](https://m.dzsc.com/product/1186584-2022122815835609.html)
- [Partstat ADI EOL 表（无 HMC482 行）](https://blog.partstat.com/analog-devices-eol-notices/)
- [DigiKey Mini-Circuits 专题页（GALI 族起价旧快照）](https://www.digikey.cn/zh/product-highlight/m/mini-circuits/monolithic-amplifiers)
- [47 CFR §97.307（Cornell LII，§7 的 FCC 原文）](https://www.law.cornell.edu/cfr/text/47/97.307)
- [ITU-R SM.329-7 Spurious emissions（杂散域口径）](https://www.itu.int/dms_pubrec/itu-r/rec/sm/R-REC-SM.329-7-199707-S!!PDF-E.pdf)
- [发射设备杂散域发射功率限值要求（摘录页，标准号待核）](https://m.renrendoc.com/paper/350770220.html)