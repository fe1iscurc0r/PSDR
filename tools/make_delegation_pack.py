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
"""


def merged_ic_sections(nb: dict, types: dict):
    for ref in sorted(IC_TOPICS):
        rows = nb.get(ref, [])
        yield ref, rows


def write_merged(out: str, nb: dict, types: dict, lines: list, parts: dict,
                 parttypes: dict, decals: dict) -> None:
    # Task C: all IC contexts in one file.
    with open(os.path.join(out, "TASK_C_ic_context_all.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# TASK C - external parts vs the datasheet formulas\n\n")
        fh.write("One section per designator. Answer only the question in that section.\n")
        fh.write("Identify your answer by the section heading, not by any file name.\n\n")
        n = 0
        for ref, rows in merged_ic_sections(nb, types):
            n += 1
            fh.write(f"---\n\n## {ref} — `{types.get(ref, 'NOT IN NETLIST')}`\n\n")
            fh.write(f"Question (only this one): {IC_TOPICS[ref]}\n\n")
            exp = EXPECT.get(ref)
            if exp:
                fh.write(f"Premise check: this section assumes the part is **{exp}**; "
                         "if the type in the heading does not match, stop and report the "
                         "contradiction.\n\n")
            if not rows:
                fh.write("No pins of this designator appear in the netlist.\n\n")
                continue
            fh.write("| pin | pin name | net | other pins on the same net (refdes(part_type).pin) |\n")
            fh.write("|---|---|---|---|\n")
            for pin, pin_name, net, others in rows:
                fh.write(f"| {pin} | {pin_name or '-'} | `{net}` | {fmt_neighbours(others, types)} |\n")
            fh.write("\nNets named `$$$...` are unnamed wires in PADS: one electrical node, no meaning.\n\n")
        fh.write(f"TOTALS: sections={n} (expected {len(IC_TOPICS)})\n")

    # Task F: all decal blocks in one file.
    refs = [r for r in IC_TOPICS if r in parts]
    names = sorted({parttypes.get(parts[r]["type"], parts[r]["type"]) for r in refs})
    with open(os.path.join(out, "TASK_F_decal_raw_all.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# TASK F - board footprint as drawn, verbatim, vs the vendor's recommended land pattern\n\n")
        fh.write("Blocks are copied out of `*PARTDECAL*` untouched. Coordinates are PADS ASCII\n")
        fh.write("integers, **38100 units = 1 mil**. Do not trust the decal name as a chip name\n")
        fh.write("(the STM32F746 sits on a pad group called `STM32F429_LQFP100`).\n\n")
        for name in names:
            blk = decal_source_blocks(lines, name)
            users = sorted(r for r in refs
                           if parttypes.get(parts[r]["type"], parts[r]["type"]) == name)
            fh.write(f"---\n\n## {name} — used by {', '.join(users)}"
                     f" — {len(decals.get(name, {}).get('terminals', []))} terminals\n\n")
            fh.write("```text\n" + "\n".join(blk) + "\n```\n\n")
        fh.write(f"TOTALS: decals={len(names)}\n")

    # Tasks A/B/E: census + BOM rows + target list, one file.
    with open(os.path.join(out, "TASK_ABE_census_and_bom.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# TASKS A/B/E - every distinct part on the board, and the DigiKey-numbered BOM rows\n\n")
        fh.write("A = lifecycle status per line, B = LCSC/SMT usability, E = the official\n")
        fh.write("datasheet URL + revision + page for each part type you are asked about.\n\n")
        fh.write("## 1. part census (part_type, qty, category, designators)\n\n")
        fh.write("Passive part-type names encode the value, e.g.\n")
        fh.write("`CSM-X5R-22U-20P-10V-1210` = 22 uF X5R 20% 10 V 1210,\n")
        fh.write("`RSM-6K98-1PCT-250MW-1206` = 6.98 kOhm 1% 250 mW 1206.\n\n")
        fh.write("```csv\n")
        with open(os.path.join(out, "parts_census.csv"), encoding="utf-8", newline="") as cf:
            fh.write(cf.read())
        fh.write("```\n\n")
        fh.write("## 2. BOM rows that carry a DigiKey number\n\n```csv\n")
        with open(os.path.join(out, "bom_rows.csv"), encoding="utf-8", newline="") as bf:
            fh.write(bf.read())
        fh.write("```\n\n")
        fh.write("## 3. non-passive part types (the datasheet target list)\n\n")
        targets = sorted({t for t in types.values() if not t.startswith(PASSIVE_PREFIX)})
        for t in targets:
            fh.write(f"- `{t}`\n")
        fh.write(f"\nTOTALS: part_types={len(set(types.values()))} "
                 f"designators={len(types)} non_passive_types={len(targets)}\n")


def write_manifest(out: str) -> int:
    import hashlib
    rows = []
    for root, _, files in os.walk(out):
        for fn in sorted(files):
            if fn == "MANIFEST.csv":
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, out).replace("\\", "/")
            data = open(p, "rb").read()
            first = data.split(b"\n", 1)[0].decode("utf-8", "replace").strip()
            rows.append((rel, len(data), hashlib.sha256(data).hexdigest(), first[:90]))
    with open(os.path.join(out, "MANIFEST.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "bytes", "sha256", "first_line"])
        w.writerows(sorted(rows))
    return len(rows)



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
    write_merged(a.out, nb, types, lines, parts, parttypes, decals)
    n_manifest = write_manifest(a.out)

    # Self-check the merged files: what they claim to contain must be what they do contain.
    problems = []
    c = open(os.path.join(a.out, "TASK_C_ic_context_all.md"), encoding="utf-8").read()
    f = open(os.path.join(a.out, "TASK_F_decal_raw_all.md"), encoding="utf-8").read()
    abe = open(os.path.join(a.out, "TASK_ABE_census_and_bom.md"), encoding="utf-8").read()
    if c.count("\n## ") != len(IC_TOPICS) or f"TOTALS: sections={len(IC_TOPICS)}" not in c:
        problems.append(f"TASK_C sections={c.count(chr(10) + '## ')} expected {len(IC_TOPICS)}")
    for ref in IC_TOPICS:
        if f"## {ref} " not in c:
            problems.append(f"TASK_C missing section {ref}")
    if "TOTALS: decals=" not in f:
        problems.append("TASK_F has no TOTALS line")
    if "TOTALS: part_types=" not in abe or "digikey" not in abe or "part_type,qty" not in abe:
        problems.append("TASK_ABE is missing census or BOM content")
    print(f"merged  : TASK_C sections={c.count(chr(10) + '## ')}  "
          f"TASK_F decals={f.count(chr(10) + '## ')}  manifest rows={n_manifest}")
    if problems:
        print("ERROR merged pack self-check failed:")
        for p in problems:
            print("  -", p)
        return 3

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
