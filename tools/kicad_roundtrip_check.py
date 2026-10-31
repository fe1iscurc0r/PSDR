#!/usr/bin/env python3
"""Close the loop on dist/kicad/PSDR_2.6.1.kicad_pcb.

The generator claims the outline and the hole pattern survived the PADS ->
KiCad -> Gerber round trip.  This proves it by re-reading what KiCad itself
plots and comparing against the normalised PADS Gerbers and the .emn table, so
the acceptance evidence is a measurement rather than a restatement of the input.

Run kicad-cli first:
    kicad-cli pcb export gerbers --layers Edge.Cuts -o <dir> <board>
    kicad-cli pcb export drill --format excellon --drill-origin absolute -u mm -o <dir> <board>
"""

import argparse
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pads_parse import parse_emn                 # noqa: E402
import gerbparse                                 # noqa: E402

MIL2MM = 25.4 / 1000.0


def dseg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def kicad_gerber_segs(path, height_mm):
    """KiCad plots mm with Y negated; undo that into the file frame."""
    g = gerbparse.load(path)
    dia = max([a.params[0] or 0.0 for a in g.apertures.values()] or [0.0])
    segs = [(s.x * 25.4, -s.y * 25.4, s.x2 * 25.4, -s.y2 * 25.4) for s in g.strokes]
    return g, segs, dia


def pads_gerber_segs(path, x0_mm, y0_mm, height_mm):
    """PADS plots inches with a +1.0" frame origin and Y up."""
    g = gerbparse.load(path)
    dia = max([a.params[0] or 0.0 for a in g.apertures.values()] or [0.0])
    segs = [((s.x - 1.0) * 25.4 - x0_mm, height_mm - ((s.y - 1.0) * 25.4 - y0_mm),
             (s.x2 - 1.0) * 25.4 - x0_mm, height_mm - ((s.y2 - 1.0) * 25.4 - y0_mm))
            for s in g.strokes]
    return g, segs, dia


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--emn", default=os.path.join(here, "Hardware", "BOMs", "PSDR_2.6.1", "psdr26.emn"))
    ap.add_argument("--edge-original", default=os.path.join(here, "dist", "gerber", "PSDR25_Main_Board", "Edge_Cuts.gbr"))
    ap.add_argument("--edge-export", required=True, help="Edge.Cuts gerber plotted by kicad-cli")
    ap.add_argument("--drill-export", required=True, help="Excellon drill plotted by kicad-cli")
    ap.add_argument("--tol-mm", type=float, default=0.01)
    args = ap.parse_args()

    board = parse_emn(args.emn)
    xs = [v[1] for v in board["outline"]]
    ys = [v[2] for v in board["outline"]]
    x0, y0 = min(xs) * MIL2MM, min(ys) * MIL2MM
    width = (max(xs) - min(xs)) * MIL2MM
    height = (max(ys) - min(ys)) * MIL2MM

    print("board from .emn      : %.4f x %.4f mm" % (width, height))

    go, so, dia_o = pads_gerber_segs(args.edge_original, x0, y0, height)
    gk, sk, dia_k = kicad_gerber_segs(args.edge_export, height)
    print("Edge.Cuts segments   : original %d (%d arcs), KiCad re-export %d (%d arcs)" % (
        len(so), len(go.arcs), len(sk), len(gk.arcs)))

    def span(segs):
        xs = [p for s in segs for p in (s[0], s[2])]
        ys = [p for s in segs for p in (s[1], s[3])]
        return max(xs) - min(xs), max(ys) - min(ys)
    (w1, h1), (w2, h2) = span(so), span(sk)
    print("outline extent       : original %.4f x %.4f mm, KiCad %.4f x %.4f mm" % (w1, h1, w2, h2))

    def to_contour(pt, segs):
        return min(dseg(pt[0], pt[1], *s) for s in segs)
    pk = [(s[0], s[1]) for s in sk] + [(s[2], s[3]) for s in sk]
    po = [(s[0], s[1]) for s in so] + [(s[2], s[3]) for s in so]
    d1 = [to_contour(p, so) for p in pk]
    d2 = [to_contour(p, sk) for p in po]
    print("contour deviation    : KiCad->original max %.5f mm, original->KiCad max %.5f mm" % (
        max(d1), max(d2)))

    txt = open(args.drill_export, encoding="latin-1").read()
    tools = {}
    for m in re.finditer(r"^; #@! TA\.AperFunction,(\w+),[^\n]*\nT(\d+)C([\d.]+)", txt, re.M):
        tools["T" + m.group(2)] = (m.group(1) == "Plated", float(m.group(3)))
    cur = None
    hits = []
    for line in txt.splitlines():
        s = line.strip()
        if re.fullmatch(r"T\d+", s):
            cur = s
            continue
        m = re.fullmatch(r"X(-?[\d.]+)Y(-?[\d.]+)", s)
        if m and cur:
            hits.append((float(m.group(1)), float(m.group(2)), cur))
    print("drill hits exported  : %d (from .emn: %d)" % (len(hits), len(board["holes"])))

    worst = 0.0
    missed = []
    plating_bad = []
    for h in board["holes"]:
        ex, ey = h["x"] * MIL2MM - x0, height - (h["y"] * MIL2MM - y0)
        ey = -ey                                   # KiCad negates Y when plotting
        d, best = min((math.hypot(ex - a, ey - c), t) for (a, c, t) in hits)
        if d > args.tol_mm:
            missed.append((h["name"], h["kind"], round(d, 4)))
        worst = max(worst, d)
        if tools.get(best) and tools[best][0] != (h["plating"] == "PTH"):
            plating_bad.append((h["name"], h["plating"], best))
    print("worst hole offset    : %.5f mm (tolerance %.3f mm)" % (worst, args.tol_mm))
    if missed:
        print("HOLES NOT REPRODUCED : %s" % missed[:10])
    if plating_bad:
        print("PLATING MISMATCH   : %s" % plating_bad[:10])
    plated = sum(1 for t in hits if tools.get(t[2], (None,))[0])
    print("plated / unplated    : %d / %d  (.emn says %d PTH / %d NPTH)" % (
        plated, len(hits) - plated,
        sum(1 for h in board["holes"] if h["plating"] == "PTH"),
        sum(1 for h in board["holes"] if h["plating"] == "NPTH")))

    ok = (not missed and not plating_bad and len(hits) == len(board["holes"])
          and len(go.arcs) == len(gk.arcs) and max(d1) < args.tol_mm and max(d2) < args.tol_mm)
    print("RESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
