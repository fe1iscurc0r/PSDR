#!/usr/bin/env python3
"""Reader for PADS Layout 9.5 ASCII exports (.emn board / .emp decal package).

This is *not* the PowerPCB dialect that KiCad's `pcb import --format pads`
expects (`*PADS-POWERPCB*` with `$NET_INFO` / `$A` component records).  The
files shipped in Hardware/BOMs/PSDR_2.6.1/ are the `BOARD_FILE 3.0` ASCII
export, which KiCad reads as an empty board without complaining.  Parsing it
here is the only way to recover outline, holes and placement.

Column offsets were measured off the real files, so they are fixed-width
slices rather than whitespace splits -- hole names such as "M3" sit in a
variable-width field and a naive split() would mis-assign them.
"""

import os

OUTLINE_TAG = slice(0, 6)
OUTLINE_X = slice(6, 36)
OUTLINE_Y = slice(36, 66)
OUTLINE_ARC = slice(66, 96)

MOVE_X = slice(0, 30)
MOVE_Y = slice(30, 60)
MOVE_Z = slice(60, 90)
MOVE_ROT = slice(90, 100)
MOVE_SIDE = slice(100, 110)
MOVE_STATE = slice(110, 120)

NAME_TYPE = slice(0, 45)
NAME_DECAL = slice(45, 90)
NAME_REFDES = slice(90, None)


def _lines(path):
    with open(path, "rb") as fh:
        raw = fh.read().decode("latin-1")
    return raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _sections(lines):
    """Yield (section_name, [body_lines]) for every `.X ... .END_X` block."""
    current = None
    body = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("."):
            head = stripped.split()[0]
            if head.startswith(".END_"):
                if current:
                    yield current, body
                current, body = None, []
                continue
            if current:
                yield current, body
            current, body = head[1:], []
            continue
        if current is not None:
            body.append(line)
    if current:
        yield current, body


def _f(text, default=0.0):
    try:
        return float(text)
    except ValueError:
        return default


def parse_emn(path):
    """Return dict(units, outline, holes, components, stray)."""
    sections = dict(_sections(_lines(path)))
    units = "THOU"
    header = sections.get("HEADER", [])
    for line in header:
        for token in line.split():
            if token in ("THOU", "MM"):
                units = token

    outline = []
    stray = []
    for line in sections.get("BOARD_OUTLINE", []):
        if not line.strip():
            continue
        x_raw = line[OUTLINE_X].strip()
        if not _looks_numeric(x_raw):
            stray.append(line.strip())
            continue
        outline.append((
            line[OUTLINE_TAG].strip(),
            _f(x_raw),
            _f(line[OUTLINE_Y].strip()),
            _f(line[OUTLINE_ARC].strip()),
        ))

    holes = []
    for line in sections.get("DRILLED_HOLES", []):
        token = line.split()
        if len(token) < 4:
            continue
        holes.append({
            "drill": _f(token[0]),
            "x": _f(token[1]),
            "y": _f(token[2]),
            "plating": token[3],
            "name": " ".join(token[4:-2]) if len(token) > 6 else (token[4] if len(token) > 4 else ""),
            "kind": token[-2],
            "owner": token[-1],
        })

    components = []
    body = sections.get("PLACEMENT", [])
    pair = [body[i:i + 2] for i in range(0, len(body) - 1, 2)]
    for names, moves in pair:
        if not moves.strip():
            continue
        if not _looks_numeric(moves[MOVE_X].strip()):
            raise ValueError("placement record out of alignment: %r / %r" % (names, moves))
        components.append({
            "part_type": names[NAME_TYPE].strip(),
            "decal": names[NAME_DECAL].strip(),
            "refdes": names[NAME_REFDES].strip(),
            "x": _f(moves[MOVE_X].strip()),
            "y": _f(moves[MOVE_Y].strip()),
            "z": _f(moves[MOVE_Z].strip()),
            "rot": _f(moves[MOVE_ROT].strip()),
            "side": moves[MOVE_SIDE].strip(),
            "state": moves[MOVE_STATE].strip(),
        })

    return {"units": units, "outline": outline, "holes": holes,
            "components": components, "stray": stray,
            "sections": sorted(sections)}


def _looks_numeric(text):
    if not text:
        return False
    try:
        float(text)
        return True
    except ValueError:
        return False


def parse_emp(path):
    """Return {decal_name: dict(part_type, units, scalar, polygon)} .

    `.emp` is the decal package: one `.ELECTRICAL` block per footprint, and
    each block holds only the body outline polygon -- there are no pad stacks
    in this export, which is why pad geometry has to be recovered from the
    Gerbers instead.
    """
    decals = {}
    for name, body in _sections(_lines(path)):
        if name != "ELECTRICAL":
            continue
        head = None
        poly = []
        for line in body:
            if not line.strip():
                continue
            if head is None:
                head = line
                continue
            token = line.split()
            if len(token) >= 3:
                poly.append((_f(token[1]), _f(token[2])))
        if head is None:
            continue
        token = head.split()
        decals[token[1]] = {
            "part_type": token[0],
            "decal": token[1],
            "units": token[2] if len(token) > 2 else "THOU",
            "scalar": _f(token[3]) if len(token) > 3 else 0.0,
            "polygon": poly,
        }
    return decals


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    emn = os.path.join(root, "Hardware", "BOMs", "PSDR_2.6.1", "psdr26.emn")
    emp = os.path.join(root, "Hardware", "BOMs", "PSDR_2.6.1", "psdr26.emp")
    board = parse_emn(emn)
    decals = parse_emp(emp)
    print("units      :", board["units"])
    print("sections   :", board["sections"])
    print("outline    : %d vertices, %d arced, closed=%s" % (
        len(board["outline"]),
        sum(1 for v in board["outline"] if v[3]),
        board["outline"][0][1:3] == board["outline"][-1][1:3]))
    print("stray      :", board["stray"])
    print("holes      :", len(board["holes"]))
    from collections import Counter
    print("  plating  :", dict(Counter(h["plating"] for h in board["holes"])))
    print("  kind     :", dict(Counter(h["kind"] for h in board["holes"])))
    print("  drills   :", sorted({h["drill"] for h in board["holes"]}))
    print("  names    :", dict(Counter(h["name"] for h in board["holes"])))
    print("components :", len(board["components"]))
    print("  side     :", dict(Counter(c["side"] for c in board["components"])))
    print("  state    :", dict(Counter(c["state"] for c in board["components"])))
    print("  decals   :", len({c["decal"] for c in board["components"]}),
          "| .emp defines", len(decals))
    missing = {c["decal"] for c in board["components"]} - set(decals)
    print("  decals missing from .emp:", sorted(missing) or "none")
