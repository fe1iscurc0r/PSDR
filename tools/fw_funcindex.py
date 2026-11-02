"""Build a function index (file:line, name) for the project-owned firmware code."""
import os
import re
import sys

DEF = re.compile(r"^[A-Za-z_][\w\s\*\(\),\[\]]*?\b([A-Za-z_]\w*)\s*\([^;]*\)\s*\{?\s*$")


def index(root):
    rows = []
    for f in sorted(os.listdir(root)):
        if not f.lower().endswith(".c"):
            continue
        path = os.path.join(root, f)
        for i, line in enumerate(open(path, encoding="latin-1"), 1):
            if not line or line[0] in " \t#/*}":
                continue
            m = DEF.match(line.rstrip())
            if not m:
                continue
            name = m.group(1)
            if name in ("if", "for", "while", "switch", "return", "sizeof"):
                continue
            rows.append((f, i, name))
    return rows


for root in sys.argv[1:]:
    rows = index(root)
    per = {}
    for f, i, n in rows:
        per.setdefault(f, []).append((i, n))
    print("== %s: %d function definitions" % (root, len(rows)))
    for f in sorted(per, key=lambda k: -len(per[k])):
        names = ", ".join("%s@%d" % (n, i) for i, n in per[f][:10])
        more = "" if len(per[f]) <= 10 else " ... +%d" % (len(per[f]) - 10)
        print("   %-22s %3d  %s%s" % (f, len(per[f]), names, more))
