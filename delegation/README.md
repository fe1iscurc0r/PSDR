# Delegation input pack

Generated, never hand-copied. Regenerate with:

```
python tools/make_delegation_pack.py
```

Sources: `Hardware/PSDR.asc` (part types, decals, placement),
`dist/netlist/PSDR_2.6.1_netlist.json` (pin/net + part types),
`Hardware/BOMs/PSDR_2.6.1/OctopartBOM.csv` (DigiKey-numbered BOM rows).

Units: PADS ASCII coordinates are integers, **38100 units = 1 mil** (derived from
the board outline, not stated in the file).

## How to consume this pack: trust the body, never the file name

The per-designator files under `ic_context/` and the per-footprint files under
`decal_raw/` are convenient, but a knowledge-base ingest that re-orders uploads can
pair a file name with the wrong body. Two defences, both mechanical:

1. **Use the three merged files - one per task. Nothing there can be mislabelled:**

   | file | contains | task |
   |---|---|---|
   | `TASK_C_ic_context_all.md` | every IC section, each starting `## <ref> ...` | C |
   | `TASK_F_decal_raw_all.md` | every footprint block, each starting `## <decal> ...` | F |
   | `TASK_ABE_census_and_bom.md` | part census + BOM rows + the datasheet target list | A, B, E |

   Each merged file ends with a `TOTALS:` line stating how many sections/rows it holds;
   check it before answering. `MANIFEST.csv` lists sha256, byte size and the first line
   of every file in the pack, so any transport that shuffles names is detectable.

2. If you are handed the small files instead, identify each one by **its own first
   line** (`# <ref> - pin/net context`) and by `_index.csv` (refdes -> part type ->
   decal), not by its name. Decal names are shared or inherited: the STM32F746 sits on
   a pad group called `STM32F429_LQFP100`, so never infer a chip from a footprint name.

## Answer schema (this repo machine-checks against it)

One row per question, 8 columns - the 7 working columns plus a leading anchor so the
result is verifiable line by line:

```
anchor | IC/件 | 引脚或功能 | 手册公式或规格(原文) | 手册推荐条件 | 板上实际值 | 判定 | 出处与依据强度
```

- `anchor` = `<merged file>:<section>` e.g. `TASK_C_ic_context_all.md:U314`, or
  `MANIFEST.csv` row for census/BOM answers.
- `判定` in `一致 / 不一致 / 信息不足`. `出处与依据强度` = document + revision + page or
  table, marked `手册原文` / `厂商页` / `第三方`, and must carry a short verbatim English quote.
- Anything not read from official material: write `unverified` in that cell. Never fill a
  gap with a typical value or usual practice. Distributor text is a lead, not evidence.
- If official material contradicts the premise stated in the file, say so in `判定`
  rather than working around it.
- Answer only the question at the head of each section. No design proposals.

Verification on our side: rows are re-checked by re-decoding the decals with
`tools/pads_asc_decal.py`, by recomputing the totals in each merged file, and by
spot-recomputing 10 random rows. A batch with any failed spot check is returned whole.
