# 采购清单（procurement_checklist.csv）说明

日期：2026-11-09。生成：`python tools/bom_procurement_list.py`（可重跑）。
口径：**2.6.1 BOM**（`PSDR2.6.1_BOM_flat.csv`，即已下单那块板的版本）逐行展开，
合并 `assembly_class.csv` 的贴装分类与 `value_threeway_sch_asc_bom.csv` 的值冲突标记。

## 列含义

| 列 | 含义 |
|---|---|
| `dnp` / `dnp_reason` | 不采购：BOM 明示 "Buy but do not populate" / "DNP by design" / 值 OPEN/DNS / qty=0 备用条目 |
| `assembly_cls` | 该行位号的贴装分类计数（hand=烙铁 / air=热风 / reflow=机贴 / mechanical=不算件） |
| `sourcing_flag` | 已知断供件（U304=SXB-2089Z、U16/U24/U30=MASWSS0129），替代调研进行中 |
| `value_conflict` | 三方值扫描里的冲突位号：`layout-alone` 按多数票（BOM+原理图）买；`bom-alone` 的 R164 两值都记、等实测；`all-differ` 的 L34 只在 BOM 有值 |
| `cost_x1_usd_2016` / `line_cost_usd_2016` | **2016 年 DigiKey 价**，仅作历史参考，不是当前采购价 |

## 数字

- 86 行：80 行采购 + 6 行不采购（C307/320、R72/79、EARPHONE、SPEAKER×2、qty=0 条目）。
- 337 个位号（不含测试点/基准点等 mechanical）。
- 2016 价口径：采购部分 $267.55，DNP 部分 $4.99（合计 $272.54，与 assembly-sourcing §6 一致）。

## 与 2.6 BOM 的差异（别拿错表）

2.6 表（`PSDR2.6_BOM_flat.csv`）多两行 "Buy but do not populate"：**电池连接器**（455-1719-ND）
与**编码器**（PEC09-2320F-S0015-ND）；2.6.1 表没有这两行。编码器属于独立的 Encoder Board 产品，
不在本板装配范围。本清单以 2.6.1 为准。

## 采购原则（2026-11-09 用户拍板）

- **国产优先**，除非国外明显更便宜；通用阻容/结构件走立创/嘉立创渠道。
- 射频断供件（U304、三片 DPDT）等替代调研结论再买，见 `docs/PSDR-alternates-proposal.md` 与后续调研文档。
- 分档采购节奏见 `docs/PSDR-assembly-sourcing.md` §6.2（P 电源 → M MCU+时钟 → A 音频 → R 射频）。
- 11 个冲突位号按 `docs/PSDR-open-data-gaps.md` §2.1b/§2.1c 的多数票口径，R164 等板到实测。