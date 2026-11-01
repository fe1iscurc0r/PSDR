#!/usr/bin/env python3
"""Turn the PADS Layout ASCII *ROUTE* section into copper geometry.

Route records come in blocks:

    REF.PIN                         REF.PIN
    XLOC YLOC LAYER WIDTH FLAGS [ARCDIR/VIANAME] [TEARDROP ...]

The first point is the source pin, the last point is the destination pin, and
the points in between are track vertices.  Two of the LAYER codes are not
copper layers at all: ``0`` and ``65`` mark points that sit inside a pad (the
source and destination pin respectively).  A point whose line carries the
literal ``STANDARDVIA`` token is a via; the 0x10000 FLAGS bit is not a via
marker, see :func:`classify`.

A record's LAYER and WIDTH belong to the piece that *leaves* that point, not
the one that arrives at it.  On ``GND C119.2->U121.99`` the 16-mil record is
the one before the 8-mil trace starts, and the 2.6.1 Gerber draws the 16-mil
stroke between that point and the next.  That reading also explains why the
first point of a connection carries a real copper layer instead of a pad code.

For a via that layer is the one the route resumes on, so the arriving segment
keeps the previous record's layer.  All 419 distinct vias are through vias: the
drill file has exactly 419 14-mil holes, each at an ASCII via position +1000
mil, and the same 419 points are 32-mil round flashes on both outer layers.

A point whose line carries ``CW``/``CCW`` is not a vertex at all: it is the
**centre** of an arc joining the previous point to the next.  There are 22 of
them, all in *ROUTE*.  The token is read literally in PADS coordinates (y up);
the Gerber traverses the same arc the other way round, as it does for the
board outline.  Only 2 of the 22 centres disagree with the following vertex on
layer or width, and those are exactly an arc into a narrower trace and an arc
into a via, which is why an arc takes the centre record's values.
"""

import argparse
import collections
import math
import re
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from pads_asc_decal import UNITS_PER_MIL, parse_connections  # noqa: E402

PAD_LAYERS = (0, 65)
COPPER_LAYERS = (1, 2, 3, 4)
ARC = re.compile(r"\b(CW|CCW)\b")


def classify(pt):
    """The literal STANDARDVIA token is the via marker, CW/CCW marks an arc.

    The 0x10000 flag bit is **not** a via marker: it also rides on ordinary
    mid-track vertices (flags 0x10600) that stay on one layer.  Trusting the bit
    turned 1,164 real vias into 1,212 and invented 48 vias in the middle of
    straight runs.
    """
    text = pt["text"].upper()
    if ARC.search(text):
        return "arc"
    if "STANDARDVIA" in text:
        return "via"
    if pt["layer"] in PAD_LAYERS:
        return "pin"
    return "track"


def arc_ccw(pt):
    """True for a counter-clockwise arc in PADS coordinates (y up)."""
    return "CCW" in pt["text"].upper()


def arc_angles(start, centre, end, ccw):
    """Start and end angle, unwrapped in the arc's own direction."""
    a0 = math.atan2(start[1] - centre[1], start[0] - centre[0])
    a1 = math.atan2(end[1] - centre[1], end[0] - centre[0])
    if ccw:
        while a1 <= a0:
            a1 += 2 * math.pi
    else:
        while a1 >= a0:
            a1 -= 2 * math.pi
    return a0, a1


def arc_mid(start, centre, end, ccw):
    """A point halfway along the arc, in PADS coordinates."""
    a0, a1 = arc_angles(start, centre, end, ccw)
    am = (a0 + a1) / 2
    r = math.dist(start, centre)
    return (centre[0] + r * math.cos(am), centre[1] + r * math.sin(am))


def connections(lines):
    """Yield (net, ref_a, pin_a, ref_b, pin_b, points) with a kind per point."""
    for net, ra, pa, rb, pb, pts in parse_connections(lines):
        for pt in pts:
            pt["kind"] = classify(pt)
        yield net, ra, pa, rb, pb, pts


def route_geometry(pts):
    """Split one connection into straight lines, arcs and vias.

    A pad layer code at the start is not a copper vertex, and no copper leaves
    it.  The connections that begin with one are pad-to-pour links:
    ``C278.2->R116.2`` jumps 984 mil from the pad to the first via with no
    stroke in the Gerber, and 13 others are bare pad-to-pad entries.  The same
    holds for the one via recorded on layer 0, which ends in a pour.

    Returns
    -------
    lines  [(layer, (x1, y1), (x2, y2), width)]
    arcs   [(layer, (x1, y1), (cx, cy), (x2, y2), ccw, width)]
    vias   [(x, y, from_layer, to_layer)]   a layer is None when the via stops
           in a pour or follows a pad marker, so the record does not name it
    """
    chain = []
    for pt in pts:
        if pt["kind"] == "arc":
            chain[-1].append(pt)
        else:
            chain.append([pt])

    lines, arcs, vias = [], [], []
    for here, nxt in zip(chain, chain[1:]):
        p = here[0]
        q = nxt[0]
        if p["layer"] not in COPPER_LAYERS:
            continue
        if len(here) > 1:
            centre = here[1]
            arcs.append((centre["layer"], (p["x"], p["y"]),
                         (centre["x"], centre["y"]), (q["x"], q["y"]),
                         arc_ccw(centre), centre["width"]))
        else:
            lines.append((p["layer"], (p["x"], p["y"]), (q["x"], q["y"]), p["width"]))
    for i, here in enumerate(chain):
        p = here[0]
        if p["kind"] != "via":
            continue
        prev = chain[i - 1][0] if i else None
        frm = prev["layer"] if prev is not None else None
        vias.append((p["x"], p["y"],
                     frm if frm in COPPER_LAYERS else None,
                     p["layer"] if p["layer"] in COPPER_LAYERS else None))
    return lines, arcs, vias


def line_length(line):
    return math.dist(line[1], line[2])


def arc_length(arc):
    _layer, start, centre, end, ccw, _width = arc
    a0, a1 = arc_angles(start, centre, end, ccw)
    return abs(a1 - a0) * math.dist(start, centre)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("asc")
    ap.add_argument("--net", default="", help="dump this net's geometry")
    ap.add_argument("--top", type=int, default=15, help="how many nets to rank")
    args = ap.parse_args()

    lines_in = open(args.asc, encoding="latin-1").read().splitlines()
    conns = list(connections(lines_in))

    per_net = collections.defaultdict(
        lambda: {"line": 0, "arc": 0, "via": 0, "len": 0.0, "conn": 0})
    vias_all = 0
    no_copper = 0
    same_layer_via = 0
    pair_hist = collections.Counter()
    for net, _ra, _pa, _rb, _pb, pts in conns:
        segs, arcs, vias = route_geometry(pts)
        s = per_net[net]
        s["conn"] += 1
        s["line"] += len(segs)
        s["arc"] += len(arcs)
        s["via"] += len(vias)
        s["len"] += sum(line_length(l) for l in segs) + sum(arc_length(a) for a in arcs)
        vias_all += len(vias)
        if not segs and not arcs:
            no_copper += 1
        for _x, _y, frm, to in vias:
            pair_hist[(frm, to)] += 1
            if frm == to:
                same_layer_via += 1

    # PADS repeats a net's connections in every *SIGNAL* block, so the raw totals
    # count the same copper several times; the distinct counts are the board.
    distinct_line = set()
    distinct_arc = set()
    distinct_via = set()
    distinct_len = 0.0
    for net, _ra, _pa, _rb, _pb, pts in conns:
        segs, arcs, vias = route_geometry(pts)
        for seg in segs:
            key = (net,) + seg
            if key not in distinct_line:
                distinct_line.add(key)
                distinct_len += line_length(seg)
        for arc in arcs:
            key = (net,) + arc
            if key not in distinct_arc:
                distinct_arc.add(key)
                distinct_len += arc_length(arc)
        for v in vias:
            distinct_via.add((net, v[0], v[1]))

    total_line = sum(v["line"] for v in per_net.values())
    total_arc = sum(v["arc"] for v in per_net.values())
    total_len = sum(v["len"] for v in per_net.values())
    print(f"nets            {len(per_net)}")
    print(f"connections     {len(conns)}")
    print(f"track lines     {len(distinct_line)} distinct of {total_line}")
    print(f"track arcs      {len(distinct_arc)} distinct of {total_arc}")
    print(f"vias            {len(distinct_via)} distinct of {vias_all}")
    print(f"track length    {distinct_len / UNITS_PER_MIL / 39.3701:.1f} mm distinct, "
          f"{total_len / UNITS_PER_MIL / 39.3701:.1f} mm as listed")
    print(f"connections with no copper at all (pour/pad-to-pad): {no_copper}")
    print(f"vias whose adjacent segments share a layer: {same_layer_via}")
    print("adjacent segment layers at vias (arriving -> leaving):")
    for (a, b), n in sorted(pair_hist.items(), key=lambda kv: -kv[1]):
        print(f"  L{a} -> L{b}: {n}")

    print(f"\ntop {args.top} nets by segment count:")
    for net, v in sorted(per_net.items(), key=lambda kv: -kv[1]["line"])[:args.top]:
        print(f"  {net:<28} conn {v['conn']:>3}  line {v['line']:>4}  arc {v['arc']:>2}"
              f"  via {v['via']:>3}  {v['len'] / UNITS_PER_MIL / 39.3701:8.1f} mm")

    if args.net:
        print(f"\n=== net {args.net} ===")
        for net, ra, pa, rb, pb, pts in conns:
            if net != args.net:
                continue
            print(f"{ra}.{pa} -> {rb}.{pb}")
            for pt in pts:
                print(f"  {pt['x'] / UNITS_PER_MIL:9.2f} {pt['y'] / UNITS_PER_MIL:9.2f} mil"
                      f"  L{pt['layer']:<3} w={pt['width'] / UNITS_PER_MIL:.1f}"
                      f"  {pt['kind']}")
            segs, arcs, vias = route_geometry(pts)
            for layer, a, b, width in segs:
                print(f"  line L{layer} w={width / UNITS_PER_MIL:.1f} "
                      f"{line_length((layer, a, b, width)) / UNITS_PER_MIL:.1f} mil "
                      f"{a} -> {b}")
            for layer, a, centre, b, ccw, width in arcs:
                print(f"  arc  L{layer} w={width / UNITS_PER_MIL:.1f} "
                      f"{arc_length((layer, a, centre, b, ccw, width)) / UNITS_PER_MIL:.1f} mil "
                      f"{a} -> {b} centre {centre} "
                      f"{'CCW' if ccw else 'CW'}")
            for v in vias:
                print(f"  via ({v[0] / UNITS_PER_MIL:.2f},{v[1] / UNITS_PER_MIL:.2f})"
                      f" L{v[2]} -> L{v[3]}")


if __name__ == "__main__":
    main()
