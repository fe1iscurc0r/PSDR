#!/usr/bin/env python3
"""Emit an SMT placement (pick-and-place) table from the PADS Layout ASCII.

Every row is one part from the ``*PART*`` section of ``Hardware/PSDR.asc``, so the
coordinates are the design's own -- no Gerber or KiCad interpolation.  Units and
conventions, all stated because a placement file is only correct together with
them:

* the ASCII stores 38100 integer units per mil (derived in :mod:`pads_asc_pcb`);
* PADS Y grows **up**, KiCad/board-fabrication Y grows down -- this file keeps the
  PADS sense, and `MidY` is measured from the board outline's lowest vertex;
* the origin is the bounding box of the single ``BOARD`` polygon in *LINES*, i.e.
  ``MidX = MidY = 0`` is the board's lower-left corner, not a corner of the
  100.00 x 65.00 mm rectangle unless the outline starts there (it does not, hence
  the outline extent is printed on stderr);
* ``Rotation`` is the part's ``ORI`` as PADS stores it; ``Side`` is ``Top`` or
  ``Bottom`` from the U/D field and ``M`` from the mirror field;
* ``Footprint`` is the PADS decal (padstack) name, which is what the stencil and
  the reflow profile are keyed on.

With ``--bom-csv`` the tool additionally expands the Ref Des cells of a BOM CSV
export (``Ref Des`` holding e.g. ``C3,10,13-17`` or ``R97-99``) and reports the
difference against the board's designators, because a placement file that does not
agree with the BOM is a factory stoppage.

Usage:
    python3 tools/pads_asc_placement.py Hardware/PSDR.asc --out placement.csv
    python3 tools/pads_asc_placement.py Hardware/PSDR.asc \
        --bom-csv PSDR2.6.1_BOM.csv --out placement.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from pads_asc_decal import UNITS_PER_MIL, parse_parts  # noqa: E402
from pads_asc_pcb import parse_outline  # noqa: E402

TOKEN = re.compile(r"^([A-Z]+)?(\d+)(?:-([A-Z]+)?(\d+))?$")


def expand_refdes(cell: str) -> list[str]:
    """Expand one ``Ref Des`` cell: 'C3,10,13-17' -> C3 C10 C13 C14 C15 C16 C17."""
    out: list[str] = []
    prefix = None
    for raw in cell.split(","):
        tok = raw.strip()
        if not tok:
            continue
        m = TOKEN.match(tok)
        if not m:
            out.append(tok)
            continue
        pre, start, pre2, end = m.groups()
        prefix = pre or prefix
        if end is None:
            out.append(f"{prefix}{int(start)}")
        else:
            if pre2 and pre2 != prefix:
                raise SystemExit(f"range prefix mismatch in {cell!r}")
            out.extend(f"{prefix}{i}" for i in range(int(start), int(end) + 1))
    return out


def bom_designators(path: str) -> tuple[set[str], list[str]]:
    """Return the designator set of a BOM CSV export plus the rows behind them."""
    rows = list(csv.reader(open(path, encoding="utf-8", errors="replace")))
    header_row = next(i for i, r in enumerate(rows) if r and r[0] == "Item No.")
    header = rows[header_row]
    ref_col = header.index("Ref Des")
    found, items = set(), []
    for r in rows[header_row + 1:]:
        if len(r) <= ref_col or not r[ref_col].strip():
            continue
        for ref in expand_refdes(r[ref_col]):
            found.add(ref)
            items.append((ref, r[0]))
    return found, items


def classify(decal: str, pins: int) -> str:
    """Padstack class, used to explain any designator that the BOM does not carry."""
    if decal.startswith("FIDUCIAL"):
        return "FIDUCIAL"
    if decal.startswith("MH") or "PADDLE" in decal:
        return "MOUNTING_HARDWARE"
    if pins <= 1 and (decal.startswith("PAD_") or "1PIN" in decal):
        return "SINGLE_PAD"      # test point / net tie: one pad, no purchased part
    return "PURCHASED"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("asc")
    ap.add_argument("--out", required=True)
    ap.add_argument("--bom-csv")
    args = ap.parse_args()

    lines = open(args.asc, encoding="latin-1").read().splitlines()
    parts = parse_parts(lines)
    points = []
    for seg in parse_outline(lines):
        for pt in seg[1:]:
            points.append(pt if isinstance(pt, tuple) else pt)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, y0 = min(xs), min(ys)
    print("BOARD outline extent (mil): %.2f x %.2f -> %.3f x %.3f mm, origin (%.0f, %.0f)"
          % ((max(xs) - x0) / UNITS_PER_MIL, (max(ys) - y0) / UNITS_PER_MIL,
             (max(xs) - x0) / UNITS_PER_MIL * 0.0254,
             (max(ys) - y0) / UNITS_PER_MIL * 0.0254,
             x0 / UNITS_PER_MIL, y0 / UNITS_PER_MIL))

    # Pin counts decide SINGLE_PAD, so read them from the routing of the same file.
    from pads_asc_netlist import parse_route, section  # noqa: E402

    i_route = section(lines, "*ROUTE*")
    i_end = next((i for i in range(i_route, len(lines))
                  if lines[i].startswith(("*MISC*", "*END*"))), len(lines))
    nets, _clusters = parse_route(lines, i_route, i_end)
    pin_count: dict[str, int] = {}
    for members in nets.values():
        seen = set()
        for m in members:
            ref = m[0] if isinstance(m, (tuple, list)) else m.get("refdes")
            pin = m[1] if isinstance(m, (tuple, list)) else m.get("pin")
            if (ref, pin) not in seen:
                seen.add((ref, pin))
                pin_count[ref] = pin_count.get(ref, 0) + 1

    rows_out = []
    for ref in sorted(parts, key=lambda r: (re.sub(r"\D", "", r).zfill(6), r)):
        p = parts[ref]
        rows_out.append({
            "Designator": ref,
            "Footprint": p["type"],
            "MidX_mm": f"{(p['x'] - x0) / UNITS_PER_MIL * 0.0254:.3f}",
            "MidY_mm": f"{(p['y'] - y0) / UNITS_PER_MIL * 0.0254:.3f}",
            "Rotation": f"{p['ori']:.1f}",
            "Side": "Bottom" if p.get("mirror") == "M" else "Top",
            "Class": classify(p["type"], pin_count.get(ref, 0)),
            "PadsOnNet": pin_count.get(ref, 0),
            "MirrorFlag": p.get("mirror", "N"),
            "PadX_mil": p["x"],
            "PadY_mil": p["y"],
        })

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    from collections import Counter
    print("wrote %s: %d parts | %s" % (
        args.out, len(rows_out),
        " ".join(f"{k}={v}" for k, v in sorted(Counter(r["Class"] for r in rows_out).items()))))

    if args.bom_csv:
        bom_set, items = bom_designators(args.bom_csv)
        named_rows = sorted(r for r in bom_set if not re.search(r"\d", r))
        bom_refs = bom_set - set(named_rows)
        board_set = set(parts)
        # The BOM lists some single-instance connectors by NAME instead of by a
        # numbered designator (USB, MICROSD, BOOT, ANT/VNA-IN, ...).  Match those
        # against the board rather than treating them as missing designators.
        name_hits = {n: sorted(r for r in board_set
                               if r.upper().replace(" ", "") == n.upper().replace(" ", "")
                               or r.upper().startswith(n.upper().split("/")[0]))
                     for n in named_rows}
        covered = bom_refs | {r for hits in name_hits.values() for r in hits}
        unexplained = sorted(r["Designator"] for r in rows_out
                             if r["Class"] == "PURCHASED" and r["Designator"] not in covered)
        orphan_rows = sorted(n for n, h in name_hits.items() if not h)
        not_covered = sorted(board_set - covered)
        outside = [r for r in rows_out if r["Designator"] in set(not_covered)]
        print("BOM: %d expanded rows -> %d numbered designators + %d rows naming an "
              "assembly/part instead" % (len(items), len(bom_refs), len(named_rows)))
        print("board parts %d | covered by BOM %d | outside BOM by class: %s"
              % (len(board_set), len(board_set) - len(not_covered),
                 dict(Counter(r["Class"] for r in outside))))
        for n in orphan_rows:
            print("  BOM row %r has no main-board part (separate assembly or cable)" % n)
        print("RECONCILIATION: %s" % (
            "every purchased part on the board is covered by the BOM; the objects outside "
            "the BOM are only fiducials, mounting hardware and single-pad test points"
            if not unexplained else
            f"DIFFERS -- purchased parts with no BOM row: {unexplained[:12]}"))
        return 0 if not unexplained else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
