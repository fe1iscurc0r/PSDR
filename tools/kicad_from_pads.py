#!/usr/bin/env python3
"""Build a KiCad 10 board from the PADS Layout 9.5 export of PSDR 2.6.1.

Why this script exists
----------------------
The Eagle files in Hardware/ are pre-XML binary (.sch/.pcb, no .brd in any
branch), so `kicad-cli pcb import --format eagle` fails with an XML parse error,
and `--format pads` expects the *PADS-POWERPCB* dialect -- it reads psdr26.emn
into a silently empty board.  The only machine-readable description of the real
2.6.1 layout is the PADS ASCII export, so the board is rebuilt from that, with
the normalised Gerbers used to measure copper dimensions.

Where every number comes from
----------------------------
Edge.Cuts   .emn BOARD_OUTLINE: 68 vertices, 25 arcs.  The arc rule was measured
            against the Gerber contour, not assumed -- the angle rides on the
            segment's *ending* vertex, positive = counter-clockwise in PADS' own
            vertex order, magnitude = included angle (may exceed 180; one is
            183.2).  Reconstructing centre and radius analytically from .emn
            alone reproduces the Gerber arcs to 0.07 mil.
footprints  .emn PLACEMENT (position, rotation, side) + .emp ELECTRICAL body
            polygon.  .emp has no pad stacks, so only body and courtyard exist.
pads        .emn DRILLED_HOLES whose name equals a component refdes -- all 47
            PIN holes do.  Drill from .emn, copper ring from the nearest
            F_Cu/B_Cu Gerber flash.
vias        the 419 holes named BOARD.
absent      copper tracks and nets.  No source in this repository carries a
            netlist: .emn has no .NETS section, .emp has no pin data, the Eagle
            binaries are unreadable.  Nothing here is invented.

Coordinate mapping
------------------
PADS THOU -> mm by *0.0254.  KiCad file coordinates have Y pointing down, so
board_y_kicad = height - board_y_pads.  KiCad's footprint forward transform was
probed by plotting a test board and reading the pad flashes back out of the
exported Gerber:

    abs = origin + K(rot) * local,   K(t) = [[cos t,  sin t],
                                             [-sin t, cos t]]

which makes the correct KiCad angle equal to the PADS angle unchanged and the
correct local geometry the PADS local geometry with Y negated.  Gerber features
sit at PADS coordinates plus a 1.0 inch plot-frame origin (verified on 466
holes: mean offset 0.00001 in against PSDR25 Main Board).
"""

import argparse
import math
import os
import sys
import uuid as _uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pads_parse import parse_emn, parse_emp       # noqa: E402
import gerbparse                                  # noqa: E402

MIL2MM = 25.4 / 1000.0
GERBER_ORIGIN_IN = 1.0
DEFAULT_VIA_RING_MIL = 32.0        # the measured ring on the 14 mil vias
MIN_ANNULAR_MM = 0.15


def K(deg):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return ((c, s), (-s, c))


def mv(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1], m[1][0] * v[0] + m[1][1] * v[1])


def uid():
    return str(_uuid.uuid4())


def num(v):
    s = "%.6f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


class Copper:
    """Nearest-flash lookup so pad and via rings are measured, not guessed."""

    def __init__(self, gerber_dir):
        self.flash = []
        self.warnings = []
        if not gerber_dir or not os.path.isdir(gerber_dir):
            self.warnings.append("no gerber package: rings fall back to defaults")
            return
        for name in ("F_Cu", "B_Cu"):
            path = os.path.join(gerber_dir, name + ".gbr")
            if not os.path.exists(path):
                self.warnings.append("%s.gbr missing" % name)
                continue
            for s in gerbparse.load(path).flashes():
                if s.dia:
                    self.flash.append((s.x, s.y, s.dia))

    def ring_mil(self, x_mil, y_mil, tol_mil=2.0):
        if not self.flash:
            return None
        gx = x_mil * MIL2MM / 25.4 + GERBER_ORIGIN_IN
        gy = y_mil * MIL2MM / 25.4 + GERBER_ORIGIN_IN
        best = None
        for (fx, fy, dia) in self.flash:
            d = math.hypot(fx - gx, fy - gy) * 1000.0
            if d <= tol_mil and (best is None or d < best[0]):
                best = (d, dia)
        return best[1] * 1000.0 if best else None


def outline_segments(outline, x0, y0, height_mm):
    """('line'|'arc', p0_mm, p1_mm, mid_mm) in KiCad file coordinates.

    The arc is worked out in the PADS frame, where the centre rule below was
    validated against the Gerber contour, and only the finished points are
    mapped into KiCad's Y-down frame.
    """
    pts = [((v[1] - x0) * MIL2MM, (v[2] - y0) * MIL2MM) for v in outline]
    angles = [v[3] for v in outline]

    def to_kicad(p):
        return (p[0], height_mm - p[1])

    segs = []
    for i in range(1, len(pts)):
        p0, p1, a = pts[i - 1], pts[i], angles[i]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        chord = math.hypot(dx, dy)
        if chord < 1e-12:
            continue
        if not a:
            segs.append(("line", to_kicad(p0), to_kicad(p1), None))
            continue
        # centre = chord midpoint + sign(a) * left normal * r*cos(a/2).
        # For |a| > 180 the cosine is negative, which puts the centre on the
        # other side automatically -- that is what makes the 183.2 degree
        # segment come out as the reflex arc it is.
        th = math.radians(a)
        r = chord / (2 * math.sin(abs(th) / 2))
        h = r * math.cos(th / 2)
        sgn = 1.0 if a > 0 else -1.0
        cx = (p0[0] + p1[0]) / 2 + sgn * (-dy / chord) * h
        cy = (p0[1] + p1[1]) / 2 + sgn * (dx / chord) * h
        half = th / 2
        mid = (cx + (p0[0] - cx) * math.cos(half) - (p0[1] - cy) * math.sin(half),
               cy + (p0[0] - cx) * math.sin(half) + (p0[1] - cy) * math.cos(half))
        segs.append(("arc", to_kicad(p0), to_kicad(p1), to_kicad(mid)))
    return segs


def body_polygon(info, mirror_y):
    """.emp body outline -> footprint-local mm.  Y is the axis that flips."""
    if not info or len(info["polygon"]) < 2:
        return []
    pts = []
    for (ux, uy) in info["polygon"]:
        y = uy * MIL2MM
        pts.append((ux * MIL2MM, -y if mirror_y else y))
    return pts


def footprint_text(kind, text, at, layer, size=1.0, thick=0.15, hide=False):
    return ('\t\t(property "%s" "%s" (at %s %s %s) (layer "%s")%s (uuid "%s")'
            ' (effects (font (size %.2f %.2f) (thickness %.2f))))' % (
                kind, text, num(at[0]), num(at[1]), num(at[2] if len(at) > 2 else 0),
                layer, " (hide yes)" if hide else "", uid(), size, size, thick))


def emit_footprint(comp, poly, pads, layer):
    fab = "F.Fab" if layer == "F.Cu" else "B.Fab"
    crt = "F.CrtYd" if layer == "F.Cu" else "B.CrtYd"
    o = ['\t(footprint "PSDR_PADS:%s"' % comp["decal"],
         '\t\t(layer "%s")' % layer,
         '\t\t(uuid "%s")' % uid(),
         '\t\t(at %s %s %s)' % (num(comp["kx"]), num(comp["ky"]), num(comp["rot"])),
         '\t\t(descr "PADS 9.5 decal %s, state %s, side %s")' % (
             comp["part_type"], comp["state"], comp["side"]),
         '\t\t(tags "%s")' % comp["decal"],
         footprint_text("Reference", comp["refdes"], (0, 0, 0), fab, hide=True),
         footprint_text("Value", comp["part_type"], (0, 0, 0), fab, hide=True)]
    if comp["state"] == "MCAD":
        o.append('\t\t(attr board_only exclude_from_bom)')
    else:
        o.append('\t\t(attr %s)' % ("through_hole" if pads else "smd"))
    o.append('\t\t(duplicate_pad_numbers_are_jumpers no)')

    if len(poly) >= 3:
        pts = " ".join('(xy %s %s)' % (num(x), num(y)) for (x, y) in poly)
        o.append('\t\t(fp_poly (pts %s) (stroke (width 0.05) (type default))'
                 ' (layer "%s") (uuid "%s"))' % (pts, fab, uid()))
    xs = [p[0] for p in poly] or [0.0]
    ys = [p[1] for p in poly] or [0.0]
    cx0, cx1 = min(xs) - 0.25, max(xs) + 0.25
    cy0, cy1 = min(ys) - 0.25, max(ys) + 0.25
    for (a, b) in (((cx0, cy0), (cx1, cy0)), ((cx1, cy0), (cx1, cy1)),
                   ((cx1, cy1), (cx0, cy1)), ((cx0, cy1), (cx0, cy0))):
        o.append('\t\t(fp_line (start %s %s) (end %s %s)'
                 ' (stroke (width 0.05) (type default)) (layer "%s") (uuid "%s"))' % (
                     num(a[0]), num(a[1]), num(b[0]), num(b[1]), crt, uid()))

    for p in pads:
        kind = "np_thru_hole" if p["plating"] == "NPTH" else "thru_hole"
        o.append('\t\t(pad "%s" %s circle' % (p["pad_no"], kind))
        o.append('\t\t\t(at %s %s)' % (num(p["lx"]), num(p["ly"])))
        o.append('\t\t\t(size %s %s)' % (num(p["size"]), num(p["size"])))
        o.append('\t\t\t(drill %s)' % num(p["drill"]))
        o.append('\t\t\t(layers "*.Cu" "*.Mask")')
        o.append('\t\t\t(remove_unused_layers no)')
        o.append('\t\t\t(net 0 "")')
        o.append('\t\t\t(pinfunction "%s")' % p["name"])
        o.append('\t\t\t(pintype "unconnected")')
        o.append('\t\t\t(uuid "%s")' % uid())
        o.append('\t\t)')
    o.append('\t)')
    return "\n".join(o)


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--emn", default=os.path.join(here, "Hardware", "BOMs", "PSDR_2.6.1", "psdr26.emn"))
    ap.add_argument("--emp", default=os.path.join(here, "Hardware", "BOMs", "PSDR_2.6.1", "psdr26.emp"))
    ap.add_argument("--gerber", default=os.path.join(here, "dist", "gerber", "PSDR25_Main_Board"))
    ap.add_argument("--out", default=os.path.join(here, "dist", "kicad", "PSDR_2.6.1.kicad_pcb"))
    ap.add_argument("--template", default=os.path.join(here, "tools", "kicad_board_header.kicad_pcb"),
                    help="a KiCad-generated .kicad_pcb whose header is reused verbatim")
    args = ap.parse_args()

    board = parse_emn(args.emn)
    decals = parse_emp(args.emp)
    copper = Copper(args.gerber)

    xs = [v[1] for v in board["outline"]]
    ys = [v[2] for v in board["outline"]]
    x0, y0 = min(xs), min(ys)
    width_mm = (max(xs) - x0) * MIL2MM
    height_mm = (max(ys) - y0) * MIL2MM

    def kicad_of(mil_x, mil_y):
        return ((mil_x - x0) * MIL2MM, height_mm - (mil_y - y0) * MIL2MM)

    holes = []
    for h in board["holes"]:
        kx, ky = kicad_of(h["x"], h["y"])
        ring = copper.ring_mil(h["x"], h["y"])
        holes.append(dict(h, kx=kx, ky=ky, ring_mm=ring * MIL2MM if ring else None))

    comps = []
    for c in board["components"]:
        kx, ky = kicad_of(c["x"], c["y"])
        comps.append(dict(c, kx=kx, ky=ky))
    by_ref = {}
    for c in comps:
        by_ref.setdefault(c["refdes"], c)

    via_holes = [h for h in holes if h["kind"] == "VIA"]
    pin_holes = [h for h in holes if h["kind"] == "PIN"]

    fp_pads = {}
    unmatched = []
    for h in pin_holes:
        c = by_ref.get(h["name"])
        if c is None:
            unmatched.append(h["name"])
            continue
        drill = h["drill"] * MIL2MM
        if h["plating"] == "NPTH":
            size = drill                      # unplated: no annular ring exists
        else:
            size = h["ring_mm"] or (drill + 2 * MIN_ANNULAR_MM)
        local = mv(K(-c["rot"]), (h["kx"] - c["kx"], h["ky"] - c["ky"]))
        n = len(fp_pads.get(c["refdes"], [])) + 1
        fp_pads.setdefault(c["refdes"], []).append(dict(
            pad_no=str(n), name=h["name"], lx=local[0], ly=local[1],
            drill=drill, size=size, plating=h["plating"]))

    if not os.path.exists(args.template):
        raise SystemExit("--template %s not found: the header must come from KiCad itself"
                         % args.template)
    header = open(args.template, encoding="utf-8").read().replace(
        "\t(embedded_fonts no)\n)\n", "")

    out = [header.rstrip("\n"), '\t(net 0 "")']

    for (kind, p0, p1, mid) in outline_segments(board["outline"], x0, y0, height_mm):
        if kind == "line":
            out.append('\t(gr_line\n\t\t(start %s %s)\n\t\t(end %s %s)\n'
                       '\t\t(stroke (width 0.1) (type solid))\n\t\t(layer "Edge.Cuts")\n'
                       '\t\t(uuid "%s")\n\t)' % (num(p0[0]), num(p0[1]), num(p1[0]),
                                                  num(p1[1]), uid()))
        else:
            out.append('\t(gr_arc\n\t\t(start %s %s)\n\t\t(mid %s %s)\n\t\t(end %s %s)\n'
                       '\t\t(stroke (width 0.1) (type solid))\n\t\t(layer "Edge.Cuts")\n'
                       '\t\t(uuid "%s")\n\t)' % (num(p0[0]), num(p0[1]), num(mid[0]),
                                                  num(mid[1]), num(p1[0]), num(p1[1]), uid()))

    for h in via_holes:
        size = h["ring_mm"] or DEFAULT_VIA_RING_MIL * MIL2MM
        out.append('\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n'
                   '\t\t(layers "F.Cu" "B.Cu")\n\t\t(tenting (front none) (back none))\n'
                   '\t\t(capping none)\n\t\t(covering (front none) (back none))\n'
                   '\t\t(plugging (front none) (back none))\n\t\t(filling none)\n'
                   '\t\t(net 0)\n\t\t(uuid "%s")\n)' % (
                       num(h["kx"]), num(h["ky"]), num(size), num(h["drill"] * MIL2MM), uid()))

    no_body = 0
    for c in sorted(comps, key=lambda z: z["refdes"]):
        layer = "F.Cu" if c["side"] == "TOP" else "B.Cu"
        info = decals.get(c["decal"])
        poly = body_polygon(info, c["side"] == "BOTTOM")
        if not poly:
            no_body += 1
        out.append(emit_footprint(c, poly, fp_pads.get(c["refdes"], []), layer))

    out.append('\t(embedded_fonts no)')
    out.append(')')

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")

    print("wrote %s  (%d bytes)" % (args.out, os.path.getsize(args.out)))
    print("  board        : %.4f x %.4f mm" % (width_mm, height_mm))
    seg = outline_segments(board["outline"], x0, y0, height_mm)
    print("  Edge.Cuts    : %d segments, of which %d arcs" % (len(seg), sum(1 for s in seg if s[0] == "arc")))
    print("  footprints   : %d (%d TOP / %d BOTTOM), %d with no .emp body polygon" % (
        len(comps), sum(1 for c in comps if c["side"] == "TOP"),
        sum(1 for c in comps if c["side"] == "BOTTOM"), no_body))
    print("  vias         : %d" % len(via_holes))
    print("  PIN holes    : %d attached to %d components, %d unmatched (%s)" % (
        len(pin_holes), len(fp_pads), len(unmatched), ",".join(sorted(set(unmatched))) or "-"))
    print("  copper rings : %d/%d holes matched a F_Cu/B_Cu flash within 2 mil" % (
        sum(1 for h in holes if h["ring_mm"]), len(holes)))
    if copper.warnings:
        print("  notes        :", "; ".join(copper.warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
