#!/usr/bin/env python3
"""Build the delegation input pack: self-contained files for an agent that has no
access to this repository, plus the answer schema this repo checks results with.

All inputs are derived, never hand-copied:

  Hardware/PSDR.asc                      -> part types, decals, placement
  dist/netlist/PSDR_2.6.1_netlist.json   -> pin/net connectivity with part types
  Hardware/BOMs/PSDR_2.6.1/OctopartBOM.csv -> the DigiKey-numbered BOM rows

Unit note: PADS ASCII coordinates are integers, 38100 units = 1 mil (derived from
the board outline in docs/WO-psdr-takeover.md C-13; not stated in the file).

Decal geometry is exported **verbatim** as source blocks rather than as my
decoded numbers, so the delegated agent cannot be misled by my interpretation of
the grammar; results are checked by re-decoding with tools/pads_asc_decal.py.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pads_asc_decal import (  # noqa: E402
    DECAL_HEADER,
    parse_decals,
    parse_parts,
    parse_parttypes,
)

# Reference designators whose datasheets drive the "external parts vs formula" audit (task C),
# and the decal/task F list. Topic text = the only question the agent may answer.
IC_TOPICS = {
    "U314": "AD8302: VMAG/VPHS transfer functions and the PSET/MSET resistor formulas",
    "U287": "HMC1023LP5E: digital interface, register map, cutoff options, CALCK, VDDBG/VBG",
    "U241": "Si5338DN: output frequency ranges, VCO/divider limits, I2C timing register",
    "U185": "RXM-GPS-RM-T: internal antenna? external active-antenna wiring, sensitivity/TTFF",
    "U15": "MAX5388: gain-set connections LA/LB and the SPI address/opcode table",
    "U272": "MCP6N11: instrumentation-amp gain set by external resistors (formula + range)",
    "U255": "MCP6N11: instrumentation-amp gain set by external resistors (formula + range)",
    "U253": "AD8131: differential output, VOS/OS pin, gain and termination formulas",
    "U260": "AD8131: differential output, VOS/OS pin, gain and termination formulas",
    "U199": "TPA0253: gain-set pins, output power with the given supply and load",
    "U85": "ADP1613: feedback-divider equation, switching frequency, inductor limits",
    "U304": "SXB-2089Z (vs SBB-2089 / HMC482ST89): bandwidth, supply, input-side DC",
    "U16": "MASWSS0129TR: control truth table (V1/V2), IL/isolation/switching, lifecycle",
    "U24": "MASWSS0129TR: control truth table (V1/V2), IL/isolation/switching, lifecycle",
    "U30": "MASWSS0129TR: control truth table (V1/V2), IL/isolation/switching, lifecycle",
    "U211": "SN74CBTLV3253: S0/S1 function table, Ron, off-capacitance, isolation",
    "U298": "SN74CBTLV3253: S0/S1 function table, Ron, off-capacitance, isolation",
    "U279": "SY100EP52: AC table incl. any minimum input frequency; quadrature /2 use",
    "U280": "SY100EP52: AC table incl. any minimum input frequency; quadrature /2 use",
    "U4": "MAX4525CUB+: supply range, Ron vs supply, off-capacitance, signal swing limits",
    "U18": "MAX4525CUB+: supply range, Ron vs supply, off-capacitance, signal swing limits",
    "U86": "MAX4525CUB+: supply range, Ron vs supply, off-capacitance, signal swing limits",
    "U121": "STM32F746VGT6: errata items for SPI+DMA, I2C2 BSY, ADC+DMA, TIM",
    "U37": "SN74LVC1G3157: Ron, signal range vs supply, control polarity",
    "U161": "MCP73871: charge current set, input/Power-Path limits, NTC requirements",
    "L39": "Coilcraft WBC2-1TL (1:2): bandwidth, loss, imbalance, ratings",
    "L82": "Coilcraft WBC2-1TL (1:2): bandwidth, loss, imbalance, ratings",
    "L41": "ADE-2ASK diode-ring mixer: RF/LO/IF ranges, LO drive, isolation, conversion loss",
    "L81": "ADE-2ASK diode-ring mixer: RF/LO/IF ranges, LO drive, isolation, conversion loss",
    "U131": "FAN4174: supply range, output swing, used as filter/gain stage",
    "U216": "FAN4174: supply range, output swing, used as filter/gain stage",
    "U47": "FAN4174: supply range, output swing, used as filter/gain stage",
    "U58": "FAN4174: supply range, output swing, used as filter/gain stage",
    "U189": "SSM2167 mic preamp: gain set, supply range, output coupling",
    "U32": "SPU0410HR5H-PB MEMS mic: supply, sensitivity, pinout vs the preamp hook-up",
    "U114": "AP3417C buck regulator: feedback divider equation, inductor/frequency limits",
}

PASSIVE_PREFIX = ("CSM-", "RSM-", "ISM-", "CAP_", "RES_", "IND_", "FER_")

# Guard: the question text for a designator is only meaningful if the designator is
# actually that part. Two refs were mismapped on first authoring, so this is checked
# on every run instead of trusted.
EXPECT = {
    "U314": "AD8302", "U287": "HMC1023", "U241": "SI5338", "U185": "RXM-GPS",
    "U15": "MAX5388", "U272": "MCP6N11", "U255": "MCP6N11", "U253": "AD8131",
    "U260": "AD8131", "U199": "TPA0253", "U85": "ADP1613", "U304": "HMC482ST",
    "U16": "MASWSS0129", "U24": "MASWSS0129", "U30": "MASWSS0129",
    "U211": "CBTLV3253", "U298": "CBTLV3253", "U279": "SY10EP52", "U280": "SY10EP52",
    "U4": "MAX4525", "U18": "MAX4525", "U86": "MAX4525", "U121": "STM32F746",
    "U37": "SN74LVC1G3157", "U161": "MCP73871", "L39": "WBC2-1TL", "L82": "WBC2-1TL",
    "L41": "ADE-2ASK", "L81": "ADE-2ASK", "U131": "FAN4174", "U216": "FAN4174",
    "U47": "FAN4174", "U58": "FAN4174", "U189": "SSM2167", "U32": "SPU0410",
    "U114": "AP3417C",
}
UNITS_PER_MIL = 38100


def mil(v: int) -> str:
    return f"{v / UNITS_PER_MIL:.3f}"


def neighbours_index(nets: dict) -> dict:
    out: dict[str, list] = {}
    for net, pins in nets.items():
        for p in pins:
            others = [q for q in pins if q is not p]
            out.setdefault(p["refdes"], []).append((p["pin"], p.get("pin_name", ""), net, others))
    for ref in out:
        out[ref].sort(key=lambda row: (len(row[0]), row[0]))
    return out


def fmt_neighbours(others: list, types: dict, limit: int = 14) -> str:
    if not others:
        return "-"
    shown = [f"{q['refdes']}({types.get(q['refdes'], '?')}).{q['pin']}" for q in others[:limit]]
    tail = "" if len(others) <= limit else f" ...(共 {len(others)} 脚)"
    return " ".join(shown) + tail


def write_ic_context(ctx_dir: str, nb: dict, types: dict) -> tuple[int, list]:
    os.makedirs(ctx_dir, exist_ok=True)
    # stale files would keep asking a question for a designator we have since removed
    for stale in os.listdir(ctx_dir):
        if stale.endswith(".md"):
            os.remove(os.path.join(ctx_dir, stale))
    missing = []
    for ref in sorted(IC_TOPICS):
        rows = nb.get(ref)
        if not rows:
            missing.append(ref)
        with open(os.path.join(ctx_dir, f"{ref}.md"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(f"# {ref} - pin/net context\n\n")
            fh.write(f"Question to answer (only this one): {IC_TOPICS[ref]}\n\n")
            fh.write(f"part_type from the netlist: `{types.get(ref, 'NOT IN NETLIST')}`\n\n")
            exp = EXPECT.get(ref)
            if exp:
                fh.write(f"Premise check: this question assumes the part is **{exp}**. "
                         "If the part_type above does not match, stop and report the "
                         "contradiction instead of answering.\n\n")
            if not rows:
                fh.write("No pin of this designator appears in the netlist.\n")
                continue
            fh.write("| pin | pin name | net | other pins on the same net (refdes(part_type).pin) |\n")
            fh.write("|---|---|---|---|\n")
            for pin, pin_name, net, others in rows:
                fh.write(f"| {pin} | {pin_name or '-'} | `{net}` | {fmt_neighbours(others, types)} |\n")
            fh.write("\nNets named `$$$...` are unnamed wires in PADS: the label carries no\n")
            fh.write("meaning, it only says these pads are one electrical node.\n")
    return len(IC_TOPICS), missing


def write_parts_census(path: str, types: dict) -> None:
    per_type: dict[str, list] = {}
    for ref, t in types.items():
        per_type.setdefault(t, []).append(ref)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["part_type", "qty", "category", "designators"])
        for t in sorted(per_type, key=lambda k: (-len(per_type[k]), k)):
            refs = sorted(per_type[t])
            cat = "passive" if t.startswith(PASSIVE_PREFIX) else "ic_or_other"
            shown = ",".join(refs[:24]) + (f",...(of {len(refs)})" if len(refs) > 24 else "")
            w.writerow([t, len(refs), cat, shown])


def decal_source_blocks(lines: list, name: str) -> list:
    """Verbatim *PARTDECAL* block for one decal: its header line until the next header."""
    starts = [i for i, ln in enumerate(lines) if DECAL_HEADER.match(ln)]
    for k, i in enumerate(starts):
        if lines[i].split()[0] == name:
            end = starts[k + 1] if k + 1 < len(starts) else len(lines)
            return lines[i:end]
    return []


def write_decal_pack(raw_dir: str, lines: list, parts: dict, parttypes: dict,
                     decals: dict, types: dict) -> int:
    os.makedirs(raw_dir, exist_ok=True)
    for stale in os.listdir(raw_dir):
        if stale.endswith(".txt"):
            os.remove(os.path.join(raw_dir, stale))
    refs = [r for r in IC_TOPICS if r in parts]
    names = sorted({parttypes.get(parts[r]["type"], parts[r]["type"]) for r in refs})
    with open(os.path.join(raw_dir, "_index.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["refdes", "netlist_part_type", "placement_type", "decal",
                    "terminals", "block_file"])
        for r in sorted(refs):
            dec = parttypes.get(parts[r]["type"], parts[r]["type"])
            blk = decal_source_blocks(lines, dec)
            fn = ""
            if blk:
                fn = f"{dec}.txt"
                with open(os.path.join(raw_dir, fn), "w", encoding="utf-8", newline="\n") as bf:
                    bf.write("\n".join(blk) + "\n")
            d = decals.get(dec)
            w.writerow([r, types.get(r, ""), parts[r]["type"], dec,
                        len(d["terminals"]) if d else "", fn])
    return len(names)


def write_bom_rows(src: str, path: str) -> int:
    n = 0
    with open(src, encoding="utf-8", errors="replace", newline="") as fin, \
            open(path, "w", encoding="utf-8", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(["qty", "digikey", "vendor", "mpn", "octopart_url"])
        for row in csv.reader(fin):
            if len(row) < 5 or not row[1].strip():
                continue
            w.writerow([row[0], row[1], row[2], row[3], row[4]])
            n += 1
    return n


README = """# Delegation input pack

Generated, never hand-copied. Regenerate with:

```
python tools/make_delegation_pack.py
```

Sources: `Hardware/PSDR.asc` (part types, decals, placement),
`dist/netlist/PSDR_2.6.1_netlist.json` (pin/net + part types),
`Hardware/BOMs/PSDR_2.6.1/OctopartBOM.csv` (DigiKey-numbered BOM rows).

Units: PADS ASCII coordinates are integers, **38100 units = 1 mil** (derived from
the board outline, not stated in the file).

Decal names are the layout database's own names and are **shared or inherited**: the
STM32F746 on this board sits on the decal named `STM32F746_LQFP100` in the netlist but
its pad group is called `STM32F429_LQFP100` in `*PARTDECAL*`. Never infer which chip a
footprint is for from the decal file name - use `decal_raw/_index.csv` (refdes -> part
type -> decal) for that mapping.

## Files

| file | what it is | feeds task |
|---|---|---|
| `ic_context/<ref>.md` | one IC: every pin -> net -> other pins on that net, with each part type. Passive part-type names **encode the value** (`CSM-X5R-22U-20P-10V-1210`, `RSM-6K98-1PCT-250MW-1206`) | C |
| `decal_raw/<decal>.txt` | **verbatim** `*PARTDECAL*` source block for that footprint (deliberately not decoded - compare pads against the vendor's recommended land pattern without taking my word for the grammar) | F |
| `decal_raw/_index.csv` | refdes -> placement type -> decal, terminal count, block file | F |
| `parts_census.csv` | every distinct part type with quantity and designators | A, B, E |
| `bom_rows.csv` | BOM rows carrying a DigiKey part number (qty / DK / vendor / MPN / link) | A, B |

## Answer schema (this repo machine-checks against it)

```
<file>:<row> | conclusion (one sentence) | evidence strength (datasheet text / vendor page / distributor) | source (document + revision + page or table) | verbatim English quote | contradiction with the premise | unverified items
```

Hard rules for the answering side:

1. Every conclusion needs a document name + revision + page or table, plus a short
   **verbatim English quote**. No citation = no answer.
2. Anything not read from official material is written as `unverified`. Never fill a
   gap with "typical value" or "usual practice".
3. Distributor or aggregator text is a lead, not evidence.
4. If official material contradicts the premise in the file, say so plainly.
5. Answer only the question at the top of the file. No design proposals.

Verification on our side: rows are re-checked by re-decoding the decals with
`tools/pads_asc_decal.py`, and by spot-recomputing 10 random BOM/census rows.
A batch with any failed spot check is returned whole, not cherry-picked.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asc", default="Hardware/PSDR.asc")
    ap.add_argument("--netlist", default="dist/netlist/PSDR_2.6.1_netlist.json")
    ap.add_argument("--bom", default="Hardware/BOMs/PSDR_2.6.1/OctopartBOM.csv")
    ap.add_argument("--out", default="delegation")
    a = ap.parse_args()

    with open(a.asc, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    parts = parse_parts(lines)
    parttypes = parse_parttypes(lines)
    decals = parse_decals(lines)

    with open(a.netlist, encoding="utf-8") as fh:
        nl = json.load(fh)
    types = nl["parts"]
    nb = neighbours_index(nl["nets"])

    bad = [(r, EXPECT[r], types.get(r, "MISSING"))
           for r in EXPECT if EXPECT[r] not in types.get(r, "")]
    if bad:
        print("ERROR IC_TOPICS/EXPECT mismatch - fix the designator mapping first:")
        for r, want, got in bad:
            print(f"  {r}: expected part containing {want!r}, netlist says {got!r}")
        return 2

    os.makedirs(a.out, exist_ok=True)
    ctx_dir = os.path.join(a.out, "ic_context")
    n_ctx, missing = write_ic_context(ctx_dir, nb, types)
    write_parts_census(os.path.join(a.out, "parts_census.csv"), types)
    n_decal = write_decal_pack(os.path.join(a.out, "decal_raw"), lines, parts,
                               parttypes, decals, types)
    n_bom = write_bom_rows(a.bom, os.path.join(a.out, "bom_rows.csv"))
    with open(os.path.join(a.out, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(README)

    print(f"ic_context: {n_ctx} files (netlist has {len(types)} designators)")
    print(f"decal_raw : {n_decal} distinct decals for the IC list")
    print(f"parts_census: {len(set(types.values()))} part types")
    print(f"bom_rows: {n_bom} rows with a DigiKey number")
    if missing:
        print("WARNING designators with no pins in the netlist (fix IC_TOPICS): "
              + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
