# `signalPath()` 引脚状态表（只读固件，不改代码）

日期：2026-11-04。**这是一张读表，不是改法。** 依据：现基线 `Source_F7/`（= 上游 `PSDR_F7 @ ab2c8fd`）
的 `src/main.c` 枚举与 `signalPath()`（`:806-937`）、引脚定义在 `src/hal.c`（行号见下），
板上落点用 `dist/netlist/PSDR_2.6.1_netlist.json` 逐网核对。

口径：
* **读得** = 固件源码逐行 / 网表逐脚读出；**算得** = 由「固件符号 → GPIO → 网名 → 板上引脚」这条链推的；
* MCU 脚号是 **LQFP100 封装脚号**（网表里 `U121` 的 pin）；GPIO 名（PA0…）来自 `hal.c`；
  两端的对应由网名逐条对上，并且与已知六根开关线的既有结论一致，**未见冲突**——
  但严格意义上的「封装脚号 ↔ GPIO 名」出自 ST 数据手册，本仓没有收那份表，这里按上述链条标注。

---

## 1. 控制线总表（12 根，全部读得/算得）

| # | 固件符号 | `hal.c` | GPIO | MCU 脚 | 网名（网表实测） | 板上落点 |
|---|---|---|---|---|---|---|
| 1 | `AMP_SWITCH_A` | :98 | PA0 | U121.22 | `AMP_SWITCH_A` | `U16.3` |
| 2 | `AMP_SWITCH_B` | :100 | PE6 | U121.5 | `AMP_SWITCH_B` | `U16.7` |
| 3 | `IMP_BRIDGE_SWITCH_A` | :102 | PC1 | U121.16 | `IMP_BRIDGE_SWITCH_A` | `U24.3` |
| 4 | `IMP_BRIDGE_SWITCH_B` | :104 | PA6 | U121.30 | `IMP_BRIDGE_SWITCH_B` | `U24.7` |
| 5 | `TX_RF_SWITCH_A` | :110 | PB2 | U121.36 | `TX_RF_SWITCH_A` | `U30.3` |
| 6 | `TX_RF_SWITCH_B` | :112 | PA7 | U121.31 | `TX_RF_SWITCH_B` | `U30.7` |
| 7 | `AMP_POWER` | :115 | PE3 | U121.2 | `AMP_POWER` | `R2.1`（再经 R2 到功放供电开关） |
| 8 | `DAC_MUX` | :127 | PE4 | U121.3 | `DAC_MUX` | `U86.6`（`MAX4525` DPDT 模拟开关） |
| 9 | `TRX_SWITCH` | :191 | PC3 | U121.18 | `TRX_SWITCH` | `U18.6`、`U4.6`（两支 `MAX4525`） |
| 10 | `FILTER_S0` | :186 | PE10 | U121.40 | `FILTER_S0` | `U211.14`、`U298.14` |
| 11 | `FILTER_S1` | :188 | PD8 | U121.55 | `FILTER_S1` | `U211.2`、`U298.2` |
| 12 | `FIVE_VOLT_REGULATOR_ENABLE` | :205 | PE2 | U121.1 | `5V_REG_ENABLE` | `U85.3`（`ADP1613` 升压，`+5V_BOOST`） |

注：第 12 条的**固件符号名与网名不同**（`FIVE_VOLT_REGULATOR_ENABLE` ↔ `5V_REG_ENABLE`）——
这正是"核对以 MCU 脚号为锚、不以名字为锚"的那条纪律的又一个例子。

**没有对应的三根**：`MIXER_SWITCH_A`、`MIXER_SWITCH_B`、`MIXER_POWER` 在 `hal.c` 里**是注释掉的**
（定义 `:106-109`、`:117-118`；连 GPIO 初始化与初值也整段注释：`:528-540`、`:570-575`），
且 `MIXER_SWITCH_A/B`、`MIXER_POWER` **在 2.6.1 网表里不是网络名**
（实测 `NOT A NET`）⇒ 本板上不存在这三条控制网，不要按 PSDR2 老图去找它们。

---

## 2. 七个枚举态的实际引脚值（读得，逐行对应 `main.c`）

枚举：`recieve_no_filter=0`、`recieve_with_filter=1`、`transmit_no_amp_no_filter=2`、
`transmit_with_amp_no_filter=3`、`tramsmit_with_amp_with_filter=4`（原拼写）、`vna_reflected=5`、`vna_through=6`。

| 态 | 代码行 | AMP_POWER | 5V_REG_EN | AMP_SW A/B | IMP_BR A/B | TX_RF A/B | DAC_MUX | TRX_SWITCH | FILTER_S0/S1 |
|---|---|---|---|---|---|---|---|---|---|
| 0 `recieve_no_filter` | `:823-853` | 1（关） | 0（关） | 0/1（旁路） | 0/1（旁路） | 1/0 | 0（喇叭） | 0（收） | 1/0 |
| 1 `recieve_with_filter` | `:855` **空 case，落到 2** | 1 | 0 | 0/1 | 0/1 | 1/0 | **1（RF）** | **1（发）** | 1/0 |
| 2 `transmit_no_amp_no_filter` | `:858-889` | 1 | 0 | 0/1 | 0/1 | 1/0 | 1（RF） | 1（发） | 1/0 |
| 3 `transmit_with_amp_no_filter` | `:891-922` | **0（开）** | **1（开）** | **0/1（仍是旁路）** | 0/1 | 1/0 | 1（RF） | 1（发） | 1/0 |
| 4 `tramsmit_with_amp_with_filter` | `:923-925` | — 不写 — | — | — | — | — | — | — | — |
| 5 `vna_reflected` | `:926-928` | — 不写 — | — | — | — | — | — | — | — |
| 6 `vna_through` | `:929-931` | — 不写 — | — | — | — | — | — | — | — |

`default:` 分支**被注释掉了**（`:932-935`）⇒ 传入枚举外的值不会有任何报错，也不写引脚。

---

## 3. 这张表暴露的四件事（全部只读得出，不做改动建议）

1. **态 1 与态 2 完全相同**：`recieve_with_filter` 是空 case，直接落进 `transmit_no_amp_no_filter` 的代码，
   于是"带滤波接收"实际会被设成 **`TRX_SWITCH=1`（注释原文 "Both TX/RX Muxes set to TX"）、`DAC_MUX=1`（RF）**——
   即选了"带滤波接收"，硬件被切到了发射/射频音频那一路。**这是观察，不是修法。**
2. **四个有实现的态里，`FILTER_S0/S1` 全是 `(1,0)`**（`:851-852`、`:886-887`、`:919-920` 三处写点）。
   ⇒ 固件**永远不会**走到滤波 mux 的其它档位；`recieve_with_filter` 这个名字对 mux 没有任何效果。
   这与外接滤波插槽（`E_FILT_RF/IF_P/N`）的结论一致：想验证外接滤波，只能**硬件跳线**选档，不能指望软件。
3. **态 3 加电但不接通放大**：`AMP_POWER=0`（开）、`5V_REG_ENABLE=1`（开），而
   `AMP_SWITCH_A=0 / B=1` 仍是旁路值，**同一段代码上方注释却写着 "//Amp relay set to on"**（`:900`）。
   这就是 #16 里"前放没被接进通路"的代码级证据（行号可引）。
4. **态 4/5/6 什么都不写**：进入这三个态时，所有控制脚**保持上一次的状态**。
   对 VNA 两个态尤其要注意：它们既不开 VNA 路径的继电器，也不切滤波 mux。

---

## 4. 与 rev-B 工作单的接口

* 控制面预算（`docs/PSDR-revB-workorder.md` §4）：`FILTER_S0/S1` 只有两位 ⇒ 至多 4 档；
  想做 6 段必须另找地址线（`U30` 的 pin 6 空掷位是一条候选），**而固件冻结意味着任何新档位都只能靠跳线或外部逻辑**。
* 态 3 的"加电不接通"与态 1 的"滤波接收被切到 TX"这两条，已可写进 M3 的**观测判据**：
  板子到手后先量这 12 根线在上电默认态与 `signalPath(3)` 下的电平，与本表对拍；
  对不上就说明固件/板子之间有第三只手（跳线、飞线、或烧的是另一版 hex）。

## 5. 复算

```bash
# 控制线定义
grep -n "AMP_SWITCH_A\|IMP_BRIDGE_SWITCH_A\|TX_RF_SWITCH_A\|AMP_POWER\|DAC_MUX\|TRX_SWITCH\|FILTER_S0\|FIVE_VOLT_REGULATOR_ENABLE" Source_F7/src/hal.c
# 各态写入
sed -n '806,937p' Source_F7/src/main.c
# 网表落点（任一网名 → 板上引脚）
python -c "import json;d=json.load(open('dist/netlist/PSDR_2.6.1_netlist.json',encoding='utf-8'));print(d['nets']['FILTER_S0'])"
```
