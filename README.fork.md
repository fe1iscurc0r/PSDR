# PSDR fork — independent `next` line

This repository is a fork of
[MichaelRColton/PSDR](https://github.com/MichaelRColton/PSDR), maintained by
[fe1iscurc0r](https://github.com/fe1iscurc0r).

Upstream is MIT licensed (`LICENSE.md`), and its maintainer explicitly invited
forks to keep the project moving
([issue #7](https://github.com/MichaelRColton/PSDR/issues/7#issuecomment-5634997217), 2026-09-11).
This fork is an independent development line. It does not speak for upstream,
and upstream has not reviewed or endorsed its contents.

## Branch layout

| ref | meaning |
|---|---|
| `master` | mirror of upstream `master`; fast-forward only |
| `next` | integration line for this fork; all new work lands here |
| `workorders/*` | topic branches; merged into `next` |
| `upstream-pr/*` | branches used only for pull requests to upstream |
| tag `fork-base/2026-10-30` | upstream `master` at `45acd0f`, the divergence point |

## What this fork adds

As of 2026-11-03:

- **Firmware builds.** Both lines build on Linux with `arm-none-eabi-gcc` 13.2.1
  from the same mainline. F4 (`Source/`): 0 errors, anchors `_estack=0x20030000`
  and Reset `0x080001B5` match the 2016-05 upstream hex (`anchor_check.py` PASS).
  F7 (`Source_F7/`): 0 errors, 26 warnings, `text 114068 / data 18488 / bss 18260`;
  initial SP `0x20050000` and the empty-slot pattern `[7, 8, 9, 10, 13, 95]` match
  both committed references (`anchor_check_f7.py` PASS). **Baseline changed on
  2026-11-03**: `Source_F7/` used to mirror `PSDR_Rebuild` (merged in M2 as
  `4dd2fca`); it now mirrors `PSDR_F7` (`ab2c8fd`), the branch the maintainer
  named as the firmware base in #19. Reset-vector *values* move with the
  GCC/linker layout, as on F4, so they are reported, not gated. The pre-rebase
  F7 binary is no longer produced from this mainline -- the reference hexes and
  the measured numbers for both baselines are kept in `dist/reference/`.
- **2.6.1 design data.** From the PADS Layout ASCII `Hardware/PSDR.asc`:
  a 391-part / 278-net / 1132-pin netlist, a 10-page KiCad schematic, and a
  4-layer KiCad board (391 footprints, 1194 pads, 5034 track segments,
  22 arcs, 419 vias, 12 zones, 67 outline segments).
  The M2 merge also put the 2.6/2.6.1 CAM and PADS data on the mainline for the
  first time: upstream `master` `45acd0f` still carried the 2.5-era
  `PSDR.pcb`/`PSDR.sch`, because the 2.6.1 work (`468dc41`) exists only on the
  F7/Rebuild line and is not an ancestor of `master`.
- **Reconciliation.** Every source flash is covered and all 461 drill hits
  match the original 2.6.1 Gerber/drill set. The board regenerates
  byte-for-byte (md5 `478a4fac8dc4745fe9bfd082826c9062`, sha256
  `5029bd0265b34bef9176b7af2ca4d8ef4c3e3324c3ff868a1ecaea3f412288cc`
  recorded in `dist/kicad/SHA256SUMS`).
- **EDA import check.** JLCEDA Pro 4.1.60 read back 4 copper layers, 278 nets,
  391 parts and 12 pour outlines; 12/12 pours fill after the precedence fix
  described under known gaps (was 10/12 as imported).
- **BOM and procurement.** Upstream issue #14 asked whether `C307,320` and
  `R72,79` were deleted. They were not: extracted from the board, none of the four
  is a series element (C307/C320 are shunts on U314 = AD8302; R72/R79 bridge the
  mixer LO pairs on L41/L81), so **no 0 ohm jumper is needed** and fitting one
  across the LO pair would short it. The reason the rows looked like missing data
  is that `OPEN`/`DNS` sit in the *Value* column; the clarification goes into the
  unlabelled remarks column the author already uses. Issue #13's two devices are
  recorded too: U304 is `RF Micro Devices SXB-2089Z` (that row's own hyperlink is
  `.../rfmd/SXB-2089Z/599-1068-1-ND/937042`, so the decal name `HMC482ST` is a
  stale label) and the switches get `Mfg Part # = MASWSS0129TR` only, because that
  row has no hyperlink -- no replacement part is proposed anywhere and
  "obsolete" is not verifiable from repository data (`OctopartBOM.csv` has no
  lifecycle column). All of it is upstream **PR #18** (4 commits / 4 files -- the
  last one adds a plain-text cell-by-cell change list so the binary `.xls` diff
  can be reviewed without opening Excel -- that list lives on the PR branch, not on
  `next`); **PR #17 (KiCad schematic, 3 commits / 23 files) was merged upstream as
  `c34afebe`**, and PR #18 is still open: a reviewer asked whether it proposes
  alternatives or fixes, and the answer posted on 2026-11-04 is that it fixes, with
  deliberately no substitute parts.
- **Firmware status (survey plus two fork-local fixes).** The survey lives in
  `docs/`. Until 2026-11-04 no firmware source was modified; two local fixes
  now sit on the fork only (never proposed upstream): a bounded Si5338 I2C
  wait, and a table-driven `signalPath()` that stops state 1
  (`recieve_with_filter`) from falling into the transmit branch. See
  `docs/PSDR-firmware-fixes-F1-F2.md`; the tree is no longer a byte-identical
  mirror of `PSDR_F7`.
  `docs/PSDR-firmware-survey.md` annotates every project module (12,035 lines of
  project code in `Source/`, 10,437 in `Source_F7/`; the other ~330k lines in each
  tree are ST HAL and CMSIS-DSP -- `python tools/fw_stats.py Source Source_F7`)
  and lists what stands in the way. **One** blocking defect applies to the tree we
  carry, and it is invisible until the board boots:
  `Source_F7/src/main.c:1031-1032` waits on the Si5338 over I2C in
  `while(result != HAL_OK)` with no bail-out, so a synthesiser that does not answer
  stops the boot before the display is initialised. The second defect we used to
  list -- an unconditional debug `while(1)` at old `main.c:1021` that only paints
  the screen -- **exists only in the `PSDR_Rebuild` lineage**; in `PSDR_F7`, the
  baseline this mainline now mirrors, that block is commented out and the only live
  `while(1)` is the real main loop at `:1101`. Neither is fixed here on purpose --
  this fork does not modify firmware source (`git diff --stat
  upstream/PSDR_F7:Source next:Source_F7` shows zero `.c/.h` changes; the F4 line
  does carry build-necessary edits, see `docs/WO-psdr-takeover.md` chapter B).
  These findings are **not** proposed upstream; they are recorded for whoever next
  has the board in hand.
  `docs/PSDR-open-data-gaps.md` lists the datasheets still to obtain (HMC1023LP5E
  on U287 is the one that blocks issue #16, and the firmware contains no reference
  to the part at all) and the PCB revision/porting constraints.
- **SMT placement table.** `tools/pads_asc_placement.py` emits
  `dist/fab/PSDR_2.6.1_placement.csv` (391 parts, Top 209 / Bottom 182) straight
  from the PADS `*PART*` records, with the board outline's lower-left corner as
  origin, PADS Y-up sense, and the raw mirror/ori fields kept. It reconciles
  against the BOM (every purchased part covered; everything outside the BOM is a
  fiducial, mounting hole or single-pad test point) and against the
  Gerber-validated KiCad anchors (391/391, worst deviation 0.0005 mm = rounding).
- **Tools.** `tools/` holds the parsers, the KiCad emitter, the
  Gerber/drill comparison script, `reproduce_kicad.py` and
  `anchor_check_f7.py` (the F7 vector-anchor gate); they use only the Python
  standard library.

### Where the rest of the fork-only material is

Nothing in this list is proposed upstream; each row says what it does and does
not establish. The index with recommended reading order is
[`docs/README.md`](docs/README.md), and every claim's command and output is in
`docs/WO-psdr-takeover.md` (chapters A-K; `docs/PSDR-chronicle.md` is the same
story told in order, including the eleven claims we later withdrew).

| 材料 | 它确立什么 | 它不确立什么 |
|---|---|---|
| `docs/PSDR-scope-and-cost.md` | 原始需求、BOM 成本构成、VNA 判为保留项、保留版地板价、不做射频直采的成本理由 | 任何具体降价承诺（价格来自 BOM 里的 DigiKey 号） |
| `docs/PSDR-alternates-proposal.md` | U304 实测封装/偏置拓扑、候选件的频段与供电门槛、局部改版的范围 | 选型结论 -- 提案不是采购单 |
| `docs/PSDR-author-measurement-log.md` | 作者自己量到什么：2.5-175 MHz、-90 dBm@7 MHz、2.5 原型装过、2019 年他选了 CubeMX+FreeRTOS | 板子现在还能不能跑到那些数（没实物） |
| `docs/PSDR-HMC1023-netlist.md` | U287 的 SPI 四线、`LPF_POWER` 无人驱动、`VDDBG` 没有供电 | 改板方案；数据手册级别的结论 |
| `docs/PSDR-open-data-gaps.md` | 还缺哪些手册、2.6 到 2.6.1 的**三处**电阻改动加 2.6.1 表内的自相矛盾（"只有一处 R164"那句已作废，见 §2.1） | 缺料是否等于停产 |
| `docs/PSDR-chronicle.md` | 编年史：上游 2014→2025 的原史（带时间戳与原话）、接手七天 72 提交按天编年、对外件全表与我们自己撤过的 11 条断言 | 结论汇总与待办（那些在总账与缺口表里） |
| `docs/SOP-eda-import-2.6.1.md` | 导入后哪些步骤必须人工、"新板直接导入得 10/12 不是回归" | 端到端自动化（已记 `unsupported`） |
| `docs/PSDR-bringup-checklist.md` | 42 个测点带坐标与网络，上电前该量什么 | 任何实测值（无实物，逐条 SKIP） |
| `evidence/` | 不可重跑的现场读数（EDA 12/12、DRC 513 的构成） | 可重跑的东西 -- 那些只留命令 |
| `dist/reference/` | F7 锚点门的两份参考 hex，带 sha256/blob/出处 | 与 GCC 13 产物字节相同（不声称） |
| `delegation/` + `tools/make_delegation_pack.py` | 给无仓库上下文执行方的自包含输入包与答案 schema | 答案本身（尚未回收、未过机器校验） |

Evidence, commands and per-item verdicts are in
[`docs/WO-psdr-takeover.md`](docs/WO-psdr-takeover.md) (Chinese); the PCB
section is §C-16.

## What this fork does not claim

- **RF is not validated.** The preamp/low-pass filter problem in
  [issue #16](https://github.com/MichaelRColton/PSDR/issues/16) is still open
  and needs hardware. Nothing here changes RF behaviour or claims a fix.
- **The KiCad board is not a production release.** Fabricate from the
  original 2.6.1 Gerbers (upstream `468dc41`, now in this tree under
  `Hardware/Gerbers/PSDR261 Main Board`). The KiCad board is an
  editable, checkable reference.
- **795 KiCad DRC violations remain.** They are triaged in §C-16: none is a
  conversion geometry error; they are source-design violations or two known
  conversion differences (thermal spoke topology, zero-drill Morse paddles).
- **Known conversion gaps:** the two pours that came back empty in JLCEDA Pro
  (`+3V3_FLIP_FLOP` on In1, `V_SUPPLY` on F.Cu) are a pour-precedence problem,
  not a `keepIsland` one: EDA fills overlapping pours with the *smaller*
  `order` winning (opposite of KiCad) and the importer numbers the 12 zones
  1..12 in file order, dropping the PADS priority. Setting the island flag
  alone still gave 10/12; restoring the source precedence gives **12/12
  filled**, verified after save + document close/reopen. EDA's own DRC then
  goes 507 → 513 and the six extras are all island copper of
  `+3V3_FLIP_FLOP`, which the source pour also has as 7 separate HATOUT
  regions. `tools/eda_epro2_pour_source.py` writes the source-derived
  `order`/`keepIsland` into a converted `.epro2` and now matches EDA's own
  PADS-route output on all 12 pours. A fully automated
  convert → patch → import run is **unsupported**: neither the typed action
  catalog (167 actions) nor the MCP bridge exposes a KiCad board import or a
  `.epro2` re-import, and GUI automation is not an acceptable substitute for a
  reproduction step. What is measured: the live board reads 12/12 filled pours
  twice in a row on the post-M2 mainline (§E-9).
  The silk gap is closed (§C-17): the GTO triangle and the GBO serial patch are
  PADS `COPPER` records, now emitted as inner-offset polygons, and the 10 mil
  silk band reconciles 100% GTO / 84.82% GBO (the rest is the stroke-font
  difference on four back-side texts).
- **Not converted:** SolidWorks enclosures and the PADS binary sources.

## Reproduce

```bash
# board + DRC + Gerber/drill package + SHA256 manifest, in one command
python tools/reproduce_kicad.py
# verify an existing tree against dist/kicad/SHA256SUMS without overwriting it
python tools/reproduce_kicad.py --check
```

The comparison defaults to `Hardware/Gerbers/PSDR261 Main Board` inside this
repository (it arrived on `next` with the M2 merge; before that, pass
`--pads-gerbers <upstream 468dc41>/Hardware/Gerbers/PSDR261\ Main\ Board`).

The script wraps the individual steps (`tools/pads_asc_pcb.py`,
`kicad-cli pcb drc`, `kicad-cli pcb export gerbers|drill`,
`tools/kicad_gerber_compare.py`); §C-18 records what each manifest row covers
and why the DRC report is not hashed.

```bash
# SMT placement table + BOM reconciliation (needs a CSV export of the BOM)
python tools/pads_asc_placement.py Hardware/PSDR.asc \
    --out dist/fab/PSDR_2.6.1_placement.csv --bom-csv PSDR2.6.1_BOM.csv
# F7 vector anchors (references are tracked under dist/reference/)
python tools/anchor_check_f7.py Source_F7/build_linux_f7/PSDR.hex \
    dist/reference/PSDR_hex_2017-01-15_aaa24f8_PSDR_F7.hex
```

KiCad 10.0 is required for the board format and the CLI flags. Firmware
build steps are in `docs/WO-psdr-takeover.md` §B and
`docs/psdr-build-notes.md`.

## License

`LICENSE.md` is the upstream MIT license (Copyright (c) 2026 PSDR) and is
kept unchanged. New files in this fork are released under the same MIT
terms. Everything is provided without warranty; hardware work is at your
own risk.
