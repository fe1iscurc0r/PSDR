"""Normalise the PSDR Gerber/Excellon sets into per-board, fab-ready packages.

Why this exists: every Gerber file in Hardware/ uses legacy PADS extensions
(.GTL/.GBL/.G1/.G2/.GTS/.GBS/.GTO/.GBO/.GKO/.pho) or numbered prefixes, and the
four+ board sets each use a different convention.  JLCPCB / JLC PCB / EasyEDA
expect KiCad-style layer names with a .gbr extension.

The tool renames, never rewrites: copied bytes are identical to the source.
Each board gets a MANIFEST recording which layer went where, which layers are
missing, and the geometry measured from the file (so a wrong rename is visible).
"""

import io
import os
import re
import shutil
import sys
import zipfile
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerbparse            # noqa: E402

# source token -> (kiCad-style name, role)
COPPER = {
    "gtl": ("F_Cu", "top copper"),
    "gbl": ("B_Cu", "bottom copper"),
    "g1": ("In1_Cu", "inner layer 2 (L2 power)"),
    "g2": ("In2_Cu", "inner layer 3 (L3)"),
}
MASK = {"gts": ("F_Mask", "top solder mask"), "gbs": ("B_Mask", "bottom solder mask")}
SILK = {"gto": ("F_SilkS", "top silkscreen"), "gbo": ("B_SilkS", "bottom silkscreen")}
OUTLINE = {"gko": ("Edge_Cuts", "board outline"),
           "gml": ("Mechanical", "mechanical/outline (GML)")}
FABNOTE = {"fabnotes": ("Fab_Notes", "fabrication notes (not for fab)")}

# .pho files are PADS names carrying RS-274X text (verified, not assumed)
PHO_MAP = {
    "top-art": COPPER["gtl"], "bot-art": COPPER["gbl"],
    "top-sm": MASK["gts"], "bot-sm": MASK["gbs"],
    "top-ss": SILK["gto"], "bot-ss": SILK["gbo"],
    "fabnotes": FABNOTE["fabnotes"],
}


def classify(fname):
    """Return (kiCadName, role, note) for one source file, or None to skip."""
    base = os.path.basename(fname)
    stem = re.sub(r"^[\s0-9-]+", "", os.path.splitext(base)[0]).strip().lower()
    ext = os.path.splitext(base)[1].lstrip(".").lower()

    if ext in ("drl", "txt"):
        # Every .txt in these directories is an Excellon drill file (PADS names the
        # drill image after the board, e.g. PSDR2.TXT), verified by the M48 header.
        return (None, "DRILL", None)

    def hit(entry):
        return entry[0], entry[1], None

    # PADS-encoded names win over extensions: a .pho/.gbr whose stem ends with a
    # known layer word says what it is, whereas bare .gbr (the Keychain set has
    # one) carries no G04 layer name at all and must not be guessed.
    for tok, val in PHO_MAP.items():
        if stem.endswith(tok):
            return hit(val)

    if ext in ("gtl", "gbl", "g1", "g2"):
        return hit(COPPER[ext])
    if ext in ("gts", "gbs"):
        return hit(MASK[ext])
    if ext in ("gto", "gbo"):
        return hit(SILK[ext])
    if ext == "gko":
        return hit(OUTLINE["gko"])
    if ext == "gml":
        return hit(OUTLINE["gml"])
    if ext == "asc":
        return (None, "SKIP", "PADS bitmap-font artefact, not a PCB layer")
    return (None, "UNIDENTIFIED",
            "no layer name and no recognised PADS extension .%s" % ext)


def drill_kind(path):
    """Summarise an Excellon drill file.

    PADS emits one un-sectioned file: '% M48 INCH,LZ' with no closing '%' and no
    PTH/NPTH markers, so plating cannot be recovered from the drill image alone
    (the PADS .emn DRILLED_HOLES section does carry it).  Recorded, not invented.
    """
    txt = io.open(path, "r", encoding="latin-1").read()
    tools = re.findall(r"^T(\d+)C([-+.\d]+)(?:F([-+.\d]+))?(?:S([-+.\d]+))?", txt, re.M)
    return dict(pth=bool(re.search(r"\bPTH\b", txt)),
                npth=bool(re.search(r"\bNPTH\b", txt)),
                holes=len(re.findall(r"^X[-+]?\d+Y[-+]?\d+", txt, re.M)),
                tools=[(t, d) for t, d, _f, _s in tools],
                header=txt.split("\n", 1)[0].strip(),
                terminates=bool(re.search(r"^M30\b", txt, re.M)),
                m48_closed=any(ln.strip() == "%" for ln in txt.split("\n")))


def measure(path):
    try:
        g = gerbparse.load(path)
    except Exception as exc:                        # noqa: BLE001
        return {"error": str(exc)}
    b = g.bbox_in()
    out = g.stats()
    if b:
        out["mm"] = (round((b[2] - b[0]) * 25.4, 2), round((b[3] - b[1]) * 25.4, 2))
        out["origin_mm"] = (round(b[0] * 25.4, 2), round(b[1] * 25.4, 2))
    return out


def _sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


KNIFE_MIL = 0.002          # inches: a contour drawn with apertures this small is a route


def _knife_only(path):
    g = gerbparse.load(path)
    if not g.apertures or not g.strokes:
        return False
    for ap in g.apertures.values():
        if not ap.params or max(abs(v) for v in ap.params) > KNIFE_MIL:
            return False
    return True


def _rect(m):
    x0, y0 = m["origin_mm"]
    return (x0, y0, x0 + m["mm"][0], y0 + m["mm"][1])


def _brackets(cand, cu_list, tol=0.2):
    cx0, cy0, cx1, cy1 = _rect(cand)
    ux0 = min(_rect(m)[0] for m in cu_list)
    uy0 = min(_rect(m)[1] for m in cu_list)
    ux1 = max(_rect(m)[2] for m in cu_list)
    uy1 = max(_rect(m)[3] for m in cu_list)
    return cx0 <= ux0 + tol and cy0 <= uy0 + tol and cx1 >= ux1 - tol and cy1 >= uy1 - tol


def _geom_str(m):
    if "error" in m:
        return "PARSE ERROR: %s" % m["error"]
    return ("strokes=%s flash=%s ap=%s size=%smm origin=%smm FS=%s warn=%s"
            % (m.get("strokes"), m.get("flashes"), m.get("apertures"),
               "x".join(str(v) for v in m["mm"]) if "mm" in m else "?",
               ",".join(str(v) for v in m["origin_mm"]) if "origin_mm" in m else "?",
               m.get("fs", "?"), m.get("warn")))


def run(src_root, out_root, label=None):
    boards = OrderedDict()
    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames.sort()
        files = [f for f in sorted(filenames)
                 if not f.lower().endswith((".png", ".zip", ".xls", ".xlsx", ".pdf", ".bmp", ".exe"))]
        if not files:
            continue
        rel = os.path.relpath(dirpath, src_root).replace("\\", "/")
        if rel == ".":
            # files sitting directly in the scanned directory still form a board set
            rel = label or os.path.basename(src_root.rstrip(os.sep))
        boards[rel] = (dirpath, files)

    report = []
    for rel, (dirpath, files) in boards.items():
        name = rel.replace("/", "_").replace(" ", "_").strip("_")
        outdir = os.path.join(out_root, name)
        if os.path.isdir(outdir):
            shutil.rmtree(outdir)
        os.makedirs(outdir)

        rows = []
        used = {}
        geom = {}
        for f in files:
            src = os.path.join(dirpath, f)
            kcn, role, note = classify(f)
            if role == "DRILL":
                info = drill_kind(src)
                tag = "_PTH_NPTH" if (info["pth"] and info["npth"]) else \
                      ("_PTH" if info["pth"] else ("_NPTH" if info["npth"] else ""))
                tgt = "%s-Drill%s.drl" % (name, tag)
                shutil.copyfile(src, os.path.join(outdir, tgt))
                sizes = ",".join("%s=%s\"" % (t, d) for t, d in info["tools"])
                rows.append((tgt, f, "drill/excellon",
                             "%d holes, %d tools [%s], header=%r, M30=%s, "
                             "PTH/NPTH marked=%s" % (info["holes"], len(info["tools"]),
                                                     sizes, info["header"],
                                                     info["terminates"],
                                                     "no" if not (info["pth"] or info["npth"])
                                                     else "yes")))
                used[tgt] = src
                continue
            if kcn is None and role == "SKIP":
                rows.append(("-- SKIP --", f, role, note or ""))
                continue
            if kcn is None:
                # keep it rather than drop it: an unrecognised layer in a fab
                # package is worse than a clearly-labelled unknown one
                tgt = "Unidentified__%s" % f
                shutil.copyfile(src, os.path.join(outdir, tgt))
                m = measure(src)
                rows.append((tgt, f, role, "%s -- %s" % (note or "", _geom_str(m))))
                used[tgt] = src
                geom[tgt] = m
                continue
            tgt = "%s.gbr" % kcn
            if tgt in used:
                tgt = "%s_2.gbr" % kcn
            shutil.copyfile(src, os.path.join(outdir, tgt))
            m = measure(src)
            rows.append((tgt, f, role, _geom_str(m)))
            used[tgt] = src
            geom[tgt] = m

        findings = []
        # A board set with no .GKO but a .GML whose contour encloses every copper
        # layer is an outline exported under the wrong name (PSDR25 Encoder does
        # exactly this: GML = 20.00 x 25.50 mm, copper 18.99 x 24.49 mm inside it).
        if "Edge_Cuts.gbr" not in used and "Mechanical.gbr" in used:
            os.replace(os.path.join(outdir, "Mechanical.gbr"),
                       os.path.join(outdir, "Edge_Cuts.gbr"))
            used["Edge_Cuts.gbr"] = used.pop("Mechanical.gbr")
            geom["Edge_Cuts.gbr"] = geom.pop("Mechanical.gbr", {})
            rows = [("Edge_Cuts.gbr" if r[0] == "Mechanical.gbr" else r[0],
                     r[1], "board outline (recovered from .GML)"
                     if r[0] == "Mechanical.gbr" else r[2], r[3]) for r in rows]
            findings.append("no .GKO in this set: .GML contour promoted to Edge_Cuts.gbr")

        # Outline recovery: a layer drawn only with knife-line apertures (<=2 mil)
        # whose extent brackets the copper is a board outline whatever its filename
        # claims.  PSDR25 Main Board's "9 - fabnotes.GBR" is exactly that: knife-only,
        # 100.03 x 65.02 mm, while its copper spans 99.69 x 64.70 mm inside it.
        if "Edge_Cuts.gbr" not in used and geom:
            cu = [m for t, m in geom.items()
                  if t.split(".")[0] in ("F_Cu", "B_Cu", "In1_Cu", "In2_Cu") and "mm" in m]
            cand = []
            for tgt, m in sorted(geom.items()):
                if "mm" not in m or tgt.endswith(".drl"):
                    continue
                src_path = used.get(tgt)
                if not src_path or not _knife_only(src_path):
                    continue
                if cu and not _brackets(m, cu):
                    continue
                cand.append((tgt, m))
            if len(cand) == 1:
                tgt, m = cand[0]
                new = "Edge_Cuts.gbr"
                shutil.copyfile(used[tgt], os.path.join(outdir, new))
                used[new] = used[tgt]
                geom[new] = m
                rows.append((new, os.path.basename(used[tgt]), "board outline (recovered)",
                             "knife-line-only layer whose extent brackets the copper; "
                             "source was named %s" % os.path.basename(used[tgt])))
                findings.append("Edge_Cuts.gbr recovered from %s (knife-only, %s mm)"
                                % (tgt, "x".join(str(v) for v in m["mm"])))
            elif len(cand) > 1:
                findings.append("outline candidates %s -- ambiguous, not promoted"
                                % ", ".join(t for t, _m in cand))

        edge = geom.get("Edge_Cuts.gbr")
        FUNCTIONAL = ("F_Cu", "B_Cu", "In1_Cu", "In2_Cu", "F_Mask", "B_Mask",
                      "F_SilkS", "B_SilkS")
        if edge and "mm" in edge:
            ex0, ey0 = edge["origin_mm"]
            ex1, ey1 = ex0 + edge["mm"][0], ey0 + edge["mm"][1]
            for tgt, m in sorted(geom.items()):
                stem = tgt.split(".")[0]
                if stem not in FUNCTIONAL or "mm" not in m:
                    continue
                x0, y0 = m["origin_mm"]
                x1, y1 = x0 + m["mm"][0], y0 + m["mm"][1]
                out = []
                if x0 < ex0 - 0.1:
                    out.append(("left", ex0 - x0))
                if x1 > ex1 + 0.1:
                    out.append(("right", x1 - ex1))
                if y0 < ey0 - 0.1:
                    out.append(("bottom", ey0 - y0))
                if y1 > ey1 + 0.1:
                    out.append(("top", y1 - ey1))
                if out:
                    findings.append("%s reaches %.2fmm outside the outline (%s)"
                                    % (tgt, max(d for _s, d in out),
                                       ", ".join("%s %.2fmm" % (s, d) for s, d in out)))
        elif not edge:
            findings.append("NO board outline layer -> fab cannot cut the board")

        fs_variants = sorted({m.get("fs") for m in geom.values() if m.get("fs")})
        if len(fs_variants) > 1:
            findings.append("layers mix coordinate formats %s -- a 3.4 file read as "
                            "3.5 shifts every feature 10x" % "/".join(fs_variants))

        present = set(used)
        want = ["F_Cu.gbr", "B_Cu.gbr", "F_Mask.gbr", "B_Mask.gbr",
                "F_SilkS.gbr", "B_SilkS.gbr", "Edge_Cuts.gbr"]
        missing = [w for w in want if w not in present]

        man = io.open(os.path.join(outdir, "MANIFEST.txt"), "w",
                      encoding="utf-8", newline="\n")
        man.write("PSDR gerber package -- board: %s\n" % rel)
        man.write("source dir: %s\n" % dirpath.replace("\\", "/"))
        man.write("bytes are copied verbatim; only names are normalised.\n\n")
        for tgt, f, role, detail in rows:
            man.write("%-30s <- %-30s %-30s %s\n" % (tgt, f, role, detail))
        bad = []
        for tgt, s in sorted(used.items()):
            d = os.path.join(outdir, tgt)
            if _sha(s) != _sha(d):
                bad.append(tgt)
        man.write("\nbyte-identity: %d/%d copied files sha256-match their source%s\n"
                  % (len(used) - len(bad), len(used),
                     "; MISMATCH " + ",".join(bad) if bad else ""))
        if findings:
            man.write("\nFINDINGS\n")
            for fi in findings:
                man.write("  - %s\n" % fi)
        if missing:
            man.write("\nMISSING for JLC fab order: %s\n" % ", ".join(missing))
        else:
            man.write("\nAll standard layers present.\n")
        man.write("\n")
        man.close()

        zp = os.path.join(out_root, name + ".zip")
        if os.path.isfile(zp):
            os.remove(zp)
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(outdir)):
                z.write(os.path.join(outdir, f), os.path.join(name, f))

        report.append((name, len(used), missing, findings))
    return report


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Hardware")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist", "gerber")
    os.makedirs(out, exist_ok=True)
    dirs = [(os.path.join(root, "Gerbers"), None)]
    for sub, label in ((os.path.join("Keychain", "Gerbers"), "Keychain"),
                       (os.path.join("Test Boards", "MultiTest2 Gerbers"), "MultiTest2")):
        p = os.path.join(root, sub)
        if os.path.isdir(p):
            dirs.append((p, label))
    seen = {}
    for d, label in dirs:
        for name, n, missing, findings in run(d, out, label):
            seen[name] = (n, missing, findings)
    print("boards normalised: %d" % len(seen))
    for name, (n, missing, findings) in seen.items():
        print("  %-34s layers=%-3d %s" % (name, n,
              "MISSING: " + ",".join(missing) if missing else "complete"))
        for fi in findings:
            print("        ! %s" % fi)
