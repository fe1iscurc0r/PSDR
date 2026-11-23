# G3 子板纸面设计：六段可切换 LC 带通（插 E_FILT 排针，不改主板）（2026-11-23）

目的：关掉 rev-B 的 **G3 门**——"带通前端到底比 HMC1023 好吗"，用**完全不动主板**的方式先测出来。
本文件是**纸面设计**，不依赖作者/板子/仪器；板子+仪器（NanoVNA/信号源）到位即可照做 A/B。
口径：**读得**=网表/手册；**算得**=公式推；**外部断言级**=竞品表，**只作起点、须仿真/NanoVNA 复核**，绝不直接当设计值（`PSDR-revB-workorder.md` §0.5、§6）。

## 1. 接口与选档（不改固件）

- 主板已有外接滤波插槽：`E_FILT_RF_P/N`（射频段）+ `E_FILT_IF_P/N`（中频段），差分。
- HMC1023 的 mux 档位 `ch=(S1<<1)|S0`，**ch0 = 外接滤波排针**（作者实测真值表，`#16` 6756908658）。
- 但固件 `FILTER_S0/S1` 三处写点恒为 `(1,0)`（=ch1 bypass），**软件永远选不到 ch0**（D-05）。
  ⇒ 子板用 **ch0** 只能靠**硬件跳线**把 `FILTER_S0/S1` 这两根线拉到 `(0,0)`，
  且**不许拿信号顶 MCU 推挽输出**：跳线串在 mux 控制脚与 MCU 之间，或断开 MCU 驱动（见 §5 风险）。
- 子板自己选 6 段：固件冻结 ⇒ **板载波段开关/跳线**（手动），不指望软件。

## 2. 波段计划（覆盖 PSDR 调谐范围）

PSDR 收/发 2.5–175 MHz；本 G3 只测 **HF + 6 m**（2 m 前端本就不行，NEXT-REV-IDEAS）。6 段重叠：

| 段 | 通带 (MHz) | 对应业余波段 | 备注 |
|---|---|---|---|
| B1 | 0.1–1.8 | 160 m | 中波边缘，注意 LO 出界（D 条：0.5–1.7 MHz 混频器 LO 受限） |
| B2 | 1.8–4 | 160/80 m | |
| B3 | 4–8 | 40/30 m | 含 7 MHz |
| B4 | 8–15 | 20/17/15 m | |
| B5 | 15–30 | 15/12/10 m | 含 21/24/28 |
| B6 | 30–60 | 10 m + 6 m | 含 50/54 |

## 3. 每段拓扑（起点，须复核）

- **拓扑**：7 阶 Chebyshev 带通（mcHF 即"7 阶 LC BPF×4 继电器重叠波段"，是本仓最贴近的现成架构）。
  纹波取 0.5 dB、通带按 §2 边带、端接 50 Ω（差分→巴伦，主板混频器侧本就带 `WBC2-1TL` 1:2 巴伦）。
- **综合方法**（不抄竞品值，自己算）：标准 Chebyshev BPF 表 → g 值 → 按 f0/BW/Z0 反归一化；
  用 `qucsstudio`/`RFsim99`/`AADE` 或 `scikit-rf` 跑一遍，**NanoVNA 实测 S21/S11 校准**。
- **竞品起点表（外部断言级，仅参考，禁止直接当设计值）**：
  - mcHF：7 阶 LC BPF×4 继电器（`github.com/m0nka/mcHF`，Altium+Gerber rev6/7/8）。
  - **Hermes-Lite 2 N2ADR 滤波板**：6× TX LPF（160–10 m）+ 3 MHz RX HPF + SWR 桥，**原理图/BOM/KiCad/Gerber 全公开**（`james.ahlstrom.name/hl2filter/`）——**最值得直接参考的"可切换滤波板"实物**，含 630 V NP0 1206 电容建议。
  - (tr)uSDX 逐波段 LPF：20 m=L11 400 nH(10T/T37-2)+L12 196 nH(7T)+C 68/470/150 pF…（`dl2man.de …v1.0n.pdf`）。
  - QCX+ 逐波段 BOM（`qrp-labs.com/images/qcxp/manual1.03.pdf`）。

## 4. 切换与器件

| 项 | 选型 | 理由 |
|---|---|---|
| 切换 | **信号继电器（磁保持优先）** | 波段选择是低频人工事件，ms 级不痛；插损最低、HF 隔离最高、无 Ron·Coff 极点（`scope §7.3` 结论：能慢的用继电器） |
| 备选 | RF 低阻 CMOS（1 Ω 档）或保留 GaAs | 仅当要 µs 级（QSK/VNA 快扫）；G3 子板是 RX 波段选择，不需要 µs |
| 控制 | 6 段 → 3 位译码（或 6 根单刀）；**板载拨码/旋钮** | 固件冻结，软件不可控（§1） |
| 隔直 | 每个 RF 口按器件手册加隔直 | 同主板上 modern 件要求 |

## 5. 风险（竞品踩过的坑，写进验收）

1. **继电器误切**：(tr)uSDX 明确警告"震动会误切锁存继电器，软件无感知"——磁保持虽省电但要**上电校验回读**当前档。
2. **磁环绕制密度**：(tr)uSDX 警告"10 m 4 匝密绕 vs 均绕差 5 MHz 陷波点"——电感必须**绕法一致 + NanoVNA 逐只测**。
3. **插损 vs 灵敏度**：带通有插损（mcHF 每段 ~1–2 dB），会吃掉一点灵敏度；G3 的 A/B 就是量"动态范围收益 > 插损代价"。
4. **顶 MCU 推挽**：硬件跳线选 ch0 时，别用跳线直接和 MCU 输出打架；串电阻或断开驱动。

## 6. A/B 验收（与 HMC1023 同机对比，最小测量集）

同一台机器、同一天线口、同一信号源，三态对比：**(i) Bypass、(ii) HMC1023 +20 dB、(iii) 子板带通**：

| 指标 | 怎么测 | 期望 |
|---|---|---|
| MDS / 灵敏度 | 步进衰减到"刚好看见瀑布信号"，记 dBm | 子板 ≤ HMC1023（-105…-110 dBm 基线，README 实测） |
| 动态范围 / 阻塞 | 带内有用信号 + 带边强台（如 7 MHz 有用 + broadcast 强台），看有用信号还看得见吗 | 子板应显著优于 bypass；与 HMC1023 比 |
| IMD3（两音） | 700/1500 Hz 双音或两个等强载波，看三阶产物 | 记录 dBc，**别拿杂散指标去套**（IMD3≠spurious，`research §7`） |
| 每段 S21/S11 | NanoVNA 逐段扫 | 通带纹波、边带衰减、回损达标 |
| 谐波（若兼作 TX 滤波） | 频谱仪看 3 次谐波 | 若子板兼 TX 滤波，须 ≤-40 dBc（rev-B D6） |

## 7. 交付物（板子+仪器到位后）

- 子板原理图 + BOM + Gerber（可用 N2ADR 板做模板）；
- 逐段实测 S21/S11（落 `evidence/g3_subband_*.csv`）；
- 三态 A/B 数据表（MDS/阻塞/IMD3）；
- 结论回写 `PSDR-revB-workorder.md` §1 G3：通过→6 段 BPF 兼 TX 滤波（D6a）；不通过→只做专用 5 段 LPF（D6b）。

## 8. 复算/出处

```bash
# mux 真值表与 ch0=外接滤波排针（dossier §3 / #16 6756908658）
grep -n "ch = (S1<<1)|S0\|external filter header" docs/PSDR-upstream-threads.md
# 外接滤波 4 点的网络名（E_FILT_* 是焊盘/测试点名，网络是 FILTER_RF/IF_P/N，挂在巴伦 L39/L82）
python -c "import json;d=json.load(open('dist/netlist/PSDR_2.6.1_netlist.json',encoding='utf-8'));print({n:d['nets'][n] for n in ['FILTER_RF_P','FILTER_RF_N','FILTER_IF_P','FILTER_IF_N']})"
```
竞品表出处见 `delegation/answers/ANS_开源SDR硬件调研_PSDR261对照.md` §3（外部断言级）。
架构结论出处见 `docs/PSDR-scope-and-cost.md` §7.3、`docs/NEXT-REV-IDEAS`（上游）。
