# VNA 通路：硬件是完整的，软件从来没走（2026-11-04）

从 `dist/netlist/PSDR_2.6.1_netlist.json` 逐网追出来的拓扑（全部**读得**）。
用途：把 #20 里"`vna_reflected` / `vna_through` 是空 case"这件事，落到"硬件到底有什么"。

## 1. 关键连接（网表实测）

| 从 | 到 | 经由 | 说明 |
|---|---|---|---|
| `U314.2` INPA | `RF_REF` | `C322`（串联隔直） | AD8302 的 **A 路 = 参考臂** |
| `U314.6` INPB | `RF_ANT` | `C309`（串联隔直） | AD8302 的 **B 路 = DUT 臂** |
| `RF_REF` 网 | `REF`（`PAD_1MM`）、`VNA-OUT`（SMA）、`R28`、`R321`、`C306` | — | 参考臂的 50 Ω 端接与测试点 |
| `RF_ANT` 网 | `DUT`（`PAD_1MM`）、`R29`、`R308` | — | DUT 臂的端接与测试点 |
| `U24`（`IMP_BRIDGE` 的 DPDT） | `C20/C21/C26/C27` → 桥臂 | 掷位 4/6/10/12 | 由 `IMP_BRIDGE_SWITCH_A/B`（U121.16/30）切换 |
| 桥路电阻 | `R22/R23/R25/R28/R29` | — | 阻抗桥的四臂/端接（值与接法见网表 CSV） |
| `U314.13` VMAG | `R312/R313` | — | 幅度输出 → MCU ADC |
| `U314.9` VPHS | `R310/R311` | — | 相位输出 → MCU ADC |

**所以 VNA 的硬件链路是完整的**：发射源 → `U30`（`TX_RF_SWITCH`）→ `U24` 阻抗桥 → `REF`/`DUT` 两臂 →
`C322`/`C309` 隔直 → `AD8302` 比较 → `VMAG`/`VPHS` → MCU。`REF`、`DUT` 是 **1 mm 焊盘**（不是 SMA），
两个 SMA 是 `ANT/VNA-IN` 与 `VNA-OUT`。

## 2. 软件侧（只读，`Source_F7/src/main.c`）

`signalPath()` 的七个枚举里，**`vna_reflected`(5) 与 `vna_through`(6) 都是空 case**（`:926-931`），
`default:` 也被注释掉（`:932-935`）⇒ **进入这两个态时，没有任何控制脚被写**，
`U24`/`U30` 保持上一次的状态。也就是说：

* 硬件上"桥 + 检波 + ADC 输入"都在；
* 软件上**没有任何一处**把开关切到 VNA 路径，也没有把 `VMAG/VPHS` 采回来算 S 参数。

这与 #20 的说法一致，而且更具体：**不是"VNA 没实现"，是"硬件有、固件两个分支是空的"**。

## 3. 与 2014 年作者自述的对照

`Documentation/PSDR2 Guide.pdf`（2014-09-28）里作者写 "**Whre is it controlled in code?**"、
"THEN WHAT HAPPENS?"，并说 R29-30 用于调斜率/中心点、R25-26 是 50 Ω 端接
⇒ 作者当年也只做到"硬件设计完"，软件这一页一直空着。两处独立来源对上了。

## 4. 复算

```bash
python -c "import json;d=json.load(open('dist/netlist/PSDR_2.6.1_netlist.json',encoding='utf-8'));\
print(d['nets']['RF_REF']);print(d['nets']['RF_ANT'])"
sed -n '918,940p' Source_F7/src/main.c
```
