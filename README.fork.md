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

As of 2026-11-02:

- **Firmware builds.** Both lines build on Linux with `arm-none-eabi-gcc` 13.2.1
  from the same mainline. F4 (`Source/`): 0 errors, anchors `_estack=0x20030000`
  and Reset `0x080001B5` match the 2016-05 upstream hex (`anchor_check.py` PASS).
  F7 (`Source_F7/`, merged in M2 as `4dd2fca`): 0 errors, initial SP
  `0x20050000` matches the 2018-06-21 upstream hex `457c270:Source/Debug/PSDR.hex`
  and the empty-slot pattern is identical; reset-vector *values* move with the
  GCC/linker layout, as on F4. Both outputs are byte-identical to the binaries
  built before the merge (§E-7).
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
  lifecycle column). All of it is upstream **PR #18** (3 commits); PR #17
  (KiCad schematic) is still open too.
- **Firmware status (read-only survey, fork-local).** No source file was touched.
  `docs/PSDR-firmware-survey.md` annotates every project module (~12k lines of
  project code in `Source/`, ~11k in `Source_F7/`; the other 330k lines are ST HAL
  and CMSIS-DSP) and lists what stands in the way. Two blocking defects are worth
  stating here because they are invisible until the board boots:
  `Source_F7/src/main.c:1021` has an unconditional debug `while(1)` that only
  fills the screen, so the real main loop at line 1065 is unreachable in the
  committed source; and `Source_F7/src/frequency_control.c:54` waits on the Si5338
  over I2C in a loop with no timeout, so a missing synthesiser hangs the boot
  before the display is initialised. Neither is fixed here on purpose -- this
  fork does not modify firmware source. These findings are **not** proposed
  upstream; they are recorded for whoever next has the board in hand.
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
# F7 vector anchors against the author's 2018-06-21 hex
python tools/anchor_check_f7.py Source_F7/build_linux_f7/PSDR.hex Source_F7/Debug/PSDR.hex
```

KiCad 10.0 is required for the board format and the CLI flags. Firmware
build steps are in `docs/WO-psdr-takeover.md` §B and
`docs/psdr-build-notes.md`.

## License

`LICENSE.md` is the upstream MIT license (Copyright (c) 2026 PSDR) and is
kept unchanged. New files in this fork are released under the same MIT
terms. Everything is provided without warranty; hardware work is at your
own risk.
