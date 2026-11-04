#!/usr/bin/env python3
"""rev-B zone closure: which parts a local respin actually touches.

Seeds are the three change zones named in docs/WO-psdr-takeover.md (K-6):
U304 (RF gain block), U16/U24/U30 (DPDT RF switches), U287 (HMC1023 LPF + supply).

Propagation is by net, hop by hop.  Reference nets are NOT propagated: a GND or a
power rail would drag half the board into every zone and make "only touch the local
area" untestable.  A net is treated as a reference net when its name matches
GND/POWER-ish patterns, or when its fan-out exceeds --max-fanout (default 12).
Every skipped net is printed, so the exclusion is auditable rather than assumed.

Outputs (relative to the repo root):
    dist/revB/zone_<tag>.csv   one row per in-zone part
    dist/revB/zones_summary.md summary table + excluded nets + the outside-set count

Reproduce:  python tools/revB_zone_closure.py
"""
import argparse
import csv
import json
import os
import re
import sys

REF_NAME = re.compile(r"(^|[^A-Z])(GND|AGND|PGND|VSS|POWER|\+?\d+V\d?(_|$))", re.I)


def load_netlist(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_placement(path):
    rows = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            d = (r.get("Designator") or "").strip()
            if d:
                rows[d] = r
    return rows


def part_nets(netlist):
    out = {}
    for net, pins in netlist["nets"].items():
        for p in pins:
            out.setdefault(p["refdes"], set()).add(net)
    return out


def closure(netlist, seeds, max_fanout):
    pn = part_nets(netlist)
    fans = {net: len(pins) for net, pins in netlist["nets"].items()}
    inzone = {s: 0 for s in seeds}
    skipped = {}
    frontier = list(seeds)
    for hop in (1, 2):
        nxt = []
        for ref in frontier:
            for net in sorted(pn.get(ref, ())):
                if fans.get(net, 0) > max_fanout or REF_NAME.search(net or ""):
                    skipped[net] = fans.get(net, 0)
                    continue
                for p in netlist["nets"][net]:
                    o = p["refdes"]
                    if o not in inzone:
                        inzone[o] = hop
                        nxt.append(o)
        frontier = nxt
    return inzone, skipped, fans


ZONES = [
    ("U304_gain", ["U304"]),
    ("DPDT_switches", ["U16", "U24", "U30"]),
    ("HMC1023_lpf", ["U287"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--netlist", default="dist/netlist/PSDR_2.6.1_netlist.json")
    ap.add_argument("--placement", default="dist/fab/PSDR_2.6.1_placement.csv")
    ap.add_argument("--outdir", default="dist/revB")
    ap.add_argument("--max-fanout", type=int, default=12)
    a = ap.parse_args()

    nl = load_netlist(a.netlist)
    place = load_placement(a.placement)
    os.makedirs(a.outdir, exist_ok=True)

    total = len(nl["parts"])
    allin = set()
    lines = []
    summary = []
    for tag, seeds in ZONES:
        inzone, skipped, fans = closure(nl, seeds, a.max_fanout)
        rows = []
        xs = []
        ys = []
        for ref, hop in sorted(inzone.items(), key=lambda kv: (kv[1], kv[0])):
            pr = place.get(ref)
            if pr:
                try:
                    x = float(pr["MidX_mm"])
                    y = float(pr["MidY_mm"])
                except (TypeError, ValueError, KeyError):
                    x = y = None
                if x is not None:
                    xs.append(x)
                    ys.append(y)
            nets = sorted(pnets(nl, ref))
            rows.append({
                "designator": ref,
                "hop": hop,
                "part_type": nl["parts"].get(ref, ""),
                "footprint": (pr or {}).get("Footprint", ""),
                "side": (pr or {}).get("Side", ""),
                "mid_x_mm": (pr or {}).get("MidX_mm", ""),
                "mid_y_mm": (pr or {}).get("MidY_mm", ""),
                "in_netlist": "yes" if ref in nl["parts"] else "NO",
                "nets": " ".join(nets),
            })
            allin.add(ref)
        with open(os.path.join(a.outdir, f"zone_{tag}.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        box = ""
        if xs:
            box = "x %.1f..%.1f mm, y %.1f..%.1f mm" % (min(xs), max(xs), min(ys), max(ys))
        summary.append((tag, seeds, len(rows), sum(1 for r in rows if r["hop"] == 1),
                        sum(1 for r in rows if r["hop"] == 2), box, len(skipped)))
        lines.append((tag, sorted(skipped.items(), key=lambda kv: -kv[1])[:12]))

    out = []
    out.append("# rev-B 影响圈（自动生成，勿手改）\n")
    out.append("")
    out.append("重跑：`python tools/revB_zone_closure.py`；源：`%s` + `%s`。" % (a.netlist, a.placement))
    out.append("")
    out.append("传播规则：按网络一跳一跳扩；**参考网络不传播**（名字含 GND/电源/电压轨，"
               "或扇出 > %d）。被挡掉的网都列在下面，排除是可查的而不是假设。" % a.max_fanout)
    out.append("")
    out.append("| 区 | 种子 | 区内件数 | hop1 | hop2 | 包围盒（mm，贴装表原点） | 被挡参考网数 |")
    out.append("|---|---|---|---|---|---|---|")
    for tag, seeds, n, h1, h2, box, nskip in summary:
        out.append("| %s | %s | %d | %d | %d | %s | %d |" % (tag, "/".join(seeds), n, h1, h2, box or "-", nskip))
    out.append("")
    out.append("**三区并集 = %d 件；板上一共 %d 件 ⇒ 影响圈外必须逐件不变的有 %d 件**"
               "（对拍用 `dist/fab/PSDR_2.6.1_placement.csv`，这是\"只动局部\"的可判定验收）。"
               % (len(allin), total, total - len(allin)))
    out.append("")
    for tag, skipped in lines:
        out.append("## %s 区被挡掉的参考网（扇出前 12 个）" % tag)
        out.append("")
        out.append("、".join("`%s`(%d)" % (n, f) for n, f in skipped) or "（无）")
        out.append("")
    with open(os.path.join(a.outdir, "zones_summary.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))

    print("zones:", [(s[0], s[2]) for s in summary])
    print("union=%d total=%d outside=%d" % (len(allin), total, total - len(allin)))
    print("wrote:", os.path.join(a.outdir, "zones_summary.md"))


def pnets(nl, ref):
    for net, pins in nl["nets"].items():
        for p in pins:
            if p["refdes"] == ref:
                yield net


if __name__ == "__main__":
    main()
