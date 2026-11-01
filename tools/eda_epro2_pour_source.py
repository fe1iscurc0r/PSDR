#!/usr/bin/env python3
"""Give a converted JLCEDA Pro .epro2 the pour precedence of the PADS source.

Why this exists: the EDA KiCad importer throws both pour attributes away.
It ignores the zone's ``island_removal_mode`` (converted output is
``keepIsland: false`` for every pour whether the board says 0 or 1) and it
ignores zone priority, numbering the pours 1..12 in file order instead.  EDA
resolves overlapping pours of different nets with the SMALLER ``order`` winning,
so the last-numbered pours lose their whole area and come back with zero copper
- on this board ``+3V3_FLIP_FLOP`` (In1) and ``V_SUPPLY`` (F.Cu).

The PADS route of the same converter proves the intended numbers: it copies the
trailing field of each ``POUROUT`` record into ``order`` (missing field = 0) and
takes ``keepIsland`` from ``PLANEFLAGS``.  This script applies exactly that rule
to a KiCad-route ``.epro2``, matched per pour by (net, layer, polygon area), so
an imported project reproduces the source precedence without hand edits.

Only matched POUR payloads are touched; every other record is copied verbatim.
"""
import argparse
import json
import os
import re
import sys
import zipfile

MIL_PER_UNIT = 1.0 / 38100.0
# PADS copper layer number -> JLCEDA Pro layerId (TOP=1, BOTTOM=2, inner=15..).
LAYER_ID = {1: 1, 2: 15, 3: 16, 4: 2}
POUR_HEAD = re.compile(r"^\S+\s+POUROUT\s+(\S+)\s+(\S+)\s+\S+\s+\S+\s+\S+\s+(\S+)"
                       r"(?:\s+(\S+)\s+(\S+)\s+(\S+))?\s*$")
POLY_HEAD = re.compile(r"^POLY\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)")


def source_pours(asc_path):
    """Return ([(net, layerId, area_mil2, order)], keep_island).

    Vertices are absolute because PADS stores them relative to the record's
    XLOC/YLOC; the area is the shoelace value used to match pours later.
    """
    lines = open(asc_path, encoding="latin-1").read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("*POUR*"))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith("*TESTPOINT*"))
    keep = False
    for line in lines:
        if line.startswith("PLANEFLAGS"):
            keep = line.split()[3] == "N"
            break
    pours = []
    i = start
    while i < end:
        m = POUR_HEAD.match(lines[i])
        if not m:
            i += 1
            continue
        xloc, yloc, net = int(m.group(1)), int(m.group(2)), m.group(3)
        order = int(m.group(6)) if m.group(6) else 0
        i += 1
        poly = POLY_HEAD.match(lines[i].strip())
        if not poly:
            raise SystemExit(f"pour {net}: expected a POLY line")
        count, _arcs, _width, level = (int(v) for v in poly.groups())
        pts = []
        for k in range(count):
            row = [int(v) for v in lines[i + 1 + k].split()]
            pts.append(((row[0] + xloc) * MIL_PER_UNIT, (row[1] + yloc) * MIL_PER_UNIT))
        if pts[0] != pts[-1]:
            raise SystemExit(f"pour {net}: polygon is not closed")
        pts = pts[:-1]
        area = 0.0
        for a in range(len(pts)):
            x1, y1 = pts[a]
            x2, y2 = pts[(a + 1) % len(pts)]
            area += x1 * y2 - x2 * y1
        pours.append((net, LAYER_ID[level], abs(area) / 2.0, order))
        i += 1 + count
    return pours, keep


def path_area(payload):
    """Shoelace area in mil^2 of an EDA pour path."""
    pts = []
    for seg in payload.get("path") or []:
        nums = [v for v in seg if isinstance(v, (int, float))]
        pts.extend((x, y) for x, y in zip(nums[0::2], nums[1::2]))
    area = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def match(net, layer, area, wanted):
    """Pick the source pour with the same net/layer and the closest area."""
    cands = [w for w in wanted if w[0] == net and w[1] == layer]
    if not cands:
        return None
    return min(cands, key=lambda w: abs(w[2] - area) / max(area, 1.0))


def patch(text, wanted, keep_island, taken):
    out, rows = [], []
    for line in text.split("\n"):
        if not line.strip():
            out.append(line)
            continue
        parts = line.split("||")
        try:
            head = json.loads(parts[0])
        except ValueError:
            out.append(line)
            continue
        if head.get("type") != "POUR" or len(parts) < 2:
            out.append(line)
            continue
        payload = json.loads(parts[1].rstrip("|"))
        net, layer = payload.get("netName"), payload.get("layerId")
        hit = match(net, layer, path_area(payload), wanted)
        if not hit or hit in taken:
            rows.append((net, layer, payload.get("order"), None))
            out.append(line)
            continue
        taken.add(hit)
        new = line
        for field, want in (("order", hit[3]), ("keepIsland", keep_island)):
            old = json.loads(new.split("||")[1].rstrip("|"))[field]
            if old == want:
                continue
            a, b = f'"{field}":{json.dumps(old)}', f'"{field}":{json.dumps(want)}'
            if a not in new:
                raise SystemExit(f"{net}: cannot rewrite {field}")
            new = new.replace(a, b, 1)
        rows.append((net, layer, payload.get("order"), hit[3]))
        out.append(new)
    return "\n".join(out), rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src_epro2")
    ap.add_argument("dst_epro2")
    ap.add_argument("--asc", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Hardware", "PSDR.asc"))
    args = ap.parse_args()

    wanted, keep_island = source_pours(args.asc)
    taken = set()
    with zipfile.ZipFile(args.src_epro2) as zin:
        epru = next(n for n in zin.namelist() if n.endswith(".epru"))
        text = zin.read(epru).decode("utf-8")
        new_text, rows = patch(text, wanted, keep_island, taken)
        with zipfile.ZipFile(args.dst_epro2, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename == epru:
                    data = new_text.encode("utf-8")
                zout.writestr(info, data)

    print(f"source: {len(wanted)} POUROUT records, keepIsland={keep_island}")
    unmatched = [w for w in wanted if w not in taken]
    print(f'{"net":16s} {"layer":6s} {"file order":11s} {"source order":12s}')
    for net, layer, before, after in rows:
        mark = "" if after is not None else "   (no source match, left as is)"
        print(f"{net:16s} {layer:6d} {before:11d} "
              f"{(after if after is not None else -1):12d}{mark}")
    if unmatched:
        print("source pours never matched in the file:", unmatched)
    print("wrote", args.dst_epro2)


if __name__ == "__main__":
    sys.exit(main())
