#!/usr/bin/env python
"""Build a net-rename table: deliverable .epcb2 (source of truth) vs a live EDA
project snapshot (.epru extracted from `easyeda project export-source`).

Matching is by copper geometry: every LINE keyed by its unordered endpoint pair
must appear in both files; each live line carries the net name the EDA client
actually kept. Votes per source net decide the mapping. Pad counts per net are
counted independently (deliverable PAD_NET vs live PAD.netName) so a merge --
several source nets collapsing onto one live net -- is visible even when the
geometry match is ambiguous.

Usage:
  python tools/eda_net_rename_table.py \
      --deliverable D:/psdr_eprj3/PSDR_revB_poured/pcb/PCB1.epcb2 \
      --live _eda_project.epru --out dist/eda/net_rename_table.csv
"""
import argparse, collections, csv, json, os, zipfile


def body(line):
    _, _, b = line.partition('||')
    try:
        return json.loads(b.rstrip('|\n'))
    except Exception:
        return {}


def key2(x1, y1, x2, y2):
    a = (round(x1), round(y1), round(x2), round(y2))
    b = (round(x2), round(y2), round(x1), round(y1))
    return a if a <= b else b


def load_deliverable(path):
    nets, stats, lines = set(), collections.defaultdict(collections.Counter), collections.defaultdict(list)
    for line in open(path, encoding='utf-8'):
        try:
            h = json.loads(line.partition('||')[0])
        except Exception:
            continue
        t, b = h.get('type'), body(line)
        if t == 'NET':
            hid = h['id']
            if isinstance(hid, str):
                hid = json.loads(hid)
            nets.add(hid[1])
        elif t == 'PAD_NET' and b.get('padNet'):
            stats[b['padNet']]['pads'] += 1
        elif t == 'LINE' and (b.get('netName') or b.get('net')):
            n = b.get('netName') or b.get('net')
            stats[n]['lines'] += 1
            lines[key2(b.get('startX', 0), b.get('startY', 0), b.get('endX', 0), b.get('endY', 0))].append(n)
        elif t == 'VIA' and (b.get('net') or b.get('netName')):
            stats[b.get('net') or b.get('netName')]['vias'] += 1
        elif t == 'POUR' and (b.get('net') or b.get('netName')):
            stats[b.get('net') or b.get('netName')]['pours'] += 1
    return nets, stats, lines


def load_live(path):
    lines, pads = {}, collections.Counter()
    for line in open(path, encoding='utf-8'):
        try:
            h = json.loads(line.partition('||')[0])
        except Exception:
            continue
        b = body(line)
        if h.get('type') == 'LINE':
            n = b.get('net') or b.get('netName') or ''
            if n:
                lines[key2(b.get('startX', 0), b.get('startY', 0), b.get('endX', 0), b.get('endY', 0))] = n
        elif h.get('type') == 'PAD':
            if b.get('netName'):
                pads[b['netName']] += 1
    return lines, pads


def extract_epru(epro2_path, dest):
    with zipfile.ZipFile(epro2_path) as z:
        name = [n for n in z.namelist() if n.endswith('.epru')][0]
        open(dest, 'wb').write(z.read(name))
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--deliverable', required=True)
    ap.add_argument('--live', required=True, help='.epru (record stream) or .epro2 to extract it from')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    live_path = a.live
    if live_path.endswith('.epro2'):
        live_path = extract_epru(live_path, os.path.splitext(live_path)[0] + '.epru')

    dnets, stats, dlines = load_deliverable(a.deliverable)
    llines, lpads = load_live(live_path)

    votes = collections.defaultdict(collections.Counter)
    matched = 0
    for k, nets in dlines.items():
        ln = llines.get(k)
        if ln is None:
            continue
        matched += 1
        for n in nets:
            votes[n][ln] += 1

    mapping = {d: c.most_common(1)[0][0] for d, c in votes.items() if c}
    rows = []
    for d in sorted(mapping):
        ln = mapping[d]
        if d == ln:
            continue
        s = stats.get(d, {})
        rows.append([d, ln, s.get('lines', 0), s.get('pads', 0), s.get('vias', 0), s.get('pours', 0)])

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['source_net', 'eda_net_now', 'lines', 'pads', 'vias', 'pours'])
        w.writerows(rows)

    rev = collections.defaultdict(list)
    for d, ln in mapping.items():
        if d != ln:
            rev[ln].append(d)
    merges = {ln: sorted(ds) for ln, ds in rev.items() if len(ds) > 1}
    total = collections.Counter()
    for r in rows:
        for i, k in zip(range(2, 6), ('lines', 'pads', 'vias', 'pours')):
            total[k] += r[i]

    print('deliverable lines: %d, live lines: %d, matched: %d' % (len(dlines), len(llines), matched))
    print('deliverable nets: %d, geometry-covered: %d' % (len(dnets), len(mapping)))
    print('nets whose name changed: %d' % len(rows))
    print('merges (one live net <- several source nets): %s' % (merges or 'none'))
    print('primitives on changed nets: %s (sum %d)' % (dict(total), sum(total.values())))
    print('wrote %s' % a.out)


if __name__ == '__main__':
    main()
