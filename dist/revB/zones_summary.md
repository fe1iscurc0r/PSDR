# rev-B 影响圈（自动生成，勿手改）


重跑：`python tools/revB_zone_closure.py`；源：`dist/netlist/PSDR_2.6.1_netlist.json` + `dist/fab/PSDR_2.6.1_placement.csv`。

传播规则：按网络一跳一跳扩；**参考网络不传播**（名字含 GND/电源/电压轨，或扇出 > 12）。被挡掉的网都列在下面，排除是可查的而不是假设。

| 区 | 种子 | 区内件数 | hop1 | hop2 | 包围盒（mm，贴装表原点） | 被挡参考网数 |
|---|---|---|---|---|---|---|
| U304_gain | U304 | 9 | 5 | 3 | x 7.9..16.0 mm, y 42.2..50.5 mm | 2 |
| DPDT_switches | U16/U24/U30 | 102 | 10 | 89 | x 0.0..96.2 mm, y 2.5..61.0 mm | 10 |
| HMC1023_lpf | U287 | 99 | 12 | 86 | x 0.0..96.2 mm, y 2.5..61.0 mm | 11 |

**三区并集 = 124 件；板上一共 391 件 ⇒ 影响圈外必须逐件不变的有 267 件**（对拍用 `dist/fab/PSDR_2.6.1_placement.csv`，这是"只动局部"的可判定验收）。

## U304_gain 区被挡掉的参考网（扇出前 12 个）

`GND`(261)、`+5V_AMP`(6)

## DPDT_switches 区被挡掉的参考网（扇出前 12 个）

`GND`(261)、`+3V3`(58)、`+3V3_CPU`(50)、`HALF_VCC`(23)、`5V_REG_ENABLE`(2)、`AMP_POWER`(2)、`FLIP-FLOP_POWER`(2)、`GPS_POWER`(2)、`LPF_POWER`(2)、`POWER_GOOD`(2)

## HMC1023_lpf 区被挡掉的参考网（扇出前 12 个）

`GND`(261)、`+3V3`(58)、`+3V3_CPU`(50)、`HALF_VCC`(23)、`LPF_5V`(13)、`5V_REG_ENABLE`(2)、`AMP_POWER`(2)、`FLIP-FLOP_POWER`(2)、`GPS_POWER`(2)、`LPF_POWER`(2)、`POWER_GOOD`(2)
