"""Minimal RS-274X (Gerber) reader used by the PSDR takeover tooling.

Supports what PADS 9.1/9.5 and gerbv actually emit in this repository:
FS/MO/OF/AP/AD/AM/LP, G00-G04, G74/G75, D01-D03 (and Dnn aperture select),
G02/G03 arcs with I/J offsets, M02.

Coordinates come back in inches; every file here declares %MOIN%.
"""

import io
import re
from collections import namedtuple

Aperture = namedtuple("Aperture", "code name kind params")
Stroke = namedtuple("Stroke", "kind x y x2 y2 w h dia aperture macro")
Arc = namedtuple("Arc", "x0 y0 x1 y1 cx cy r ccw multi")

_TOKEN = re.compile(r"([XYDGMIJ])([-+]?\d+(?:\.\d+)?)")


def _num(raw, frac):
    """Gerber coordinates are absolute integer strings with an implied decimal."""
    neg = raw.startswith("-")
    raw = raw.lstrip("+-")
    if "." in raw:
        val = float(raw)
    else:
        val = float(raw) / (10 ** frac)
    return -val if neg else val


def _arc_points(x0, y0, x1, y1, cx, cy, r, ccw, multi=True, steps=24):
    """Linearise a Gerber G02/G03 arc so bounding boxes are honest.

    G75 (multi-quadrant) is what PADS emits for filleted outlines; G74 clamps the
    sweep to one quadrant, and getting that wrong traces the long way round.
    """
    import math
    a0 = math.atan2(y0 - cy, x0 - cx)
    a1 = math.atan2(y1 - cy, x1 - cx)
    if ccw:
        while a1 < a0:
            a1 += 2 * math.pi
    else:
        while a1 > a0:
            a1 -= 2 * math.pi
    if not multi and abs(a1 - a0) > math.pi / 2 + 1e-9:
        a1 = a0 + (math.pi / 2) * (1 if a1 > a0 else -1)
    span = a1 - a0
    n = max(2, int(abs(span) / (math.pi / 2) * steps) + 1)
    out = []
    for i in range(n + 1):
        a = a0 + span * i / n
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    out[0] = (x0, y0)
    out[-1] = (x1, y1)
    return out


class Gerber:
    def __init__(self, text):
        self.strokes = []
        self.arcs = []
        self.macros = {}
        self.apertures = {}
        self.polarity = "D"
        self.warnings = []
        self.frac = 5
        self.intdig = 3
        self.fs_raw = ""
        self.units = 1.0          # multiplier to inches
        self._mode = "G01"
        self._x = 0.0
        self._y = 0.0
        self._gap = False
        self._cur = None
        self._op = None
        self._multi = True
        self._parse(text)

    # ------------------------------------------------------------------ parse
    def _parse(self, text):
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Extended (per-block) commands sit between pairs of '%'.  Splitting on
        # '%' gives alternating plain / extended segments, which is exactly how
        # RS-274X is defined -- a manual find("%", pos+1) mispairs on '%MOIN*%'
        # because the terminator is not the first '%' after the opener.
        for idx, seg in enumerate(text.split("%")):
            if idx % 2 == 0:
                for block in seg.split("*"):
                    block = block.strip()
                    if block:
                        self._cmd(block)
            else:
                body = seg.strip().strip("*").strip()
                if body:
                    self._ext(body)

    def _ext(self, body):
        body = body.strip()
        if not body:
            return
        tag = body[:2]
        if tag == "FS":
            self.fs_raw = body
            m = re.search(r"X(\d)(\d)", body)
            if m:
                self.frac = int(m.group(2))
                self.intdig = int(m.group(1))
            elif re.search(r"X\d{6}", body):
                self.frac = 5
        elif tag == "MO":
            if "MM" in body:
                self.units = 1.0 / 25.4
            elif "IN" in body:
                self.units = 1.0
        elif tag == "LP":
            self.polarity = body[2:3] or "D"
        elif tag == "AD":
            # '%ADD10C,0.0565*%'  -> directive 'AD' + letter 'D' + code '10' + shape 'C'.
            # The 'D' is part of the aperture-define verb, not part of the code.
            m = re.match(r"D(\d+|[A-Za-z_]\w*)([A-Za-z]\w*)", body[2:])
            if not m:
                self.warnings.append("bad AD: %s" % body[:40])
                return
            # PADS writes %ADD042C% but selects it with D42 -- codes are numeric, so
            # leading zeros must not become part of the key.
            code = m.group(1)
            if code.isdigit():
                code = code.lstrip("0") or "0"
            kind = m.group(2)
            params = [float(p) for p in re.findall(r"[-+]?\d*\.?\d+", body[m.end() + 2:])]
            self.apertures[code] = Aperture(code, code, kind, params)
        elif tag == "AM":
            m = re.match(r"AM([A-Za-z_]\w*)", body)
            if m:
                self.macros[m.group(1)] = body[m.end():]

    def _cmd(self, block):
        if block.startswith("G04"):
            return          # comment block: content up to its '*' is not geometry
        px = py = di = dj = None
        op = None
        for letter, digits in _TOKEN.findall(block):
            if letter == "X":
                px = _num(digits, self.frac) * self.units
            elif letter == "Y":
                py = _num(digits, self.frac) * self.units
            elif letter == "I":
                di = _num(digits, self.frac) * self.units
            elif letter == "J":
                dj = _num(digits, self.frac) * self.units
            elif letter == "D":
                d = digits.lstrip("0") or "0"
                if d in ("1", "2", "3"):
                    op = int(d)
                else:
                    if d not in self.apertures:
                        self.warnings.append("D%s selects undefined aperture" % d)
                    self._cur = d
            elif letter == "G":
                g = int(digits)
                if g in (0, 1, 2, 3):
                    self._mode = "G%02d" % g
                elif g == 74:
                    self._multi = False
                elif g == 75:
                    self._multi = True
        if op is None and (px is not None or py is not None):
            # D01/D02/D03 are modal: PADS emits bare moves such as "G01X392014*".
            op = self._op
        if op is None:
            return
        self._op = op
        nx = self._x if px is None else px
        ny = self._y if py is None else py
        if op == 1:
            if self._mode == "G00":
                self._gap = True
            else:
                self._expose(nx, ny, di, dj)
        elif op == 2:
            self._gap = True          # pen up: next D01 starts a new contour
        elif op == 3:
            self._flash(nx, ny)
        self._x, self._y = nx, ny

    # ------------------------------------------------------------- geometry
    def _ap_size(self):
        """Return (w, h, dia, macro) for the currently selected aperture."""
        ap = self.apertures.get(getattr(self, "_cur", None))
        if ap is None:
            self.warnings.append("exposure with no aperture selected")
            return None, None, None, None
        p = ap.params
        if ap.kind == "C":
            d = p[0] if p else None
            return d, d, d, None
        if ap.kind == "R":
            w = p[0] if p else None
            h = p[1] if len(p) > 1 else w
            return w, h, max([v for v in (w, h) if v is not None], default=None), None
        if ap.kind == "O":
            w = p[0] if p else None
            h = p[1] if len(p) > 1 else w
            return w, h, max([v for v in (w, h) if v is not None], default=None), None
        if ap.kind == "P":            # regular polygon: circumdiameter, sides, rotation
            d = p[0] if p else None
            return d, d, d, None
        # macro apertures (ANN / TER / custom): approximate by their largest parameter
        nums = [abs(float(v)) for v in p]
        d = max(nums, default=None)
        return d, d, d, ap.name

    def _expose(self, x, y, di, dj):
        w, h, dia, macro = self._ap_size()
        if self._mode in ("G02", "G03"):
            if di is None or dj is None:
                self.warnings.append("arc without I/J offsets; recorded as chord")
            else:
                cx, cy = self._x + di, self._y + dj
                r = (di * di + dj * dj) ** 0.5
                self.arcs.append(Arc(self._x, self._y, x, y, cx, cy, r,
                                     self._mode == "G03", self._multi))
                pts = _arc_points(self._x, self._y, x, y, cx, cy,
                                  r, ccw=(self._mode == "G03"), multi=self._multi)
                for (a, b) in zip(pts, pts[1:]):
                    self.strokes.append(Stroke("draw", a[0], a[1], b[0], b[1],
                                               w, h, dia, self._cur or "", macro))
                self._gap = False
                return
        self.strokes.append(Stroke("draw", self._x, self._y, x, y,
                                   w, h, dia, self._cur or "", macro))
        self._gap = False

    def _flash(self, x, y):
        w, h, dia, macro = self._ap_size()
        self.strokes.append(Stroke("flash", x, y, x, y,
                                   w, h, dia, getattr(self, "_cur", ""), macro))
        self._gap = False

    # ------------------------------------------------------------------- util
    def flashes(self):
        return [s for s in self.strokes if s.kind == "flash"]

    def drawups(self):
        return [s for s in self.strokes if s.kind == "draw"]

    def bbox(self):
        if not self.strokes:
            return None
        lo_x = lo_y = float("inf")
        hi_x = hi_y = float("-inf")
        for s in self.strokes:
            half_x = (s.w or 0.0) / 2.0
            half_y = (s.h or 0.0) / 2.0
            for (px, py) in ((s.x, s.y), (s.x2, s.y2)):
                lo_x = min(lo_x, px - half_x)
                hi_x = max(hi_x, px + half_x)
                lo_y = min(lo_y, py - half_y)
                hi_y = max(hi_y, py + half_y)
        return (lo_x, lo_y, hi_x, hi_y)

    def bbox_in(self):
        b = self.bbox()
        if not b:
            return None
        return tuple(round(v, 4) for v in b)

    def stats(self):
        return dict(strokes=len(self.strokes),
                    flashes=len(self.flashes()),
                    drawups=len(self.drawups()),
                    arcs=len(self.arcs),
                    apertures=len(self.apertures),
                    macros=len(self.macros),
                    bbox_in=self.bbox_in(),
                    fs="%d.%d" % (self.intdig, self.frac),
                    warn=len(self.warnings))


def load(path):
    with io.open(path, "r", encoding="latin-1", newline=None) as fh:
        return Gerber(fh.read())
