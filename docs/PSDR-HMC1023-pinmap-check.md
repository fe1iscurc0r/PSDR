# HMC1023 32 脚逐脚对手册（v01.0113 Table 6 × 2.6.1 网表）

日期：2026-11-04；**2026-11-07 独立复核**（工单 §7.3 收口）：重新从
`dist/netlist/PSDR_2.6.1_netlist.json` 取 U287 全部 33 端子、重新用 `pymupdf` 按坐标
重建手册 p.11–12 Table 6，逐脚一致；复核中发现并更正了 §2 第 2 条的通道归属笔误。
口径：**手册** = `HMC1023LP5E v01.0113` 的 **Table 6 Pin Descriptions**（p.11–12，
用 `pymupdf` 按坐标重建；`pypdf` 抽这张表会列错位，别用）；**板** = `dist/netlist/PSDR_2.6.1_netlist.json` 的 U287。

## 1. 逐脚表

| 手册脚 | 手册功能 | 手册要求/说明 | 板上网络（实测） | 判定 |
|---|---|---|---|---|
| 1,3,8,9,10,17,24,25,32 | N/C | 手册注：测量时这些脚"connected to RF/DC ground externally" | 全部 `GND` | ✅ 与手册注一致 |
| 2,4 | VDDQ | Q 通道 5 V 供电，须就地去耦 | `LPF_5V` | ✅ |
| 5 | CMQ | Q 通道输出共模电平 | `$$$27752` → `R296.1`/`R297.2` | ✅（偏置电阻） |
| 6,7 | OQP,OQN | Q 通道差分输出 | `FILTER_OUT_P` / `FILTER_OUT_N` | ✅ |
| **11** | **CALCK** | 校准时钟输入 | `$$$15644` → `C283.1`（另一端 `FILTER_CAL` ← Si5338 `CLK1A`） | ✅ 已接（交流耦合） |
| 12,14,15 | SCK,SDI,SEN | SPI | `FILTER/GAIN_POT_CLK` / `FILTER/GAIN_POT_MOSI` / `FILTER_CS` | ✅ |
| 13 | SDO | SPI 数据输出 | `FILTER_MISO` | ✅ |
| 16 | DVDD | 数字 5 V 供电 | `LPF_5V` | ✅ |
| 18,19 | OIN,OIP | **I 通道**差分输出 | `$$$31740`→`C293.2`、`$$$31750`→`C294.1` | ⚠️ 见 §2 第 2 条 |
| 20 | CMI | I 通道输出共模电平 | `$$$27784` → `R285.2`/`R286.1` | ✅（偏置电阻） |
| 21,23 | VDDi | I 通道 5 V 供电 | `LPF_5V` | ✅ |
| **22** | **VDDCAL** | 校准 5 V 供电 | `LPF_5V` | ✅ **有供电** |
| 26,27 | IIP,IIN | I 通道差分输入 | `FILTER_IN_P` / `FILTER_IN_N` | ✅ |
| **28** | **VDDBG** | **偏置 5 V 供电** | `$$$15137` → **只有 `C292.1`**（去耦电容） | ❌ **无供电，只有去耦** |
| **29** | **VBG** | 1.2 V 带隙输出（**testing only**） | **无网络**（悬空） | ✅ 手册说仅测试用，可不接 |
| 30,31 | IQN,IQP | **Q 通道**差分输入 | `$$$31745`←`C293.1`、`$$$31748`←`C294.2` | ⚠️ 见 §2 第 2 条 |
| 33（散热盘） | GND | — | `GND` | ✅ |

## 2. 结论（三条，全部读得）

1. **VDDBG（pin 28）是唯一真正的供电缺口**：它只挂了一个去耦电容 `C292`，没有任何电源馈入。
   手册要求 "Bias 5V Supply. Must be locally decoupled to GND" ⇒ **偏置块没有供电**。
   这比我们之前泛泛说的"VDDBG 无供电"更精确：**线有、电容有、电源没有**。
2. **I 通道输出被电容跨接到 Q 通道输入**：`OIN/OIP`（**I** 输出，18/19）经 `C293`/`C294`
   接到 `IQN/IQP`（**Q** 输入，30/31）。Q 通道没有外部信号馈入，其输入只来自 I 输出的
   交流耦合——Q 半边没有被使用，I 通道（26/27 输入、18/19 输出）才是真正在用的那半。
   （HMC1023 是双通道器件，板上只用了一半。）
   2026-11-07 更正：旧版此处把 18/19 写成"Q 输出"、30/31 写成"Q 输入"并称之为"自环"；
   手册 Table 6 明确 18/19 属 I 通道、30/31 属 Q 通道，物理接法不变，通道归属以手册为准。
3. **VBG（29）悬空是对的**：手册标 "1.2V Bandgap output (testing only)"，不接不算缺陷；
   之前把"pin 29 无网络"当异常列出来的口径要改成"按手册可不接"。

## 3. 复算

```bash
python -c "import json;d=json.load(open('dist/netlist/PSDR_2.6.1_netlist.json',encoding='utf-8'));\
print([p for p in d['nets']['\$\$\$15137']])"
python - <<'PY'
import pymupdf,collections
doc=pymupdf.open('D:/my git/PSDR-build-artifacts/hmc1023.pdf')
for pno in (10,11):
    rows=collections.defaultdict(list)
    for w in doc[pno].get_text('words'): rows[round(w[1]/4)].append((w[0],w[4]))
    for k in sorted(rows): print('page',pno+1,'|',' '.join(t for _,t in sorted(rows[k]))[:120])
PY
```
