#!/usr/bin/env python3
"""Compare a KiCad plot of Hardware/PSDR.asc with the original 2.6.1 Gerbers.

The two sides come from the same layout database but not from the same file
format, so this script measures rather than assumes the relationship:

* the PADS Gerbers are 1000 mil above/right of the ASCII frame, on both axes,
  with no flip -- checked by comparing the extents of the copper flashes;
* a KiCad plot uses one D03 flash per pad per layer and per via, while PADS
  draws custom decals with D01 strokes and only flashes simple apertures.
  Therefore the check is one-directional on flashes: every source flash must
  have a KiCad flash at the same place.  The reverse count is printed so the
  difference stays visible instead of being hidden behind a pass/fail;
* drills are compared per diameter with a 0.1 mil tolerance, because the PADS
  Excellon file is 2.4 inch (0.1 mil resolution).

Usage::

    python tools/kicad_gerber_compare.py \
        --pads "D:/.../Hardware/Gerbers/PSDR261 Main Board" \
        --fab  <export dir>

``--fab`` must contain the Gerber and drill files produced by::

    kicad-cli pcb export gerbers --no-protel-ext \
        -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask -o <fab> <board>
    kicad-cli pcb export drill -o <fab> <board>
"""

import argparse
import collections
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerbparse  # noqa: E402

# KiCad layer suffix -> PADS source file (2.6.1 "PSDR261 Main Board").
LAYERS = [
    ("F_Cu", "3 - top-art.GTL"),
    ("In1_Cu", "4 - L2.p.G1"),
    ("In2_Cu", "5 - L3.G2"),
    ("B_Cu", "6 - bot-art.GBL"),
    ("F_Mask", "2 - top-sm.GTS"),
    ("B_Mask", "7 - bot-sm.GBS"),
]
PADS_SHIFT_MIL = 1000.0
MATCH_MIL = 0.1


def nearest(point, points):
    x, y = point
    return min(math.hypot(x - u, y - v) for (u, v) in points)


def coverage(src, dst):
    """Nearest-distance coverage of every source item, allowing reuse of dst.

    Reuse matters: PADS writes two identical 62 mil mask flashes on top of each
    other at two points, while KiCad plots one opening there.  A greedy
    one-to-one match would call the second copy "missing"; the dup column in the
    table shows how many source flashes are exact duplicates.
    """
    missing = []
    worst = 0.0
    for point in src:
        d = nearest(point, dst)
        worst = max(worst, d)
        if d > MATCH_MIL:
            missing.append((point, d))
    return missing, worst


def ki_flashes(path):
    return [(s.x * 1000.0, s.y * 1000.0) for s in gerbparse.load(path).flashes()]


def pads_flashes(path):
    return [(s.x * 1000.0 - PADS_SHIFT_MIL, s.y * 1000.0 - PADS_SHIFT_MIL)
            for s in gerbparse.load(path).flashes()]


def parse_drill(path, definition_selects=False):
    """Return {diameter_mm: [(x_mil, y_mil), ...]} for PADS or KiCad Excellon.

    KiCad writes the tool definition (``TnC<size>``) and the selection (``Tn``)
    on separate lines; PADS puts both on the definition line and has no bare
    ``Tn`` after the header.  Unit and number format also differ: PADS here is
    INCH with a 2.4 integer (leading zeros), KiCad is METRIC decimal.
    """
    text = open(path, "r", encoding="latin-1").read()
    metric = re.search(r"^\s*METRIC", text, re.M) is not None
    unit = 25.4 if metric else 1.0           # file units per inch, for coordinates
    mm_per_unit = 1.0 if metric else 25.4    # for tool diameters
    hit = collections.defaultdict(list)
    tool_of = {}
    cur = None
    x = y = 0.0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith((";", "%", "M30")):
            continue
        m = re.match(r"T(\d+)C([0-9.]+)", line)
        if m:
            tool_of[int(m.group(1))] = round(float(m.group(2)) * mm_per_unit, 3)
            if definition_selects:
                cur = tool_of[int(m.group(1))]
            continue
        m = re.match(r"T(\d+)$", line)
        if m:
            cur = tool_of[int(m.group(1))]
            continue
        m = re.match(r"X(-?[0-9.]+)?Y(-?[0-9.]+)?$", line)
        if not m or cur is None or not (m.group(1) or m.group(2)):
            continue
        if m.group(1):
            x = float(m.group(1)) if "." in m.group(1) else int(m.group(1)) / 1e4
            x = x / unit * 1000.0                  # inches/mm -> mil
        if m.group(2):
            y = float(m.group(2)) if "." in m.group(2) else int(m.group(2)) / 1e4
            y = y / unit * 1000.0
        hit[cur].append((x, y))
    return hit


def match(a, b):
    """Greedy nearest-neighbour matching; returns (missing, leftover, worst)."""
    b = list(b)
    missing = []
    worst = 0.0
    for point in a:
        if not b:
            missing.append((point, None))
            continue
        d, i = min((math.hypot(point[0] - u, point[1] - v), j)
                   for j, (u, v) in enumerate(b))
        if d <= MATCH_MIL:
            worst = max(worst, d)
            b.pop(i)
        else:
            missing.append((point, d))
    return missing, b, worst


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pads", required=True, help="2.6.1 PADS Gerber directory")
    ap.add_argument("--fab", required=True, help="KiCad Gerber/drill export directory")
    ap.add_argument("--board", default="PSDR_2.6.1_pcb_spike_full",
                    help="file stem used by the KiCad plot")
    args = ap.parse_args()

    print("flash: source flash -> nearest KiCad flash")
    print("%-8s %-22s %6s %7s %4s %10s" % ("layer", "pads file", "src#", "kicad#", "dup", "worst mil"))
    flash_missing = 0
    for layer, source in LAYERS:
        s = pads_flashes(os.path.join(args.pads, source))
        k = ki_flashes(os.path.join(args.fab, args.board + "-" + layer + ".gbr"))
        missing, worst = coverage(s, k)
        flash_missing += len(missing)
        print("%-8s %-22s %6d %7d %4d %10.4f" % (
            layer, source, len(s), len(k), len(s) - len(set(s)), worst))
        for point, d in missing[:5]:
            print("   MISSING", point, "nearest", round(d, 3))

    print("\ndrill: per diameter")
    s = parse_drill(os.path.join(args.pads, "0 - drillfile.TXT"), definition_selects=True)
    s = {size: [(x - PADS_SHIFT_MIL, y - PADS_SHIFT_MIL) for (x, y) in hits]
         for size, hits in s.items()}
    k = parse_drill(os.path.join(args.fab, args.board + ".drl"))
    print("%8s %6s %6s %8s %6s %10s" % ("mm", "src#", "kicad#", "missing", "extra", "worst mil"))
    total_src = total_missing = 0
    for size in sorted(set(s) | set(k)):
        missing, leftover, worst = match(s.get(size, []), k.get(size, []))
        total_src += len(s.get(size, []))
        total_missing += len(missing)
        print("%8.3f %6d %6d %8d %6d %10.4f" % (
            size, len(s.get(size, [])), len(k.get(size, [])),
            len(missing), len(leftover), worst))
        for point, d in missing:
            print("   MISSING %.3f mm at (%.2f, %.2f) mil = (%.2f, %.2f) mm"
                  % (size, point[0], point[1], point[0] / 1000 * 25.4, point[1] / 1000 * 25.4))
        for point in leftover:
            print("   EXTRA %.3f mm at (%.2f, %.2f) mil" % (size, point[0], point[1]))
    print("\nsource hits %d, missing %d" % (total_src, total_missing))
    print("RESULT:", "every source flash is covered and all drill hits match"
          if flash_missing == 0 and total_missing == 0
          else "%d source flash(es) uncovered, %d drill hit(s) missing"
               % (flash_missing, total_missing))


if __name__ == "__main__":
    main()
