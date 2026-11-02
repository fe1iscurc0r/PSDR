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

KiCad 10.0 is required for the board format and the CLI flags. Firmware
build steps are in `docs/WO-psdr-takeover.md` §B and
`docs/psdr-build-notes.md`.

## License

`LICENSE.md` is the upstream MIT license (Copyright (c) 2026 PSDR) and is
kept unchanged. New files in this fork are released under the same MIT
terms. Everything is provided without warranty; hardware work is at your
own risk.
