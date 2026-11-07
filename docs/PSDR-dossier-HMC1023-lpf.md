# Zone dossier：U287 HMC1023 LPF（rev-B 工单 §3/§7.4）

日期：2026-11-07。口径：填表不留空，拿不准写 `pending` 并标注等哪个门（G1/G2/G3 定义见
`docs/PSDR-revB-workorder.md` §1）。数据来源：`dist/revB/zone_HMC1023_lpf.csv`、
`dist/netlist/PSDR_2.6.1_netlist.json`、`docs/PSDR-HMC1023-pinmap-check.md`（2026-11-07 独立复核）、
`docs/PSDR-HMC1023-netlist.md`、`docs/PSDR-hmc1023-driver-plan.md`。

## 1. 模板六字段

| 字段 | 内容 | 状态/等哪个门 |
|---|---|---|
| 器件身份 | `HMC1023LP5E`，**原件已到手**（v01.0113，本地 `PSDR-build-artifacts/hmc1023.pdf`）；32 端子 + 散热盘逐脚与 Table 6 对齐（pinmap-check，2026-11-07 复核一致） | 已确认，无 pending |
| 封装能否替换 | 32 端子 + 散热盘（decal `T` 记 33、网表 32 个有网 + pin 29 VBG 悬空——手册标 "testing only"，悬空**正确**）。无引脚兼容的第二来源 ⇒ 换料即改封装布局，属重设计不是局部 | 结论已定；去留本身 **pending（等 G3）** |
| 现供电 | `LPF_5V`（6 个供电脚：2/4/16/21/22/23）经 Q208 开关，栅极 `LPF_POWER`=PE11 固件零驱动、R207 上拉默认关断。**VDDBG（28）在 2.6.1 只挂 C292 去耦、无供电**＝已记录的硬件缺口；rev-B 已把 `VDDBG` 并入 `LPF_5V`（U287.28/C292.1 改挂 71 号网），EDA 现场已补 +155 mil 连接；离线 revB 文件里该网仍有 2.506 mm 物理缺口待补铜 | 网表/手册已读实；离线文件补铜 **pending（等用户画线，走线归用户）**；PE11 驱动属固件，**不在本 dossier 排期（固件默认不碰）** |
| 隔直要求 | —（模板不适用；I 通道输出 18/19 经 C293/C294 交流耦合跨接到 Q 通道输入 30/31，Q 半边无外部馈入＝板上只用 I 通道，pinmap-check §2） | 已填 |
| 改动清单 | **保留 or 换成 6 段 LC：pending（等 G3 的同机 A/B 数字）**。已完成的改动只有 VDDBG 并网（见上）。校准时钟 CALCK 经 C283 接 Si5338 CLK1A，而固件只写 MULTISYNTH0、CLK1 未配置 ⇒ CALCK 依赖 NVM 上电状态，**pending（等 G2 台架实测 CLK1A）** | pending（G3；CLK1A 等 G2） |
| 参考实现 | **UHSDR 已实现**：`mchf-eclipse/hardware/uhsdr_hmc1023.c`，commit `c447c2e4`（2018-10-21，含手动细校准）；本仓校准序列构建器 + 主机测试已在 `tools/hosttest/hmc1023_seq.*`（无板阶段） | 已填 |

## 2. 区数据（实测，重跑可复现）

- 种子 `U287`；区内 99 件；一跳 14 件：`U287 C283 C292 C293 C294 R285 R286 R296 R297 U121 U15 U211 U298`；二跳 86 件。
- 一跳包围盒铺满全板（x 0–96.2 mm、y 2.5–61.0 mm）⇒ **不是局部**。
- 被挡参考网 11 条，含 `LPF_5V`(13 脚)。
- `U287` Bottom 面 (33.020, 14.986) mm；SPI 与 U15 数字电位器共总线（PB13/14/15），
  片选分离（`FILTER_CS` PB12 / `GAIN_POT_NSS` PE4），SDO 独占 MISO ⇒ 读回可行。

## 3. 硬约束

rev-B 范围定义 (c)：**只动一跳 14 件**，且只在决定去留这颗时动。G3 之前不动它（工单 §6）。
`U121/U15/U211/U298` 虽在一跳内，贴装/网络属硬约束；固件改动一律另立授权，不在本 dossier 内排期。