# Zone dossier：三片 DPDT（U16/U24/U30，rev-B 工单 §3/§7.4）

日期：2026-11-07。口径：填表不留空，拿不准写 `pending` 并标注等哪个门（G1/G2/G3 定义见
`docs/PSDR-revB-workorder.md` §1）。数据来源：`dist/revB/zone_DPDT_switches.csv`、
`dist/netlist/PSDR_2.6.1_netlist.json`、`docs/PSDR-external-findings-2026-11-03.md` §1.3、
`docs/PSDR-open-data-gaps.md` #4、`docs/PSDR-signalpath-pinmap.md`。

## 1. 模板六字段

| 字段 | 内容 | 状态/等哪个门 |
|---|---|---|
| 器件身份 | 网表/BOM 写 `MASWSS0129TR`（MACOM RF DPDT）；但实购到底是 CBTLV 还是 CB3Q 两条来源打架（external-findings §1.3），原厂 PDF 取不到，真值表停在**镜像级** | **pending（等 G1）**：身份与真值表不确认，`signalPath()` 的档位解释全部悬空 |
| 封装能否替换 | **不能随意换**：13 焊盘；控制脚数与真值表必须与现封装一致，否则固件 `signalPath()` 全错。换封装＝同时改固件映射，超出"局部"定义 | 结论已定；若 G1 确认实购与网表不符，重评 **pending（等 G1）** |
| 现供电 | `+3V3_CPU`（网表实测）。轨压**算得** 2.898/3.012 V（R113 383K/402K 冲突 × FB 0.6 V）；MASWSS0129 镜像资料控制高电平 ≥ +2.9 V ⇒ 余量约 0.1 V | **pending（等 G2 实测轨压与控制脚实际电平）** |
| 隔直要求 | —（模板不适用；RF 通路隔直由各串联电容承担：`C13 C20 C21 C26 C27 C303 C305 C306 C35`，均在一跳内实测在位） | 已填 |
| 改动清单 | **`U30` pin 6 = 空掷位**（2026-11-07 网表复核：U30 只有 12 脚有网，pin 6 不在任何网内）⇒ 多一路可自由接的掷位，是 6 段带通选路预算的唯一现成资源。其余改动 **pending（等 G1 真值表 + G3 子板 A/B 数字）** | 空掷位已读实；其余 pending（G1+G3） |
| 参考实现 | 真值表与互补驱动缺口清单：`docs/PSDR-open-data-gaps.md` #4；逐 case 引脚矩阵：`docs/PSDR-signalpath-pinmap.md`（12 线 × 7 态，含态 1 落进发射分支、态 3 加电仍旁路） | 已填 |

## 2. 区数据（实测，重跑可复现）

- 种子 `U16/U24/U30`；区内 102 件；一跳 13 件：三片 + `C13 C20 C21 C26 C27 C303 C305 C306 C35 U121`；二跳 89 件。
- 一跳包围盒铺满全板（x 0–96.2 mm、y 2.5–61.0 mm）⇒ **不是局部**：射频路径每一跳都是下一级输入。
- 被挡参考网 10 条：`GND`(261)、`+3V3`(58)、`+3V3_CPU`(50)、`HALF_VCC`(23) 及 6 条 2 脚电源使能网。
- 三片均 Top 面、x=16.002 mm 一列：U16 y=44.958、U24 y=36.830、U30 y=28.702。
- 控制网（工单 §4）：`AMP_SWITCH_A/B`→U16.3/7，`IMP_BRIDGE_SWITCH_A/B`→U24.3/7，`TX_RF_SWITCH_A/B`→U30.3/7。

## 3. 硬约束

rev-B 范围定义 (b)：**只动三片各自的一跳邻居（13 件）**，且只在换封装/改掷位时动。
二跳 89 件与区外 262 件逐件不变；`U121` 虽在一跳内，MCU 贴装/网络属硬约束，不得借"一跳内"改它。