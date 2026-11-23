#!/usr/bin/env python3
"""Join the 2.6.1 BOM with assembly_class.csv into one procurement checklist.

Output rows are BOM rows (grouped refdes kept), enriched with:
  - dnp: explicit "do not populate" / "DNP by design" / value OPEN/DNS
  - assembly_cls: per-refdes class counts from assembly_class.csv
  - sourcing: known unobtainium flags (assembly-sourcing.md §3)
  - value_conflict: refdes whose value differs across sch/asc/BOM (threeway scan)

Usage: python tools/bom_procurement_list.py [--bom ...] [--class ...] [--threeway ...] [--out ...]
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bom_refdes_crosscheck import expand, read_flat_bom

UNOBTAINIUM = {
    "U304": "SXB-2089Z 停产，原厂页撤档；替代调研中",
    "U16": "MASWSS0129 停产撤档；替代调研中",
    "U24": "MASWSS0129 停产撤档；替代调研中",
    "U30": "MASWSS0129 停产撤档；替代调研中",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bom", default="Hardware/BOMs/PSDR_2.6.1/PSDR2.6.1_BOM_flat.csv")
    ap.add_argument("--class", dest="cls", default="Hardware/BOMs/PSDR_2.6.1/assembly_class.csv")
    ap.add_argument("--threeway", default="Hardware/BOMs/PSDR_2.6.1/value_threeway_sch_asc_bom.csv")
    ap.add_argument("--out", default="Hardware/BOMs/PSDR_2.6.1/procurement_checklist.csv")
    a = ap.parse_args()
    for p in (a.bom, a.cls, a.threeway):
        if not os.path.exists(p):
            print(f"ERROR missing input: {p}", file=sys.stderr)
            return 2

    rows = read_flat_bom(a.bom)
    hdr = [c.strip() for c in rows[0]]
    idx = {name: i for i, name in enumerate(hdr) if name}
    notes_i = idx["value"] + 1  # unnamed remarks column right after value

    cls = {}
    with open(a.cls, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            cls[r["designator"]] = r["cls"]

    contested = {}
    with open(a.threeway, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("status") in ("layout-alone", "bom-alone", "all-differ"):
                contested[r["refdes"]] = r["status"]

    out_rows = []
    stats = Counter()
    cost_pop = cost_dnp = 0.0
    for r in rows[1:]:
        if len(r) < len(hdr) or not r[idx["ref_des"]].strip():
            continue
        refs = expand(r[idx["ref_des"]])
        note = r[notes_i] if len(r) > notes_i else ""
        value = r[idx["value"]].strip()
        dnp_reason = ""
        low = note.lower()
        if "do not populate" in low or "dnp by design" in low:
            dnp_reason = note.strip()
        elif value.upper() in ("OPEN", "DNS", "DNP", "NA"):
            dnp_reason = f"value={value}"
        classes = Counter(cls.get(x, "?") for x in refs)
        cls_str = ",".join(f"{k}x{v}" for k, v in sorted(classes.items()))
        sourcing = "; ".join(sorted({UNOBTAINIUM[x] for x in refs if x in UNOBTAINIUM}))
        conflicts = "; ".join(f"{x}:{contested[x]}" for x in refs if x in contested)
        qty = int(r[idx["qty_per_unit"]])
        if qty == 0:
            stats["qty0_rows"] += 1
            dnp_reason = dnp_reason or "qty_per_unit=0（备用/替代条目，不采购）"
        try:
            unit = float(r[idx["cost_x1"]]) if r[idx["cost_x1"]].strip() else 0.0
        except ValueError:
            unit = 0.0
        line_cost = qty * unit
        if dnp_reason:
            stats["dnp_rows"] += 1
            cost_dnp += line_cost
        else:
            stats["populated_rows"] += 1
            cost_pop += line_cost
        stats["refdes_total"] += len(refs)
        if sourcing:
            stats["unobtainium_rows"] += 1
        out_rows.append({
            "item_no": r[idx["item_no."]],
            "ref_des": r[idx["ref_des"]],
            "qty_per_unit": qty,
            "type": r[idx["type"]],
            "value": value,
            "mfg_part": r[idx["mfg_part_#"]],
            "vendor_part": r[idx["vendor_part_#"]],
            "dnp": "YES" if dnp_reason else "",
            "dnp_reason": dnp_reason,
            "assembly_cls": cls_str,
            "sourcing_flag": sourcing,
            "value_conflict": conflicts,
            "notes": note,
            "cost_x1_usd_2016": r[idx["cost_x1"]],
            "line_cost_usd_2016": f"{line_cost:.2f}",
        })

    with open(a.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    summary = (
        f"rows={len(out_rows)} populated={stats['populated_rows']} dnp={stats['dnp_rows']} "
        f"refdes_total={stats['refdes_total']} unobtainium_rows={stats['unobtainium_rows']}\n"
        f"cost_2016_usd: populated={cost_pop:.2f} dnp={cost_dnp:.2f}\n"
    )
    with open(a.out + ".summary.txt", "w", encoding="utf-8") as fh:
        fh.write(summary)
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())