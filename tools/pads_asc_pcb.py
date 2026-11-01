#!/usr/bin/env python3
"""Emit a KiCad board from the PADS ASCII: real decal pads plus routed copper.

This is the direction-A spike, not a whole-board converter.  It places only the
parts that touch one net and copies only that net's tracks and vias, so the
output can be diffed against the source without a whole-board comparison.

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

The board outline is **not** a rectangle.  Levels 15, 16, 17 and 18 of *LINES*
(after adding each line's own XLOC/YLOC) all bound the same 3937.0 x 2559.1 mil
= 100.0 x 65.0 mm box, but they carry 258 OPEN/CIRCLE pieces between them:
rounded corners, three connector notches on the left edge and a clipped corner
at the lower right.  This emitter still draws the bounding rectangle, so treat
the Edge.Cuts here as a placeholder, not the real profile.
"""

import argparse
import itertools
import math
import os
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
BOARD_W_MIL = 3937.0
BOARD_H_MIL = 2559.1


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


def footprint(ref, part, decal, decal_name, pin_net):
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
    out.append("\t)")
    return "\n".join(out)


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

    all_conns = list(connections(lines))
    conns = all_conns if args.all else [c for c in all_conns if c[0] == args.net]
    if not conns:
        raise SystemExit(f"net {args.net} not found in *ROUTE*")

    net_names = list(dict.fromkeys(c[0] for c in conns))
    net_id = {n: i + 1 for i, n in enumerate(net_names)}
    net_id[None] = 0

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
        lines, arcs, route_vias = route_geometry(pts)
        segs.extend((a, b, layer, width, net) for layer, a, b, width in lines)
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
    for num, name, kind in ((0, "F.Cu", "signal"), (1, "In1.Cu", "power"),
                            (2, "In2.Cu", "power"), (31, "B.Cu", "signal")):
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
        out.append(footprint(ref, part, decal, decal_name, pins))

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

    w, h = BOARD_W_MIL * MIL, BOARD_H_MIL * MIL
    corners = [(0, 0), (w, 0), (w, -h), (0, -h), (0, 0)]
    for (x1, y1), (x2, y2) in zip(corners, corners[1:]):
        out.append(f'\t(gr_line\n\t\t(start {x1:.4f} {y1:.4f})\n'
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
    print(f"outline       {BOARD_W_MIL * MIL:.2f} x {BOARD_H_MIL * MIL:.2f} mm")
    print(f"pad-net conflicts: {len(conflicts)} {conflicts[:5]}")
    print(f"wrote         {args.out}")


if __name__ == "__main__":
    main()
