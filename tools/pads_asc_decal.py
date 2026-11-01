#!/usr/bin/env python3
"""Decode PADS Layout ASCII footprints (PARTDECAL) and check them against routing.

The ASCII file stores, for every part, a decal reference and a placement
(x, y, rotation, mirror).  The decal stores terminal offsets and pad stacks.
If both are decoded correctly, then the pad centre computed for ``U287.3``
must coincide with the first point of a routed connection that starts at
``U287.3``.  That is the check this script performs: it needs no external
reference geometry, because the routing and the decals come from the same
database.

Coordinates in the file are integers; 38100 of them make one mil.  That factor
is not documented in the file - it is derived from the board outline, whose
y extent is 97,497,900 units and 2559 mil in the .emn, and confirmed by the
decal values all becoming round numbers in mils (952500 -> 25 mil).
"""

import argparse
import collections
import math
import re
import sys

UNITS_PER_MIL = 38100

DECAL_HEADER = re.compile(
    r"^(\S+)\s+([A-Z])\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$"
)
PARTTYPE_HEADER = re.compile(r"^(\S+)\s+(\S+)\s+([A-Z]{2,4})\s+")
PART_HEADER = re.compile(
    r"^(\S+)\s+(\S+)\s+(-?\d+)\s+(-?\d+)\s+(-?[\d.]+)\s+(\S)\s+(\S)\s+"
)
PAD_HEADER = re.compile(r"^PAD\s+(\S+)\s+(\d+)\s*$")
TERMINAL = re.compile(r"^T\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\S+)\s*$")
CONNECTION = re.compile(r"^(\S+)\.(\S+)\s+(\S+)\.(\S+)\s*$")
SECTION = re.compile(r"^\*([A-Z][A-Z0-9_]*)\*")
COORD = re.compile(r"^(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\b")


def index(lines, name):
    for i, line in enumerate(lines):
        if line.startswith(name):
            return i
    raise SystemExit(f"section {name} not found")


def parse_decals(lines):
    """Return {decal name: {"terminals": [(pin, tx, ty)], "pads": {pin: [...]}}}."""
    start = index(lines, "*PARTDECAL*")
    end = index(lines, "*PARTTYPE*")
    decals = {}
    i = start
    while i < end:
        m = DECAL_HEADER.match(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        terminals = []
        pads = {}
        i += 1
        while i < end and not DECAL_HEADER.match(lines[i]):
            t = TERMINAL.match(lines[i].strip())
            if t:
                terminals.append((t.group(5), int(t.group(1)), int(t.group(2))))
                i += 1
                continue
            p = PAD_HEADER.match(lines[i].strip())
            if p:
                pin, count = p.group(1), int(p.group(2))
                pads.setdefault(pin, []).extend(
                    lines[i + 1 + k].strip() for k in range(count)
                )
                i += count + 1
                continue
            i += 1
        decals[name] = {"terminals": terminals, "pads": pads}
    return decals


def parse_parttypes(lines):
    start = index(lines, "*PARTTYPE*")
    end = index(lines, "*PART*       ITEMS")
    types = {}
    i = start
    while i < end:
        m = PARTTYPE_HEADER.match(lines[i])
        if m and not lines[i].startswith("*"):
            name, decal = m.group(1), m.group(2)
            types[name] = decal
            # skip to the next block, which starts after the last "PINNUMBER" line
            i += 1
            while i < end and lines[i].strip() and not PARTTYPE_HEADER.match(lines[i]):
                i += 1
            continue
        i += 1
    return types


def parse_parts(lines):
    start = index(lines, "*PART*       ITEMS")
    end = index(lines, "*ROUTE*")
    parts = {}
    for i in range(start, end):
        m = PART_HEADER.match(lines[i])
        if not m:
            continue
        ref, ptype, x, y, ori, glue, mirror = (
            m.group(1), m.group(2), int(m.group(3)), int(m.group(4)),
            float(m.group(5)), m.group(6), m.group(7),
        )
        parts[ref] = {"type": ptype, "x": x, "y": y, "ori": ori, "mirror": mirror}
    return parts


def route_end(lines, start):
    """Index of the first top-level header after *ROUTE* that is not a net.

    *ROUTE* is followed by *POUR*, *TESTPOINT* and *MISC*, and the connection
    header pattern matches text in them: every
    ``Design.Timestamp 2009.06.06.18.59.11`` line in *MISC* parsed as a
    connection between ref "Design" and ref "2009.06.06.18.59", which turned
    854 real connections into 1031.  Net blocks (``*SIGNAL*``) and ``*REMARK*``
    are the only headers that belong to the route section itself.
    """
    for i in range(start + 1, len(lines)):
        m = SECTION.match(lines[i])
        if m and m.group(1) not in ("SIGNAL", "REMARK"):
            return i
    return len(lines)


def parse_connections(lines):
    """Yield (net, ref_a, pin_a, ref_b, pin_b, [points]).

    A *SIGNAL* block holds one connection header followed by the polyline of
    that connection: first point is the source pin, the rest are route
    vertices.  ``layer`` 0 and 65 mark pad points; we keep the raw values.
    """
    start = index(lines, "*ROUTE*")
    end = route_end(lines, start)
    net = None
    for i in range(start, end):
        line = lines[i].rstrip()
        if line.startswith("*SIGNAL*"):
            net = line.split()[1]
            continue
        m = CONNECTION.match(line)
        if m and net:
            points = []
            j = i + 1
            while j < len(lines):
                c = COORD.match(lines[j].strip())
                if not c:
                    break
                points.append(
                    {
                        "x": int(c.group(1)),
                        "y": int(c.group(2)),
                        "layer": int(c.group(3)),
                        "width": int(c.group(4)),
                        "flags": int(c.group(5)),
                        "text": lines[j].strip(),
                    }
                )
                j += 1
            yield net, m.group(1), m.group(2), m.group(3), m.group(4), points


def transform(part, tx, ty, mirror_axis, sign, order):
    """Map a decal-local terminal to board coordinates, in PADS units."""
    x, y = tx, ty
    mirrored = part["mirror"] == "M"
    th = math.radians(part["ori"]) * sign

    def apply_mirror(x, y):
        if not mirrored:
            return x, y
        return (-x, y) if mirror_axis == "x" else (x, -y)

    if order == "mirror-then-rotate":
        x, y = apply_mirror(x, y)
        rx = x * math.cos(th) - y * math.sin(th)
        ry = x * math.sin(th) + y * math.cos(th)
    else:
        rx = x * math.cos(th) - y * math.sin(th)
        ry = x * math.sin(th) + y * math.cos(th)
        rx, ry = apply_mirror(rx, ry)
    return part["x"] + rx, part["y"] + ry


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("asc")
    ap.add_argument("--tol", type=int, default=1,
                    help="match tolerance in ASCII units (default 1)")
    ap.add_argument("--show", default="", help="comma separated refdes to dump")
    args = ap.parse_args()

    lines = open(args.asc, encoding="latin-1").read().splitlines()
    decals = parse_decals(lines)
    types = parse_parttypes(lines)
    parts = parse_parts(lines)
    conns = list(parse_connections(lines))

    print(f"decals        {len(decals)}")
    print(f"part types    {len(types)}")
    print(f"parts         {len(parts)}")
    print(f"connections   {len(conns)}")

    missing_decal = [r for r, p in parts.items()
                     if types.get(p["type"], "").split(":")[-1] not in decals]
    if missing_decal:
        print(f"parts whose decal is missing: {len(missing_decal)} {missing_decal[:10]}")

    # terminal lookup, per (refdes, pin)
    term = {}
    for ref, p in parts.items():
        decal = decals.get(types.get(p["type"], "").split(":")[-1])
        if not decal:
            continue
        for pin, tx, ty in decal["terminals"]:
            term[(ref, pin)] = (tx, ty)

    # try both mirror axes, both rotation directions, both orders; report best
    best = None
    results = []
    for axis in ("x", "y"):
        for sign in (1, -1):
            for order in ("mirror-then-rotate", "rotate-then-mirror"):
                hit = tot = 0
                misses = collections.Counter()
                for net, ra, pa, rb, pb, pts in conns:
                    if not pts:
                        continue
                    for ref, pin, pt in ((ra, pa, pts[0]), (rb, pb, pts[-1])):
                        key = (ref, pin)
                        if key not in term:
                            continue
                        tot += 1
                        tx, ty = term[key]
                        px, py = transform(parts[ref], tx, ty, axis, sign, order)
                        if abs(px - pt["x"]) <= args.tol and abs(py - pt["y"]) <= args.tol:
                            hit += 1
                        else:
                            misses[parts[ref]["type"]] += 1
                results.append((hit, tot, axis, sign, order, misses))
                if tot and (best is None or hit > best[0]):
                    best = (hit, tot, axis, sign, order)
    for hit, tot, axis, sign, order, _ in sorted(results, reverse=True)[:4]:
        print(f"  mirror_axis={axis} rotate={'CCW' if sign > 0 else 'CW':<3} "
              f"{order:<19} {hit}/{tot} ({100.0 * hit / tot:.2f}%)")

    if best:
        hit, tot, axis, sign, order = best
        print(f"\nbest: mirror_axis={axis} rotate={'CCW' if sign > 0 else 'CW'} order={order}")
        print(f"connection endpoints landing on a pad centre: {hit}/{tot} "
              f"({100.0 * hit / tot:.2f}%)")
        misses = next(r[5] for r in results if r[:5] == best)
        print("worst part types:", misses.most_common(8))

    if args.show:
        for ref in args.show.split(","):
            p = parts.get(ref)
            if not p:
                print(f"{ref}: not found")
                continue
            decal = decals.get(types.get(p["type"], "").split(":")[-1])
            if not decal:
                print(f"{ref}: decal '{types.get(p['type'])}' not found")
                continue
            print(f"\n{ref} type={p['type']} decal={types.get(p['type'])} "
                  f"at ({p['x']},{p['y']}) ori={p['ori']} mirror={p['mirror']}")
            for pin, tx, ty in decal["terminals"][:8]:
                px, py = transform(p, tx, ty, "x", 1, "rotate-then-mirror")
                print(f"  pin {pin:>3} local ({tx/UNITS_PER_MIL:8.2f},{ty/UNITS_PER_MIL:8.2f}) mil"
                      f"  board ({px/UNITS_PER_MIL:9.2f},{py/UNITS_PER_MIL:9.2f}) mil")
            for pin, stack in list(decal["pads"].items())[:3]:
                print(f"  pads[{pin}]: {stack}")


if __name__ == "__main__":
    sys.exit(main())
