#!/usr/bin/env python3
"""Reconcile a freshly built F7 image against the author's 2018 reference hex.

The F4 gate in ``docs/psdr-handoff/anchor_check.py`` requires the reset vector to
equal its upstream value; on F7 that value moves with the linker layout, so this
gates on the two layout-independent properties instead -- initial SP and the
pattern of empty vector slots -- and reports the reset values as measurements.

Usage:
    python3 tools/anchor_check_f7.py Source_F7/build_linux_f7/PSDR.hex \
        Source_F7/Debug/PSDR.hex
"""

from __future__ import annotations

import argparse
import sys


def parse_ihex(path: str) -> tuple[int, dict[int, int]]:
    """Return ``(lowest data address, {absolute address: byte})``."""
    mem: dict[int, int] = {}
    upper = 0
    base: int | None = None
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith(":"):
                continue
            raw = bytes.fromhex(line[1:])
            count = raw[0]
            addr = (raw[1] << 8) | raw[2]
            rectype, data = raw[3], raw[4:4 + count]
            if rectype == 0x00:
                for i, value in enumerate(data):
                    absolute = upper + addr + i
                    mem[absolute] = value
                    if base is None or absolute < base:
                        base = absolute
            elif rectype == 0x04:
                upper = ((data[0] << 8) | data[1]) << 16
            elif rectype == 0x02:
                upper = ((data[0] << 8) | data[1]) << 4
            elif rectype == 0x01:
                break
    if base is None:
        raise SystemExit(f"{path}: no data records")
    return base, mem


def vector_words(mem: dict[int, int], base: int, count: int) -> list[int | None]:
    return [sum(mem[base + 4 * i + j] << (8 * j) for j in range(4))
            if all(base + 4 * i + j in mem for j in range(4)) else None
            for i in range(count)]


def hexw(value: int | None) -> str:
    return "--------" if value is None else f"0x{value:08X}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("built")
    ap.add_argument("reference")
    ap.add_argument("--words", type=int, default=118)
    args = ap.parse_args()

    tables = {}
    for label, path in (("reference", args.reference), ("built", args.built)):
        base, mem = parse_ihex(path)
        table = vector_words(mem, base, args.words)
        tables[label] = table
        print(f"{label:9s} {path}\n          base={hexw(base)}  SP={hexw(table[0])}"
              f"  reset={hexw(table[1])}  empty-slots="
              f"{[i for i, w in enumerate(table) if w == 0]}")

    ref, new = tables["reference"], tables["built"]
    sp_ok = ref[0] == new[0]
    slots_ok = [i for i, w in enumerate(ref) if w == 0] == [i for i, w in enumerate(new) if w == 0]
    print(f"initial SP agree     : {sp_ok}")
    print(f"empty-slot pattern   : {slots_ok}")
    print(f"reset value agree    : {ref[1] == new[1]} (not a gate)")
    print(f"words equal          : {sum(1 for a, b in zip(ref, new) if a == b)}/{args.words}")
    print("RESULT: " + ("PASS" if sp_ok and slots_ok else "FAIL"))
    return 0 if sp_ok and slots_ok else 1


if __name__ == "__main__":
    sys.exit(main())
