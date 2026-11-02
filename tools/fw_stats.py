"""Per-directory line counts of .c/.h/.s in a firmware tree, excluding build output.

Usage: python tools/fw_stats.py Source Source_F7"""
import collections
import os
import sys

SKIP = {"build_linux", "build_linux_f7", "build_linux_f7_os", "Debug", "obj"}


def scan(root):
    per = collections.Counter()
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        rel = os.path.relpath(dp, root)
        top = rel.split(os.sep)[0] if rel != "." else "."
        for f in fn:
            if os.path.splitext(f)[1].lower() not in (".c", ".h", ".s"):
                continue
            try:
                n = sum(1 for _ in open(os.path.join(dp, f), encoding="latin-1"))
            except Exception:
                n = 0
            per[top] += n
    return per


for root in sys.argv[1:] or ("Source", "Source_F7"):
    per = scan(root)
    print("== %s: %d lines of .c/.h/.s (build dirs excluded)" % (root, sum(per.values())))
    for k, v in per.most_common(14):
        print("   %-30s %7d" % (k, v))
