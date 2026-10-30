#!/usr/bin/env python3
"""Compare the vector-table anchors of a freshly built PSDR.elf against the
upstream 2016 Debug/PSDR.hex.

Usage: python3 anchor_check.py <build_linux/PSDR.elf> <Debug/PSDR.hex> [objcopy]

Checks the two anchors the workorder treats as binding (initial SP at flash
offset 0, reset vector at offset 4) and additionally reports how much of the
overlap actually matches byte-for-byte, so a partial agreement is never
reported as full agreement.
"""

import subprocess
import sys


def parse_ihex(path):
    """Return {absolute_address: byte} for an Intel HEX file."""
    mem = {}
    base = 0
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith(":"):
                continue
            raw = bytes.fromhex(line[1:])
            count, addr, rectype = raw[0], (raw[1] << 8) | raw[2], raw[3]
            data = raw[4:4 + count]
            if rectype == 0x00:
                for i, value in enumerate(data):
                    mem[base + addr + i] = value
            elif rectype == 0x01:
                break
            elif rectype == 0x02:          # extended segment address
                base = ((data[0] << 8) | data[1]) << 4
            elif rectype == 0x04:          # extended linear address
                base = ((data[0] << 8) | data[1]) << 16
    return mem


def le32(get, offset):
    return (get(offset) | get(offset + 1) << 8 | get(offset + 2) << 16 |
            get(offset + 3) << 24)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    elf, ref_hex = sys.argv[1], sys.argv[2]
    objcopy = sys.argv[3] if len(sys.argv) > 3 else "arm-none-eabi-objcopy"

    tmp = "/tmp/psdr_new_isr.bin"
    subprocess.run([objcopy, "-O", "binary", "--only-section=.isr_vector",
                    elf, tmp], check=True, capture_output=True)
    new_bin = open(tmp, "rb").read()

    upstream = parse_ihex(ref_hex)
    origin = min(upstream)
    ref = bytes(upstream.get(origin + i, 0) for i in range(len(new_bin)))

    def from_ref(offset):
        return upstream.get(origin + offset, 0)

    def from_new(offset):
        return new_bin[offset]

    anchors = (
        ("initial SP", 0x20030000, le32(from_ref, 0), le32(from_new, 0)),
        ("reset vector", 0x080001B5, le32(from_ref, 4), le32(from_new, 4)),
    )

    print("reference hex base : 0x%08X" % origin)
    print("vector bytes       : new=%d  ref=%d" % (len(new_bin), len(ref)))
    ok = True
    for name, expected, got_ref, got_new in anchors:
        agree = got_ref == got_new
        matches_target = got_new == expected
        ok = ok and agree and matches_target
        print("%-14s upstream=0x%08X  new=0x%08X  expected=0x%08X  %s" %
              (name, got_ref, got_new, expected, "OK" if agree and matches_target else "MISMATCH"))

    same = sum(1 for a, b in zip(ref, new_bin) if a == b)
    print("byte-for-byte over vector table: %d/%d (%.1f%%)" %
          (same, len(ref), 100.0 * same / max(len(ref), 1)))
    if same != len(ref):
        first = next(i for i, (a, b) in enumerate(zip(ref, new_bin)) if a != b)
        print("first divergence at vector offset %d (0x%02X)" % (first, first))
        print("  note: later vector entries move with GCC version / linker "
              "layout; the two anchors above are the binding criterion.")

    print("RESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
