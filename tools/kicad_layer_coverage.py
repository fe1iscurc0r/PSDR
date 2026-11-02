#!/usr/bin/env python3
"""Bidirectional coverage between two Gerber layers, per copper/mask/silk pair.

The reproduction chain already proves pad- and drill-level agreement
(:mod:`kicad_gerber_compare`).  This answers the broader question a fabricator
asks: for a whole layer, how much of the CAM package is explained by our plot and
how much of our plot is explained by theirs.

Method: rasterise each file at a fixed pitch, dilate one side by the tolerance and
count pixels that survive the subtraction.  Two numbers come out of every pair and
both are needed -- a one-sided coverage figure hides invented copper just as well
as missing copper.  Region fills (``G36``/``G37``) are rasterised as polygons;
flashes are drawn at their aperture width.

This is a *measurement*, not a verdict: a low coverage on a copper layer is
expected where the source hatches its pours and our plot fills them, and the
interpretation belongs in the build log next to the number.

Usage:
    python3 tools/kicad_layer_coverage.py <pads-dir> <our-fab-dir> [--pitch 40]
        [--tol-mm 0.1] [--pairs 8]
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gerbparse  # noqa: E402
from PIL import Image, ImageChops, ImageDraw, ImageFilter  # noqa: E402

PAIRS = [
    ("F.Cu", "3 - top-art.GTL", "PSDR_2.6.1_pcb_spike_full-F_Cu.gbr"),
    ("In1.Cu", "4 - L2.p.G1", "PSDR_2.6.1_pcb_spike_full-In1_Cu.gbr"),
    ("In2.Cu", "5 - L3.G2", "PSDR_2.6.1_pcb_spike_full-In2_Cu.gbr"),
    ("B.Cu", "6 - bot-art.GBL", "PSDR_2.6.1_pcb_spike_full-B_Cu.gbr"),
    ("F.Mask", "2 - top-sm.GTS", "PSDR_2.6.1_pcb_spike_full-F_Mask.gbr"),
    ("B.Mask", "7 - bot-sm.GBS", "PSDR_2.6.1_pcb_spike_full-B_Mask.gbr"),
    ("F.Silk", "1 - top-ss.GTO", "PSDR_2.6.1_pcb_spike_full-F_Silkscreen.gbr"),
    ("B.Silk", "8 - bot-ss.GBO", "PSDR_2.6.1_pcb_spike_full-B_Silkscreen.gbr"),
]

BOARD = (0.0, 0.0, 101.6, 66.04)      # mm, with the CAM package's 1000 mil frame


def strokes(path, dx=0.0, dy=0.0):
    """Segments in mm.  gerbparse already applies the file's unit to coordinates,
    so its values are inches -- multiplying by ``g.units`` again shrinks them 25x."""
    g = gerbparse.load(path)
    out = []
    for s in list(g.drawups()) + list(g.flashes()):
        w = (s.w or 0.0) * 25.4                  # mm
        if w <= 0:
            w = 0.004
        out.append((s.x * 25.4 + dx, s.y * 25.4 + dy,
                    (s.x2 if s.x2 is not None else s.x) * 25.4 + dx,
                    (s.y2 if s.y2 is not None else s.y) * 25.4 + dy, w))
    return out


def regions(path, scale=1e-6, offset=0.0):
    """G36/G37 polygon fills, converted to mm with the file's own coordinate scale."""
    raw = open(path, encoding="latin-1").read()
    out = []
    for block in re.findall(r"G36\*(.*?)G37\*", raw, re.S):
        pts = []
        for tok in block.split("*"):
            m = re.match(r"^(?:G0[123])?X(-?\d+)Y(-?\d+)D0[123]$", tok.strip())
            if m:
                pts.append((int(m.group(1)) * scale + offset,
                            int(m.group(2)) * scale + offset))
        if len(pts) >= 3:
            out.append(pts)
    return out


def raster(items, reg, pitch):
    w = int(round((BOARD[2] - BOARD[0]) * pitch)) + 1
    h = int(round((BOARD[3] - BOARD[1]) * pitch)) + 1
    img = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(img)
    for poly in reg:
        dr_polygon(dr, poly, pitch)
    for x1, y1, x2, y2, wmm in items:
        px = max(1, int(round(wmm * pitch)))
        a = ((x1 - BOARD[0]) * pitch, (BOARD[3] - y1) * pitch)
        b = ((x2 - BOARD[0]) * pitch, (BOARD[3] - y2) * pitch)
        dr.line([a, b], fill=255, width=px)
        if a == b:
            dr.ellipse([a[0] - px / 2, a[1] - px / 2, a[0] + px / 2, a[1] + px / 2], fill=255)
    return img


def dr_polygon(dr, poly, pitch):
    dr.polygon([((x - BOARD[0]) * pitch, (BOARD[3] - y) * pitch) for x, y in poly], fill=255)


def coverage(a, b, dil_mm, pitch):
    dil = b.filter(ImageFilter.MaxFilter(int(round(dil_mm * pitch)) * 2 + 1))
    diff = ImageChops.subtract(a, dil)
    total = sum(1 for p in a.getdata() if p)
    left = sum(1 for p in diff.getdata() if p)
    return total, left


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pads_dir")
    ap.add_argument("our_dir")
    ap.add_argument("--pitch", type=float, default=40.0, help="pixels per mm")
    ap.add_argument("--tol-mm", type=float, default=0.10)
    ap.add_argument("--pads-shift-mm", type=float, default=25.4,
                    help="translation the CAM package carries (1000 mil on both axes)")
    ap.add_argument("--region-scale", type=float, default=1e-6,
                    help="coordinate divisor for G36 vertices (PADS: 1e-6 mm per unit)")
    args = ap.parse_args()

    print("layer      CAM  seg/region      ours  seg/region     CAM->ours  ours->CAM"
          "   (tol %.2f mm @ %.0f px/mm)" % (args.tol_mm, args.pitch))
    for name, pad_file, our_file in PAIRS:
        p1 = os.path.join(args.pads_dir, pad_file)
        p2 = os.path.join(args.our_dir, our_file)
        if not (os.path.exists(p1) and os.path.exists(p2)):
            print("%-9s MISSING input (%s / %s)" % (name, os.path.exists(p1), os.path.exists(p2)))
            continue
        # the CAM package carries the +1000 mil translation; our plot does not
        s1 = strokes(p1, -args.pads_shift_mm, -args.pads_shift_mm)
        s2 = strokes(p2)
        r1 = [( (x - args.pads_shift_mm, y - args.pads_shift_mm) for x, y in poly )
              for poly in regions(p1, args.region_scale)]
        r2 = regions(p2, args.region_scale)
        m1, m2 = raster(s1, r1, args.pitch), raster(s2, r2, args.pitch)
        t1, left1 = coverage(m1, m2, args.tol_mm, args.pitch)
        t2, left2 = coverage(m2, m1, args.tol_mm, args.pitch)
        cov1 = 100.0 * (t1 - left1) / t1 if t1 else 0.0
        cov2 = 100.0 * (t2 - left2) / t2 if t2 else 0.0
        print("%-9s %6d /%4d reg    %6d /%4d reg      %7.2f%%  %7.2f%%"
              % (name, len(s1), len(r1), len(s2), len(r2), cov1, cov2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
