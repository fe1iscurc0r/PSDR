#!/usr/bin/env python3
"""Cross-check every designator's value across the three sources we actually have.

Why this exists: the delegate answers for TASK C came back with dozens of rows judged
"信息不足" because our pack only carried the PADS *part type* (`RES_0603`, `CAP_0603`)
and never the value. The values are in the board file, and they are in the BOM - but
the BOM lists them in grouped refdes rows inside a binary .xls, so nobody had joined
the two. This tool does the join and reports where the sources disagree.

Sources (all committed, no .xls reading needed):
  Hardware/PSDR.asc                                PART blocks: Value / Comment
  Hardware/BOMs/PSDR_2.6.1/PSDR2.6_BOM_flat.csv     refdes groups + value  (flattened .xls)
  Hardware/BOMs/PSDR_2.6.1/PSDR2.6.1_BOM_flat.csv   same, 2.6.1

Output: Hardware/BOMs/PSDR_2.6.1/BOM_refdes_crosscheck.csv with columns
  refdes, bom_2_6, bom_2_6_1, asc_value, asc_comment, flags

Refdes groups in the BOM read like `C3,10,13,238-240` or the 2.6 typo `R97,-99`;
both forms are expanded here, which is also what shows the typo's real membership.

Usage: python tools/bom_refdes_crosscheck.py [--asc ...] [--bom26 ...] [--bom261 ...] [--out ...]
"""
import argparse
import csv
import os
import re
import sys

SCALE = {"R": 1.0, "K": 1e3, "M": 1e6, "U": 1e-6, "N": 1e-9, "P": 1e-12}
# words that mean "not fitted" rather than a value
DNF = {"OPEN", "DNS", "DNP", "NC", "NA"}


def canon(raw: str) -> str:
    """Normalise a value string so `1K0`/`1k`/`100R 1/4W` compare equal to their BOM twin."""
    if not raw:
        return ""
    s = re.sub(r"\s+", "", str(raw).upper())
    s = re.sub(r"(1/4W|1/8W|1/10W|NTC|OHMS|Ω)", "", s)
    if s in DNF:
        return s
    m = re.match(r"^(\d+)([RKMUNP])(\d+)$", s)          # EIA decimal-letter: 1K0, 12K1, 2P2
    if m:
        return repr(float(f"{m.group(1)}.{m.group(3)}") * SCALE[m.group(2)])
    m = re.match(r"^(\d+(?:\.\d+)?)([RKMUNP])$", s)
    if m:
        return repr(float(m.group(1)) * SCALE[m.group(2)])
    return s


def asc_part_values(path: str) -> dict:
    """Return {refdes: (value, comment)} from `PART <refdes>` blocks in the board file."""
    out: dict = {}
    cur = None
    depth = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r"^PART (\S+)\s*$", line)
            if m:
                cur, depth = m.group(1), 0
                out[cur] = ["", ""]
                continue
            if cur is None:
                continue
            t = line.strip()
            if t == "{":
                depth += 1
                continue
            if t == "}":
                depth -= 1
                if depth <= 0:
                    cur = None
                continue
            kv = re.match(r"^(Value|Comment)\s+(.*)$", t)
            if kv and depth >= 1:
                idx = 0 if kv.group(1) == "Value" else 1
                out[cur][idx] = kv.group(2).strip()
    return out


def expand(spec: str):
    """Expand a BOM `Ref Des` cell. Handles prefixes, ranges, bare numbers and `-99` shorthand."""
    refs, prefix, last = [], "", 0
    for tok in re.split(r"[;,]", str(spec)):
        t = tok.strip()
        if not t:
            continue
        m = re.match(r"^([A-Z]+)(\d+)\s*-\s*(?:[A-Z]+)?(\d+)$", t)      # R310-313
        if m:
            refs += [m.group(1) + str(n) for n in range(int(m.group(2)), int(m.group(3)) + 1)]
            prefix, last = m.group(1), int(m.group(3))
            continue
        m = re.match(r"^-(\d+)$", t)                                     # the 2.6 typo: R97,-99
        if m and prefix:
            refs += [prefix + str(n) for n in range(last + 1, int(m.group(1)) + 1)]
            last = int(m.group(1))
            continue
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", t)                          # C238-240 (no prefix)
        if m and prefix:
            refs += [prefix + str(n) for n in range(int(m.group(1)), int(m.group(2)) + 1)]
            last = int(m.group(2))
            continue
        m = re.match(r"^(\d+)$", t)                                      # C3,10,13 -> 10, 13
        if m and prefix:
            refs.append(prefix + m.group(1))
            last = int(m.group(1))
            continue
        m = re.match(r"^([A-Z]+)(\d+)$", t)
        if m:
            refs.append(t)
            prefix, last = m.group(1), int(m.group(2))
            continue
        refs.append(t)                                                   # named nodes: ANT/VNA-IN
    return refs


def read_flat_bom(path: str):
    """Read a flattened BOM csv, dropping the leading `#` provenance comment lines."""
    with open(path, encoding="utf-8", newline="") as fh:
        return [r for r in csv.reader(ln for ln in fh if not ln.startswith("#"))]


def bom_index(rows) -> dict:
    """Return {refdes: value} from flattened BOM rows (header found by name)."""
    hdr_i = next(i for i, r in enumerate(rows) if any(c.strip().lower().replace("_", " ") == "ref des" for c in r))
    hdr = [c.strip().lower().replace("_", " ") for c in rows[hdr_i]]
    ref_c = hdr.index("ref des")
    val_c = hdr.index("value") if "value" in hdr else None
    type_c = hdr.index("type") if "type" in hdr else None
    out = {}
    for r in rows[hdr_i + 1:]:
        if len(r) <= ref_c or not r[ref_c].strip():
            continue
        value = r[val_c].strip() if val_c is not None and len(r) > val_c else ""
        ptype = r[type_c].strip() if type_c is not None and len(r) > type_c else ""
        for ref in expand(r[ref_c]):
            out.setdefault(ref, {"value": value, "type": ptype})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asc", default="Hardware/PSDR.asc")
    ap.add_argument("--bom26", default="Hardware/BOMs/PSDR_2.6.1/PSDR2.6_BOM_flat.csv")
    ap.add_argument("--bom261", default="Hardware/BOMs/PSDR_2.6.1/PSDR2.6.1_BOM_flat.csv")
    ap.add_argument("--out", default="Hardware/BOMs/PSDR_2.6.1/BOM_refdes_crosscheck.csv")
    a = ap.parse_args()

    for p in (a.asc, a.bom26, a.bom261):
        if not os.path.exists(p):
            print(f"ERROR missing input: {p}", file=sys.stderr)
            return 2

    asc = asc_part_values(a.asc)
    b26, b261 = bom_index(read_flat_bom(a.bom26)), bom_index(read_flat_bom(a.bom261))
    refs = sorted(set(asc) | set(b261) | set(b26))

    stats = {"agree": 0, "mismatch": 0, "asc_only": 0, "bom_only": 0, "no_value": 0}
    rows_out, mismatches = [], []
    for ref in refs:
        av, ac = asc.get(ref, ("", ""))
        v26 = b26.get(ref, {}).get("value", "")
        v261 = b261.get(ref, {}).get("value", "")
        flags = []
        if av and v261:
            if canon(av) == canon(v261):
                stats["agree"] += 1
            else:
                flags.append("ASC!=BOM2.6.1")
                stats["mismatch"] += 1
        elif av and not v261:
            stats["asc_only"] += 1
            flags.append("no-bom-value")
        elif v261 and not av:
            stats["bom_only"] += 1
            flags.append("no-asc-value")
        else:
            stats["no_value"] += 1
            flags.append("no-value-either")
        if v26 and v261 and canon(v26) != canon(v261):
            flags.append("2.6->2.6.1-changed")
        if "ASC!=BOM2.6.1" in flags:
            mismatches.append((ref, v26, v261, av, ac))
        rows_out.append([ref, v26, v261, av, ac, "|".join(flags)])

    with open(a.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["refdes", "bom_2_6", "bom_2_6_1", "asc_value", "asc_comment", "flags"])
        w.writerows(rows_out)

    print(f"designators joined : {len(refs)}")
    print(f"asc == 2.6.1 BOM   : {stats['agree']}")
    print(f"asc != 2.6.1 BOM   : {stats['mismatch']}")
    print(f"value only in asc  : {stats['asc_only']}   only in BOM: {stats['bom_only']}"
          f"   neither: {stats['no_value']}")
    print(f"\nwrote {a.out} ({len(rows_out)} rows)")
    if mismatches:
        print("\n=== where the board file and the 2.6.1 BOM disagree ===")
        print("refdes | 2.6 BOM | 2.6.1 BOM | .asc Value | .asc Comment")
        for m in mismatches:
            print(" | ".join(x or "-" for x in m))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
