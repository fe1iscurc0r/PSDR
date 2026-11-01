#!/usr/bin/env python3
"""Set keepIsland on selected POUR records of a JLCEDA Pro .epro2 project.

The EDA KiCad importer ignores the zone's ``island_removal_mode`` and writes
``keepIsland: false`` for every pour (verified by converting the same board
with mode 0 and mode 1: both outputs are false).  This script flips the flag in
the converted project before it is imported.

Measured on the live 2.6.1 project (EDA 4.1.60): ``keepIsland`` alone is NOT
enough -- with it set on both empty pours and every zone re-poured, EDA still
filled only 10 of 12.  What actually fills them is the pour *precedence*
(EDA's ``pourPriority`` wins with the SMALLER number, the opposite of KiCad,
and the importer assigns 1..12 in file order).  See ``docs/WO-psdr-takeover.md``
section C-15 supplement; mapping the PADS pour priorities through is tracked
separately.

Only the matched POUR payloads are touched; every other record is copied
through byte for byte.
"""
import argparse
import json
import sys
import zipfile


def patch_epru(text, nets, all_pours):
    out, changed = [], []
    for line in text.split("\n"):
        if not line.strip():
            out.append(line)
            continue
        parts = line.split("||")
        try:
            head = json.loads(parts[0])
        except ValueError:
            out.append(line)
            continue
        if head.get("type") != "POUR" or len(parts) < 2:
            out.append(line)
            continue
        payload = json.loads(parts[1].rstrip("|"))
        net = payload.get("netName")
        if not (all_pours or net in nets):
            out.append(line)
            continue
        if payload.get("keepIsland") is True:
            out.append(line)
            continue
        if '"keepIsland":false' not in line:
            raise SystemExit(f"cannot find keepIsland:false in POUR {net!r}")
        out.append(line.replace('"keepIsland":false', '"keepIsland":true', 1))
        changed.append((net, payload.get("layerId")))
    return "\n".join(out), changed


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--nets", default="+3V3_FLIP_FLOP,V_SUPPLY",
                    help="comma-separated net names (default: the two empty pours)")
    ap.add_argument("--all", action="store_true", help="patch every pour")
    args = ap.parse_args()
    nets = {n for n in args.nets.split(",") if n}

    with zipfile.ZipFile(args.src) as zin:
        epru = next(n for n in zin.namelist() if n.endswith(".epru"))
        text = zin.read(epru).decode("utf-8")
        new_text, changed = patch_epru(text, nets, args.all)
        if not changed:
            raise SystemExit("no POUR record matched")
        with zipfile.ZipFile(args.dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename == epru:
                    data = new_text.encode("utf-8")
                zout.writestr(info, data)

    # Read the patched project back and prove the flags landed.
    with zipfile.ZipFile(args.dst) as z:
        epru = next(n for n in z.namelist() if n.endswith(".epru"))
        rows = []
        for line in z.read(epru).decode("utf-8").split("\n"):
            if not line.strip():
                continue
            parts = line.split("||")
            head = json.loads(parts[0])
            if head.get("type") != "POUR" or len(parts) < 2:
                continue
            payload = json.loads(parts[1].rstrip("|"))
            rows.append((payload.get("netName"), payload.get("layerId"),
                         payload.get("keepIsland")))
    print(f"changed {len(changed)} pour(s): {changed}")
    for net, layer, flag in rows:
        mark = "patched" if (net, layer) in changed else ""
        print(f"  {net:16s} layer={layer} keepIsland={flag} {mark}")
    print("wrote", args.dst)


if __name__ == "__main__":
    sys.exit(main())
