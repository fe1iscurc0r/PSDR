#!/usr/bin/env python3
"""Emit a KiCad board from the PADS ASCII: real decal pads plus routed copper.

The board is emitted whole: every part, every routed segment and via, the four
planes' pours, the board profile from the ``BOARD`` record, and the silkscreen
(decals, board-level *LINES*, free *TEXT* and the Ref.Des. labels).  The
reconciliation against the 2.6.1 Gerbers is in
:mod:`kicad_gerber_compare`; the evidence for each decoding choice is in
``docs/WO-psdr-takeover.md``.

Three facts this leans on, each checked against
``Hardware/Gerbers/PSDR25 Main Board`` (same board revision: after translating by
+999.71 mil the seven mounting holes and six fiducials land within 0.3 mil of the
gerber drill/copper positions, and the drill extent is 97.8 x 63.0 mm against an
outline of 100.0 x 65.0 mm):

* 38100 ASCII units = 1 mil.
* A copper pad (stack level -2) of shape RF/OF is a rectangle SIZE wide by
  FINLENGTH long, rotated FINORI degrees from decal local +X, **centred on the
  terminal**.  Measured on C139: both mask openings are 35 x 30 mil and their
  centres sit at the two terminal x positions to the last digit.
* PADS Y grows up, KiCad Y grows down, so every y is negated on output.  Pad
  angles travel the other way (see ``pad_angle``): only the three parts placed
  at 45-degree multiples can tell the two signs apart.
* A route record's width and layer belong to the piece leaving that point, and
  a ``CW``/``CCW`` record is an arc centre, not a vertex -- see
  :mod:`pads_asc_route` for the Gerber evidence.

The board outline is **not** a rectangle: the one ``BOARD`` record in *LINES* is
a 68-vertex CLOSED polygon (42 straight edges and 25 fillet arcs) covering
3937.0 x 2559.1 mil = 100.0 x 65.0 mm, with three connector notches on the left
edge and a clipped corner at the lower right.  Levels 15-18 of *LINES* are
annotation graphics, not the profile: their absolute extent is 5773 x 1379 mil,
far larger than the board.  A vertex line carrying eight numbers starts an arc that
ends at the next vertex: after x/y come the begin angle and signed sweep in
0.1 degrees, then two points symmetric about the centre.  Their midpoint is the
arc centre; the sweep fixes the mid point used by KiCad's three-point arc.

Silkscreen decoding, checked stroke by stroke against ``1 - top-ss.GTO`` and
``8 - bot-ss.GBO``:

* The CAM job is embedded in the ASCII: ``Top Silkscreen`` is
  ``DOC_LAYER_NUMBERS 1 26`` and ``Bottom Silkscreen`` is ``4 29``, each with
  the copper layer of its side plus the silkscreen layer.  A full level x side
  x Gerber census agrees: a decal piece on level 26 is drawn on **the part's
  side** (top part -> GTO, bottom part -> GBO); levels 0 and 1 are drawn on GTO
  for top parts only and nowhere for bottom parts; levels 20/23/27/29 are drawn
  nowhere.  Layer 29 is not the far-side outline: the level-29 pieces that
  looked like matches duplicate level-26 circles, and J170's level-29 CLOSED
  rectangle is absent from both silks from every tested transform variant.
* Zero-length decal segments are not plotted by PADS and are skipped here too.
* A board-level *LINES* piece is not part-relative: layer 26 = F.SilkS,
  29 = B.SilkS.  The two 736-piece hatched "psdr" logos are 2-mil strokes and
  appear as exactly 736 draws of the 0.002 in aperture on each Gerber silk.
* Ref.Des. labels go on the part's side with the label's **absolute** ORI
  (R113 part 270/label 90 plots vertical text in GTO).  Part Type is never
  plotted; on R113 its anchor has no stroke where the Ref.Des. anchor has the
  glyphs.
"""

import argparse
import itertools
import math
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pads_asc_decal import (  # noqa: E402
    UNITS_PER_MIL, index, parse_decals, parse_parttypes, parse_parts, transform,
)
from pads_asc_route import arc_mid, connections, route_geometry  # noqa: E402

MIL = 0.0254
LAYER = {1: "F.Cu", 2: "In1.Cu", 3: "In2.Cu", 4: "B.Cu"}


def quoted(text):
    """Make a PADS name safe inside a KiCad s-expression string.

    Two part types are literally named ``0.1"_1PIN`` and
    ``0.1"_6P_HEADER_DUAL_ENTRY_1241152-6``; the quote closed the string early
    and pcbnew refused the whole board ("应为 … 实际 ''symbol''").
    """
    return text.replace('"', "in")


def arc_midpoint(vertex):
    """Mid point of the arc whose vertex line carries six extra numbers.

    The trailing four numbers are two points symmetric about the centre (the
    midpoint of the two agrees with the centre implied by the begin angle and
    sweep to well under a mil).  ``begin`` and ``sweep`` are in 0.1 degrees.
    """
    x, y, begin, sweep, px, py, qx, qy = vertex
    cx, cy = (px + qx) / 2.0, (py + qy) / 2.0
    r = math.hypot(x - cx, y - cy)
    ang = math.radians((begin + sweep / 2.0) / 10.0)
    return (cx + r * math.cos(ang), cy + r * math.sin(ang))


def parse_outline(lines):
    """Return the board profile as ordered ('line'|'arc', ...) segments.

    Only the ``BOARD`` record in *LINES* is the profile.  Its vertices are
    relative to the record's XLOC/YLOC and the ring repeats its first point at
    the end.  The extra arc numbers are in that same relative frame.
    """
    start = next(i for i, l in enumerate(lines) if l.startswith("*LINES*"))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith("*VIA*"))
    for i in range(start, end):
        tok = lines[i].split()
        if len(tok) >= 6 and tok[1] == "BOARD":
            xloc, yloc = int(tok[2]), int(tok[3])
            break
    else:
        raise SystemExit("no BOARD record in *LINES*")
    for j in range(i + 1, end):
        tok = lines[j].split()
        if tok and tok[0] == "CLOSED":
            count = int(tok[1])
            vertices = []
            for k in range(j + 1, j + 1 + count):
                vals = [int(v) for v in lines[k].split()]
                vals[0] += xloc
                vals[1] += yloc
                if len(vals) == 8:
                    for n in (4, 5, 6, 7):
                        vals[n] += xloc if n % 2 == 0 else yloc
                vertices.append(vals)
            break
    else:
        raise SystemExit("BOARD record has no CLOSED piece")
    if vertices[0][:2] != vertices[-1][:2]:
        raise SystemExit("BOARD outline is not closed")
    ring = vertices[:-1]
    segs = []
    for idx, v in enumerate(ring):
        a = (v[0], v[1])
        nxt = ring[(idx + 1) % len(ring)]
        b = (nxt[0], nxt[1])
        if len(v) == 8:
            if len(nxt) == 8:
                raise SystemExit(f"consecutive outline arcs at {a}")
            segs.append(("arc", a, b, arc_midpoint(v)))
        else:
            segs.append(("line", a, b))
    return segs



def parse_stack(raw_lines):
    """Parse the level lines of one PAD block.

    The tail after the shape differs by family, per the file's own *REMARK*:

        LEVEL SIZE SHAPE IDIA [CORNERRADIUS] [DRILL [PLATED]]        (R, S, C)
        LEVEL SIZE SHAPE FINORI FINLENGTH FINOFFSET [CR] [DR [PL]]   (RF, OF)

    So for R/S/C the first number is the inner diameter, not a corner radius.
    Read only the contiguous run of numbers: a few pads append a second finger
    group after the plated flag (``... 1350000 P 0.000 9000000 0``), and those
    trailing groups must not be mistaken for a drill.

    Level -2 is the side the part sits on and level 0 the far side; the two
    SMA_BOARD_EDGE ground legs (pins 4/5) carry copper *only* on level 0, so
    when -2 is empty the level 0 line is used instead and the pad is flagged
    ``far``.  Level -1 is the inner-layer copper: on MH3M_PLATED it is
    157.48 mil against a 224.41 mil outer pad, which is enough of a difference
    to change the inner-layer DRC.
    """
    lines = {}
    for text in raw_lines:
        tok = text.split()
        if len(tok) >= 3 and tok[0] in ("-2", "-1", "0"):
            lines.setdefault(tok[0], text)

    source = None
    for level in ("-2", "0"):
        text = lines.get(level)
        if text is None:
            continue
        tok = text.split()
        if int(tok[1]) > 0:
            source = (level, tok)
            break
    if source is None:
        # No copper on either outer side: a bare drilled hole (the button's
        # 33.46 mil leg).  Keep the -2 line so the hole still comes out.
        text = lines.get("-2")
        if text is None:
            return None
        source = ("-2", text.split())
    level, tok = source
    text = lines[level]
    size = int(tok[1]) / UNITS_PER_MIL
    shape = tok[2]
    pad = {"size": size, "shape": shape, "finori": 0.0,
           "finlength": size, "finoffset": 0.0, "corner": 0.0, "drill": 0.0,
           "far": level == "0", "inner_size": None, "far_size": None}
    if shape in ("RF", "OF"):
        if len(tok) < 6:
            raise SystemExit(f"finger pad without geometry: {text!r}")
        pad["finori"] = float(tok[3])
        pad["finlength"] = int(tok[4]) / UNITS_PER_MIL
        pad["finoffset"] = int(tok[5]) / UNITS_PER_MIL
        rest = tok[6:]
    else:
        rest = tok[3:]
    nums = []
    for t in rest:
        try:
            nums.append(int(t))
        except ValueError:
            break
    pad["extra_groups"] = len(rest) > len(nums) and any(
        c.isdigit() for t in rest[len(nums):] for c in t
    )
    if shape in ("RF", "OF"):
        pad["corner"] = nums[0] / UNITS_PER_MIL if nums else 0.0
        pad["drill"] = nums[1] / UNITS_PER_MIL if len(nums) > 1 else 0.0
    elif shape == "S":
        # Square pads lead with the corner radius: the "IDIA" slot is only
        # meaningful for a round hole, and reading it as a drill produces
        # 5-8 mil holes that no tool in the drill file has.
        pad["corner"] = nums[0] / UNITS_PER_MIL if nums else 0.0
        pad["drill"] = nums[1] / UNITS_PER_MIL if len(nums) > 1 else 0.0
    else:
        # R pools the hole in the IDIA slot: "0 R 1800000 N" is a bare
        # 47.24 mil non-plated hole (a mounting hole, no copper).
        pad["drill"] = nums[0] / UNITS_PER_MIL if nums else 0.0
        pad["corner"] = nums[1] / UNITS_PER_MIL if len(nums) > 1 else 0.0
    # Only a literal N marks a non-plated hole; an absent flag means plated.
    pad["plated"] = rest[len(nums):len(nums) + 1] != ["N"]
    inner = lines.get("-1")
    if inner:
        inner_size = int(inner.split()[1]) / UNITS_PER_MIL
        if inner_size > 0:
            pad["inner_size"] = inner_size
    if not pad["far"]:
        # A pad may carry copper on the far side as well as the inner layers:
        # the Morse paddle contacts are 76 x 275.6 mil on levels -2, -1 and 0.
        far = lines.get("0")
        if far:
            far_size = int(far.split()[1]) / UNITS_PER_MIL
            if far_size > 0:
                pad["far_size"] = far_size
    return pad


_uid_counter = itertools.count()


def uid():
    """Deterministic, so regenerating the board gives a diff-free file.

    uuid4 changed every UUID on every run; uuid5 over the emission order makes
    the whole board byte-identical for identical input, which is what makes the
    gerber/drill reconciliation in the workorder reproducible.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"psdr261/pcb/{next(_uid_counter)}"))


def kicad_point(part, local_x, local_y):
    """Decal-local ASCII coordinate -> board KiCad coordinate in mm."""
    x, y = transform(part, local_x, local_y, "x", 1, "rotate-then-mirror")
    return x / UNITS_PER_MIL * MIL, -y / UNITS_PER_MIL * MIL


def pad_angle(part, finori):
    """Board angle of the pad's long (FINLENGTH) side.

    A pad is a line, not an arrow, so at 0/90/180/270 either sign works and the
    first version of this function used the opposite one.  Only CW1/CW2 (315 and
    135 degrees) and C13 (135) expose the handedness: with the wrong sign the
    two 275-mil Morse paddle pads lie along their own long axis 2.15 mm apart and
    short.  The 2.6.1 Gerber at 468dc41 strokes them at -45 degrees, which is
    what this sign produces.
    """
    a = part["ori"] + finori
    return -a if part["mirror"] == "M" else a


def footprint(ref, part, decal, decal_name, pin_net, silk=False):
    fp_x, fp_y = kicad_point(part, 0, 0)
    side = "B.Cu" if part["mirror"] == "M" else "F.Cu"
    mask = "B.Mask" if part["mirror"] == "M" else "F.Mask"
    paste = "B.Paste" if part["mirror"] == "M" else "F.Paste"
    fptype = quoted(part["type"])
    out = [
        f'\t(footprint "PSDR:{fptype}"',
        f'\t\t(layer "{side}")',
        f'\t\t(uuid "{uid()}")',
        f'\t\t(at {fp_x:.4f} {fp_y:.4f} 0)',
        f'\t\t(descr "PADS decal {quoted(decal_name)}, {fptype}")',
        f'\t\t(property "Reference" "{quoted(ref)}" (at 0 0 0) (layer "F.Fab") (hide yes) '
        f'(uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))',
        f'\t\t(property "Value" "{fptype}" (at 0 0 0) (layer "F.Fab") (hide yes) '
        f'(uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))',
        '\t\t(attr smd)',
        '\t\t(duplicate_pad_numbers_are_jumpers no)',
    ]
    for pin, tx, ty in decal["terminals"]:
        stack = decal["pads"].get(pin) or decal["pads"].get("0")
        if not stack:
            raise SystemExit(f"{ref}: no pad stack for pin {pin}")
        p = parse_stack(stack)
        if p is None:
            raise SystemExit(f"{ref}: pin {pin} has no copper level")
        px, py = kicad_point(part, tx, ty)
        ang = pad_angle(part, p["finori"])
        w, h = p["finlength"], p["size"]
        if p["finoffset"]:
            raise SystemExit(f"{ref}: pin {pin} has FINOFFSET={p['finoffset']}, "
                             "the centred-pad model does not cover it")
        # PADS "R" is a round pad: 8550000 units on M3 is a 224.41 mil
        # *circle* in top.GTL (%ADD151C,0.22441*%), not a square of that
        # width -- the square's corner reached 4.03 mm from centre and
        # swallowed the NRST/+5V tracks that clear the 2.85 mm circle.
        if p["shape"] == "R":
            shape = "circle"
        else:
            shape = "roundrect" if p["corner"] > 0 else "rect"
        net = ""
        if pin in pin_net:
            net_id, net_name = pin_net[pin]
            net = f'\n\t\t\t(net {net_id} "{quoted(net_name)}")'
        pad_side, pad_mask, pad_paste = side, mask, paste
        if p["far"]:
            pad_side = "F.Cu" if side == "B.Cu" else "B.Cu"
            pad_mask = "F.Mask" if side == "B.Cu" else "B.Mask"
            pad_paste = "F.Paste" if side == "B.Cu" else "B.Paste"
        drill = p["drill"] * MIL
        if drill > 0:
            # A drilled pad.  Size 0 is a hole with no annular ring (the
            # mounting holes): KiCad still wants a pad size, and setting it to
            # the drill gives the zero ring the source describes.
            if p["size"] == 0:
                w = h = p["drill"]
            kind = "thru_hole" if p["plated"] else "np_thru_hole"
            # PADS plots no soldermask opening on the NPTH holes (checked on all
            # 25 against top-sm.GTS/bot-sm.GBS: no stroke within 23.6 mil), so
            # "*.Mask" here would add 25 openings per side that the source does
            # not have.
            layers = '"*.Cu" "*.Mask"' if p["plated"] else '"*.Cu"'
        elif p["inner_size"] or p["far_size"]:
            # A pad with copper on both sides (or on the inner layers) and no
            # drill: the Morse paddle contacts are 76 x 275.6 mil on levels
            # -2, -1 and 0, with mask openings on both sides in top.GTS and
            # bot.GBS.  KiCad plots a multi-layer "smd"/"connect" pad on every
            # listed copper layer, but its connectivity graph never joins the
            # inner-layer tracks to it (measured on a four-case test board).
            # A through-hole pad with a zero drill keeps the copper and the
            # mask, adds nothing to the Excellon file, and connects; the one
            # cost is the through_hole_pad_without_hole DRC error per pad.
            kind = "thru_hole"
            layers = '"*.Cu" "*.Mask"'
        else:
            kind = "smd"
            layers = f'"{pad_side}" "{pad_paste}" "{pad_mask}"'
        body = [
            f'\t\t(pad "{pin}" {kind} {shape}',
            f'\t\t\t(at {px - fp_x:.4f} {py - fp_y:.4f} {ang:.4f})',
            f'\t\t\t(size {w * MIL:.4f} {h * MIL:.4f})',
            f'\t\t\t(layers {layers})',
        ]
        if drill > 0 or kind == "thru_hole":
            body.insert(3, f'\t\t\t(drill {drill:.4f})')
        if shape == "roundrect":
            body.append(f'\t\t\t(roundrect_rratio {p["corner"] / min(w, h):.4f})')
        if drill > 0 and p["inner_size"] and abs(p["inner_size"] - p["size"]) > 0.01:
            # PADS keeps a separate pad size for the inner layers; KiCad's
            # default thru-hole pad has one size for all copper.  Without this
            # the 224.41 mil M2/M3 outer pad was used on In1.Cu too and swallowed
            # five tracks that clear the 157.48 mil source pad.
            body.append(
                '\t\t\t(padstack\n'
                '\t\t\t\t(mode front_inner_back)\n'
                '\t\t\t\t(layer "Inner"\n'
                f'\t\t\t\t\t(shape {shape})\n'
                f'\t\t\t\t\t(size {p["inner_size"] * MIL:.4f} {p["inner_size"] * MIL:.4f})\n'
                '\t\t\t\t)\n'
                '\t\t\t)')
        body.append(f'\t\t\t(uuid "{uid()}"){net}')
        body[-1] += "\n\t\t)"
        out.extend(body)
    if silk:
        emit_footprint_silk(part, fp_x, fp_y, decal, out)
    out.append("\t)")
    return "\n".join(out)


def parse_board_silk(lines):
    """Return the *LINES* pieces on the two silkscreen layers.

    Each record is ``NAME LINES XLOC YLOC PIECES FLAGS`` and its piece
    vertices are relative to XLOC/YLOC.  Layer 26 is the top silk and 29 the
    bottom; the 15-18 annotation levels of the same section stay out.
    """
    start = next(i for i, l in enumerate(lines) if l.startswith("*LINES*"))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith("*VIA*"))
    header = re.compile(r"^\S+\s+LINES\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s*$")
    piece = re.compile(r"^(OPEN|CLOSED|CIRCLE|TAG)\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(\d+)\s*$")
    pieces = []
    i = start
    while i < end:
        h = header.match(lines[i])
        if not h:
            i += 1
            continue
        xloc, yloc, count = int(h.group(1)), int(h.group(2)), int(h.group(3))
        i += 1
        for _ in range(count):
            m = piece.match(lines[i].strip())
            if not m:
                break
            kind, n = m.group(1), int(m.group(2))
            level = int(m.group(5))
            pts = []
            for k in range(n):
                vals = [int(v) for v in lines[i + 1 + k].split()]
                vals[0] += xloc
                vals[1] += yloc
                if len(vals) == 8:
                    for q in (4, 5, 6, 7):
                        vals[q] += xloc if q % 2 == 0 else yloc
                pts.append(vals)
            if level in (26, 29):
                pieces.append({"level": level, "kind": kind,
                               "width": int(m.group(3)), "pts": pts})
            i += n + 1
    return pieces


def parse_free_text(lines):
    """Return the *TEXT* strings: coord line, font line, text line."""
    start = next(i for i, l in enumerate(lines) if l.startswith("*TEXT*"))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith("*LINES*"))
    pattern = re.compile(
        r"^\s*(-?\d+)\s+(-?\d+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+"
        r"([NYM])\s+(LEFT|CENTER|RIGHT)\s+(UP|CENTER|DOWN)")
    out = []
    i = start
    while i < end:
        m = pattern.match(lines[i])
        if not m or i + 2 >= end:
            i += 1
            continue
        out.append({
            "x": int(m.group(1)), "y": int(m.group(2)),
            "ori": float(m.group(3)), "level": int(m.group(4)),
            "height": int(m.group(5)), "width": int(m.group(6)),
            "mirrored": m.group(7), "hjust": m.group(8), "vjust": m.group(9),
            "text": lines[i + 2].strip(),
        })
        i += 3
    return out


def silk_geometry(kind, pts):
    """Yield ('line', a, b) / ('arc', a, b, mid) / ('circle', a, b).

    ``pts`` are ASCII-unit vertices; an eight-number vertex starts an arc that
    ends at the next vertex (see :func:`arc_midpoint`).
    """
    if kind == "CIRCLE":
        return [("circle", pts[0][:2], pts[1][:2])]
    ring = pts + [pts[0]] if kind == "CLOSED" else pts
    out = []
    for v, nxt in zip(ring, ring[1:]):
        if len(v) == 8:
            out.append(("arc", v[:2], nxt[:2], arc_midpoint(v)))
        else:
            out.append(("line", v[:2], nxt[:2]))
    return out


def _stroke(width):
    return f"(stroke (width {width:.4f}) (type solid))"


def _justify(hjust, vjust, mirror=False):
    """PADS LEFT/CENTER/RIGHT + UP/CENTER/DOWN -> KiCad justify tokens.

    ``mirror`` is required for text on back layers; without it KiCad DRC flags
    the item and plots it unreadable.
    """
    parts = []
    if hjust != "CENTER":
        parts.append(hjust.lower())
    if vjust != "CENTER":
        parts.append({"UP": "top", "DOWN": "bottom"}[vjust])
    if mirror:
        parts.append("mirror")
    return f" (justify {' '.join(parts)})" if parts else ""


def emit_footprint_silk(part, fp_x, fp_y, decal, out):
    """Decal graphics on levels 0/1/26 as fp_line/fp_arc/fp_circle.

    Level 26 is the part-side silkscreen: a mirrored part's 26 mirrors to 29,
    which is what the ``Bottom Silkscreen`` CAM doc plots.  Levels 0 and 1 are
    *absolutely* top-side: every top part's 0/1 graphics land on GTO (e.g. all
    five top C1210s and the three LEDs at 100% coverage), and no bottom part's
    0/1 graphics are on GTO or GBO (its layer 1 would mirror to 4, and the
    bottom doc lists ``DOC_OUTLINES None`` for that layer).  Levels 20/23/27/29
    are drawn nowhere: 20 is the courtyard cross, 27 the assembly outline, and
    J170's level-29 rectangle is absent from both silks under every part
    transform variant.  The decal-local vertices travel through the same part
    transform as the pads.
    """
    def local(px, py):
        x, y = kicad_point(part, int(round(px)), int(round(py)))
        return x - fp_x, y - fp_y

    mirrored = part["mirror"] == "M"
    if mirrored:
        side_layer = "B.SilkS"
    else:
        side_layer = "F.SilkS"
    for g in decal.get("graphics", []):
        level = g["level"]
        if level == 26:
            layer = side_layer
        elif level in (0, 1) and not mirrored:
            layer = "F.SilkS"
        else:
            continue
        width = g["width"] / UNITS_PER_MIL * MIL
        for seg in silk_geometry(g["kind"], g["pts"]):
            if seg[0] == "line":
                if seg[1][:2] == seg[2][:2]:
                    continue          # PADS skips zero-length silk strokes too
                x1, y1 = local(*seg[1])
                x2, y2 = local(*seg[2])
                out.append(f'\t\t(fp_line\n\t\t\t(start {x1:.4f} {y1:.4f})\n'
                           f'\t\t\t(end {x2:.4f} {y2:.4f})\n'
                           f'\t\t\t{_stroke(width)}\n\t\t\t(layer "{layer}")\n'
                           f'\t\t\t(uuid "{uid()}")\n\t\t)')
            elif seg[0] == "arc":
                x1, y1 = local(*seg[1])
                xm, ym = local(*seg[3])
                x2, y2 = local(*seg[2])
                out.append(f'\t\t(fp_arc\n\t\t\t(start {x1:.4f} {y1:.4f})\n'
                           f'\t\t\t(mid {xm:.4f} {ym:.4f})\n'
                           f'\t\t\t(end {x2:.4f} {y2:.4f})\n'
                           f'\t\t\t{_stroke(width)}\n\t\t\t(layer "{layer}")\n'
                           f'\t\t\t(uuid "{uid()}")\n\t\t)')
            else:
                x1, y1 = local(*seg[1])
                x2, y2 = local(*seg[2])
                cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                out.append(f'\t\t(fp_circle\n\t\t\t(center {cx:.4f} {cy:.4f})\n'
                           f'\t\t\t(end {x2:.4f} {y2:.4f})\n'
                           f'\t\t\t{_stroke(width)}\n\t\t\t(layer "{layer}")\n'
                           f'\t\t\t(uuid "{uid()}")\n\t\t)')


def emit_board_silk(pieces, out):
    """Board-level *LINES* silk as gr_line/gr_arc/gr_circle."""
    for g in pieces:
        layer = "F.SilkS" if g["level"] == 26 else "B.SilkS"
        width = g["width"] / UNITS_PER_MIL * MIL
        for seg in silk_geometry(g["kind"], g["pts"]):
            if seg[0] == "line":
                x1, y1 = seg[1][0] / UNITS_PER_MIL * MIL, -seg[1][1] / UNITS_PER_MIL * MIL
                x2, y2 = seg[2][0] / UNITS_PER_MIL * MIL, -seg[2][1] / UNITS_PER_MIL * MIL
                out.append(f'\t(gr_line\n\t\t(start {x1:.4f} {y1:.4f})\n'
                           f'\t\t(end {x2:.4f} {y2:.4f})\n\t\t{_stroke(width)}\n'
                           f'\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n\t)')
            elif seg[0] == "arc":
                x1, y1 = seg[1][0] / UNITS_PER_MIL * MIL, -seg[1][1] / UNITS_PER_MIL * MIL
                xm, ym = seg[3][0] / UNITS_PER_MIL * MIL, -seg[3][1] / UNITS_PER_MIL * MIL
                x2, y2 = seg[2][0] / UNITS_PER_MIL * MIL, -seg[2][1] / UNITS_PER_MIL * MIL
                out.append(f'\t(gr_arc\n\t\t(start {x1:.4f} {y1:.4f})\n'
                           f'\t\t(mid {xm:.4f} {ym:.4f})\n'
                           f'\t\t(end {x2:.4f} {y2:.4f})\n\t\t{_stroke(width)}\n'
                           f'\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n\t)')
            else:
                x1, y1 = seg[1][0] / UNITS_PER_MIL * MIL, -seg[1][1] / UNITS_PER_MIL * MIL
                x2, y2 = seg[2][0] / UNITS_PER_MIL * MIL, -seg[2][1] / UNITS_PER_MIL * MIL
                cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                out.append(f'\t(gr_circle\n\t\t(center {cx:.4f} {cy:.4f})\n'
                           f'\t\t(end {x2:.4f} {y2:.4f})\n\t\t{_stroke(width)}\n'
                           f'\t\t(fill none)\n'
                           f'\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n\t)')


def emit_text(text, x, y, ori, height, width, hjust, vjust, layer, out,
              mirror=False):
    """One gr_text at absolute board coordinates (PADS ASCII units)."""
    kx, ky = x / UNITS_PER_MIL * MIL, -y / UNITS_PER_MIL * MIL
    size = height / UNITS_PER_MIL * MIL
    thick = width / UNITS_PER_MIL * MIL
    out.append(f'\t(gr_text "{quoted(text)}"\n\t\t(at {kx:.4f} {ky:.4f} {ori % 360:.4f})\n'
               f'\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n'
               f'\t\t(effects (font (size {size:.4f} {size:.4f}) '
               f'(thickness {thick:.4f})){_justify(hjust, vjust, mirror)})\n\t)')


def emit_labels(parts, out):
    """One Ref.Des. gr_text per part, on the part's side.

    A part can carry several Ref.Des. blocks (Q178 has one on layer 1 and one
    on 27); the layer-1 block is the silkscreen one, so it wins when present.
    Part Type and Comment are not plotted by the 2.6.1 CAM job and are skipped.
    """
    emitted = 0
    skipped = []
    for ref in sorted(parts):
        part = parts[ref]
        labels = [l for l in part.get("labels", []) if l["kind"] == "Ref.Des."]
        if not labels:
            skipped.append(ref)
            continue
        lab = next((l for l in labels if l["level"] == 1), labels[0])
        bx, by = transform(part, lab["x"], lab["y"], "x", 1, "rotate-then-mirror")
        layer = "B.SilkS" if part["mirror"] == "M" else "F.SilkS"
        emit_text(ref, bx, by, lab["ori"], lab["height"], lab["width"],
                  lab["hjust"], lab["vjust"], layer, out,
                  mirror=(layer == "B.SilkS"))
        emitted += 1
    return emitted, skipped


def parse_pours(lines):
    """Return ``[(net, layer, [vertices])]`` for the POUROUT polygons.

    Only ``POUROUT`` is the copper boundary; the ``HATOUT`` records after each
    pour are the source tool's already-hatched islands and KiCad re-derives
    them from the zone.  Vertices are relative to the record's XLOC/YLOC and
    repeat the first point at the end.  PADS pours extend past the board edge;
    KiCad clips them at Edge.Cuts when filling.
    """
    start = next(i for i, l in enumerate(lines) if l.startswith("*POUR*"))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith("*TESTPOINT*"))
    pours = []
    i = start
    while i < end:
        tok = lines[i].split()
        if len(tok) >= 8 and tok[1] == "POUROUT":
            net, xloc, yloc = tok[7], int(tok[2]), int(tok[3])
            i += 1
            poly = lines[i].split()
            count, arc_count, _width, level = (int(v) for v in poly[1:5])
            if arc_count:
                raise SystemExit(f"pour {tok[0]} has {arc_count} arc corners")
            pts = []
            for k in range(count):
                row = [int(v) for v in lines[i + 1 + k].split()]
                pts.append((row[0] + xloc, row[1] + yloc))
            if pts[0] != pts[-1]:
                raise SystemExit(f"pour {tok[0]} is not closed")
            pours.append((net, LAYER[level], pts[:-1]))
            i += 1 + count
        else:
            i += 1
    return pours


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("asc")
    ap.add_argument("--net", default="", help="emit just this net")
    ap.add_argument("--all", action="store_true", help="emit every part and net")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    if bool(args.net) == bool(args.all):
        raise SystemExit("give exactly one of --net NAME or --all")

    lines = open(args.asc, encoding="latin-1").read().splitlines()
    decals = parse_decals(lines)
    types = parse_parttypes(lines)
    parts = parse_parts(lines)
    outline = parse_outline(lines)
    pours = parse_pours(lines) if args.all else []
    board_silk = parse_board_silk(lines) if args.all else []
    free_text = parse_free_text(lines) if args.all else []

    all_conns = list(connections(lines))
    conns = all_conns if args.all else [c for c in all_conns if c[0] == args.net]
    if not conns:
        raise SystemExit(f"net {args.net} not found in *ROUTE*")

    net_names = list(dict.fromkeys(c[0] for c in conns))
    net_id = {n: i + 1 for i, n in enumerate(net_names)}
    net_id[None] = 0
    unrouteable = sorted({n for n, _l, _p in pours} - set(net_names))
    if unrouteable:
        raise SystemExit(f"pour nets without tracks: {unrouteable}")

    pad_net = {}
    conflicts = []
    for net, ra, pa, rb, pb, _pts in conns:
        for ref, pin in ((ra, pa), (rb, pb)):
            if ref not in parts:
                raise SystemExit(f"route endpoint {ref}.{pin} is not a *PART*")
            if pad_net.get((ref, pin), net) != net:
                conflicts.append(((ref, pin), pad_net[(ref, pin)], net))
            pad_net[(ref, pin)] = net
    refs = sorted({r for r, _p in pad_net}) if not args.all else sorted(parts)

    segs = []
    arc_segs = []
    vias = []
    for net, _ra, _pa, _rb, _pb, pts in conns:
        route_lines, arcs, route_vias = route_geometry(pts)
        segs.extend((a, b, layer, width, net) for layer, a, b, width in route_lines)
        arc_segs.extend((a, centre, b, ccw, layer, width, net)
                        for layer, a, centre, b, ccw, width in arcs)
        vias.extend((v[0], v[1], net) for v in route_vias)

    # PADS lists a net's connections again inside every *SIGNAL* block, and a via
    # that several branches meet at is listed once per branch.  Emitting the
    # repeats stacked 199 pairs of drills on one spot (holes_co_located).
    raw_segs, raw_arcs, raw_vias = len(segs), len(arc_segs), len(vias)
    segs = list(dict.fromkeys(segs))
    arc_segs = list(dict.fromkeys(arc_segs))
    vias = list(dict.fromkeys(vias))

    out = []
    out.append('(kicad_pcb\n\t(version 20260206)\n\t(generator "pcbnew")\n'
               '\t(generator_version "10.0")\n\t(general\n\t\t(thickness 1.6)\n'
               '\t\t(legacy_teardrops no)\n\t)\n\t(paper "A4")\n\t(layers')
    for num, name, kind in ((0, "F.Cu", "signal"), (4, "In1.Cu", "signal"),
                            (6, "In2.Cu", "signal"), (2, "B.Cu", "signal")):
        out.append(f'\t\t({num} "{name}" {kind})')
    for num, name, alias in ((9, "F.Adhes", "F.Adhesive"), (11, "B.Adhes", "B.Adhesive"),
                             (13, "F.Paste", None), (15, "B.Paste", None),
                             (5, "F.SilkS", "F.Silkscreen"), (7, "B.SilkS", "B.Silkscreen"),
                             (1, "F.Mask", None), (3, "B.Mask", None),
                             (25, "Edge.Cuts", None), (35, "F.Fab", None)):
        alias_part = f' "{alias}"' if alias else ""
        out.append(f'\t\t({num} "{name}" user{alias_part})')
    out.append('\t)\n\t(setup\n\t\t(pad_to_mask_clearance 0)\n'
               '\t\t(allow_soldermask_bridges_in_footprints no)\n\t)\n'
               '\t(embedded_fonts no)')
    out.append('\t(net 0 "")')
    for name in net_names:
        out.append(f'\t(net {net_id[name]} "{quoted(name)}")')

    emitted_pads = 0
    netted_pads = 0
    unrouted = []
    for ref in refs:
        part = parts[ref]
        decal_name = types.get(part["type"], "").split(":")[-1]
        decal = decals.get(decal_name)
        if not decal:
            raise SystemExit(f"{ref}: decal {decal_name} not found")
        pins = {p: (net_id[n], n) for (r, p), n in pad_net.items() if r == ref}
        terminals = {t[0] for t in decal["terminals"]}
        stray = set(pins) - terminals
        if stray:
            raise SystemExit(f"{ref}: net assigned to {sorted(stray)}, which are "
                             f"not terminals of {decal_name} {sorted(terminals)}")
        emitted_pads += len(decal["terminals"])
        netted_pads += sum(1 for t in decal["terminals"] if t[0] in pins)
        unrouted.extend((ref, p) for p in terminals if p not in pins)
        out.append(footprint(ref, part, decal, decal_name, pins, silk=args.all))

    zero_len = 0
    for (ax, ay), (bx, by), layer, width, net in segs:
        x1, y1 = ax / UNITS_PER_MIL * MIL, -ay / UNITS_PER_MIL * MIL
        x2, y2 = bx / UNITS_PER_MIL * MIL, -by / UNITS_PER_MIL * MIL
        # a repeated vertex one ASCII unit apart becomes an invisible track
        if (round(x1, 4), round(y1, 4)) == (round(x2, 4), round(y2, 4)):
            zero_len += 1
            continue
        out.append(f'\t(segment\n\t\t(start {x1:.4f} {y1:.4f})\n'
                   f'\t\t(end {x2:.4f} {y2:.4f})\n'
                   f'\t\t(width {width / UNITS_PER_MIL * MIL:.4f})\n'
                   f'\t\t(layer "{LAYER[layer]}")\n\t\t(net {net_id[net]})\n'
                   f'\t\t(uuid "{uid()}")\n\t)')

    for (ax, ay), (cx, cy), (bx, by), ccw, layer, width, net in arc_segs:
        x1, y1 = ax / UNITS_PER_MIL * MIL, -ay / UNITS_PER_MIL * MIL
        x2, y2 = bx / UNITS_PER_MIL * MIL, -by / UNITS_PER_MIL * MIL
        mx, my = arc_mid((ax, ay), (cx, cy), (bx, by), ccw)
        out.append(f'\t(arc\n\t\t(start {x1:.4f} {y1:.4f})\n'
                   f'\t\t(mid {mx / UNITS_PER_MIL * MIL:.4f} {my / UNITS_PER_MIL * -MIL:.4f})\n'
                   f'\t\t(end {x2:.4f} {y2:.4f})\n'
                   f'\t\t(width {width / UNITS_PER_MIL * MIL:.4f})\n'
                   f'\t\t(layer "{LAYER[layer]}")\n\t\t(net {net_id[net]})\n'
                   f'\t\t(uuid "{uid()}")\n\t)')

    for gx, gy, net in vias:
        x, y = gx / UNITS_PER_MIL * MIL, -gy / UNITS_PER_MIL * MIL
        out.append(f'\t(via\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size 0.8128)\n'
                   f'\t\t(drill 0.3556)\n\t\t(layers "F.Cu" "B.Cu")\n'
                   f'\t\t(net {net_id[net]})\n\t\t(uuid "{uid()}")\n\t)')

    for net, layer, pts in pours:
        xy = " ".join(f"(xy {x / UNITS_PER_MIL * MIL:.4f} {-y / UNITS_PER_MIL * MIL:.4f})"
                      for x, y in pts)
        out.append(f'\t(zone\n\t\t(net "{quoted(net)}")\n\t\t(layer "{layer}")\n'
                   f'\t\t(uuid "{uid()}")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads\n'
                   f'\t\t\t(clearance 0.254)\n\t\t)\n\t\t(min_thickness 0.254)\n'
                   f'\t\t(fill\n\t\t\t(thermal_gap 0.254)\n'
                   f'\t\t\t(thermal_bridge_width 0.254)\n'
                   f'\t\t\t(island_removal_mode 0)\n\t\t)\n\t\t(polygon\n\t\t\t(pts\n'
                   f'\t\t\t\t{xy}\n\t\t\t)\n\t\t)\n\t)')

    if args.all:
        emit_board_silk(board_silk, out)
        for t in free_text:
            layer = "F.SilkS" if t["level"] == 26 else "B.SilkS"
            emit_text(t["text"], t["x"], t["y"], t["ori"], t["height"],
                      t["width"], t["hjust"], t["vjust"], layer, out,
                      mirror=(t["mirrored"] == "M" or layer == "B.SilkS"))
        labels, no_label = emit_labels(parts, out)

    w = max(p[0] for s in outline for p in s[1:3]) / UNITS_PER_MIL * MIL
    h = max(p[1] for s in outline for p in s[1:3]) / UNITS_PER_MIL * MIL
    for seg in outline:
        if seg[0] == "line":
            _kind, a, b = seg
            x1, y1 = a[0] / UNITS_PER_MIL * MIL, -a[1] / UNITS_PER_MIL * MIL
            x2, y2 = b[0] / UNITS_PER_MIL * MIL, -b[1] / UNITS_PER_MIL * MIL
            out.append(f'\t(gr_line\n\t\t(start {x1:.4f} {y1:.4f})\n'
                       f'\t\t(end {x2:.4f} {y2:.4f})\n'
                       f'\t\t(stroke (width 0.1) (type default))\n'
                       f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uid()}")\n\t)')
        else:
            _kind, a, b, m = seg
            x1, y1 = a[0] / UNITS_PER_MIL * MIL, -a[1] / UNITS_PER_MIL * MIL
            x2, y2 = b[0] / UNITS_PER_MIL * MIL, -b[1] / UNITS_PER_MIL * MIL
            mx, my = m[0] / UNITS_PER_MIL * MIL, -m[1] / UNITS_PER_MIL * MIL
            out.append(f'\t(gr_arc\n\t\t(start {x1:.4f} {y1:.4f})\n'
                       f'\t\t(mid {mx:.4f} {my:.4f})\n'
                       f'\t\t(end {x2:.4f} {y2:.4f})\n'
                       f'\t\t(stroke (width 0.1) (type default))\n'
                       f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uid()}")\n\t)')

    out.append(")")
    text = "\n".join(out) + "\n"
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    open(args.out, "w", encoding="utf-8", newline="\n").write(text)

    print(f"nets          {len(net_names)}")
    print(f"parts         {len(refs)}")
    print(f"pads emitted  {emitted_pads}  ({netted_pads} carry a net, "
          f"{len(unrouted)} do not)")
    print(f"track segments {len(segs) - zero_len} written ({zero_len} zero-length "
          f"dropped) of {len(segs)} distinct of {raw_segs}  layers "
          f"{sorted({LAYER[s[2]] for s in segs})}")
    print(f"track arcs    {len(arc_segs)} distinct of {raw_arcs}")
    print(f"vias          {len(vias)} distinct of {raw_vias}")
    n_line = sum(1 for s in outline if s[0] == "line")
    print(f"outline       {n_line} lines + {len(outline) - n_line} arcs, "
          f"{w:.2f} x {h:.2f} mm")
    by_layer = {}
    for _net, layer, _pts in pours:
        by_layer[layer] = by_layer.get(layer, 0) + 1
    print(f"pours         {len(pours)} zones {by_layer}")
    if args.all:
        decal_pieces = sum(1 for d in decals.values() for g in d["graphics"]
                           if g["level"] in (0, 1, 26))
        by_level = {}
        for g in board_silk:
            by_level[g["level"]] = by_level.get(g["level"], 0) + 1
        print(f"silk          {decal_pieces} decal pieces, "
              f"{len(board_silk)} board pieces {by_level}, "
              f"{len(free_text)} free texts, {labels} refdes labels "
              f"({len(no_label)} parts without one)")
    print(f"pad-net conflicts: {len(conflicts)} {conflicts[:5]}")
    print(f"wrote         {args.out}")


if __name__ == "__main__":
    main()
