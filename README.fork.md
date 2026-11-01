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

As of 2026-11-01:

- **Firmware builds.** The F4 firmware builds on Linux with
  `arm-none-eabi-gcc` 13.2.1 (0 errors; anchors `_estack=0x20030000` and
  Reset `0x080001B5` match the 2016-05 upstream hex). The F7 firmware has a
  `Makefile.linux` on `workorders/2026-11-01-psdr-f7-linux-build`, and its
  output is reconciled against the 2018-06-21 upstream hex by address, vector
  table and size. F7 integration into `next` is planned (M2).
- **2.6.1 design data.** From the PADS Layout ASCII `Hardware/PSDR.asc`:
  a 391-part / 278-net / 1132-pin netlist, a 10-page KiCad schematic, and a
  4-layer KiCad board (391 footprints, 1194 pads, 5034 track segments,
  22 arcs, 419 vias, 12 zones, 67 outline segments).
- **Reconciliation.** Every source flash is covered and all 461 drill hits
  match the original 2.6.1 Gerber/drill set. The board regenerates
  byte-for-byte (md5 `157f000bc9caa4eb67492a9a751d8f91`).
- **EDA import check.** JLCEDA Pro 3.2.203 read back 4 copper layers,
  278 nets, 391 parts and 12 pour outlines; 10/12 pours fill after rebuild
  (two known gaps below).
- **Tools.** `tools/` holds the parsers, the KiCad emitter and the
  Gerber/drill comparison script; they use only the Python standard library.

Evidence, commands and per-item verdicts are in
[`docs/WO-psdr-takeover.md`](docs/WO-psdr-takeover.md) (Chinese); the PCB
section is §C-16.

## What this fork does not claim

- **RF is not validated.** The preamp/low-pass filter problem in
  [issue #16](https://github.com/MichaelRColton/PSDR/issues/16) is still open
  and needs hardware. Nothing here changes RF behaviour or claims a fix.
- **The KiCad board is not a production release.** Fabricate from the
  original 2.6.1 Gerbers at upstream `468dc41`. The KiCad board is an
  editable, checkable reference.
- **795 KiCad DRC violations remain.** They are triaged in §C-16: none is a
  conversion geometry error; they are source-design violations or two known
  conversion differences (thermal spoke topology, zero-drill Morse paddles).
- **Known conversion gaps:** a ~1.4 mm silk triangle on GTO is unlocated, and
  two zones (`+3V3_FLIP_FLOP` on In1, `V_SUPPLY` on F.Cu) rebuild with zero
  fill when imported into JLCEDA Pro due to a `keepIsland` mismatch.
- **Not converted:** SolidWorks enclosures and the PADS binary sources.

## Reproduce

```bash
python tools/pads_asc_pcb.py Hardware/PSDR.asc --all \
    -o dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb
kicad-cli pcb drc --severity-all --refill-zones \
    -o dist/kicad/drc_PSDR_2.6.1_pcb_spike_full.txt \
    dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb
```

KiCad 10.0 is required for the board format and the CLI flags. Firmware
build steps are in `docs/WO-psdr-takeover.md` §B and
`docs/psdr-build-notes.md`.

## License

`LICENSE.md` is the upstream MIT license (Copyright (c) 2026 PSDR) and is
kept unchanged. New files in this fork are released under the same MIT
terms. Everything is provided without warranty; hardware work is at your
own risk.
