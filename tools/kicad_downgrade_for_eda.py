#!/usr/bin/env python
"""Produce an EDA-import test variant of a KiCad board: older format header +
sanitized net names. Never overwrites the source; the committed baseline stays
byte-identical.

Why: EasyEDA 4.1.60's native KiCad import of PSDR_2.6.1_revB.kicad_pcb flattened
all 391 footprints to standalone pads/polylines/text. The file declares KiCad 10
(version 20260206); this tool emits a KiCad 8 header (20240108), drops the v9
`embedded_fonts` token, and replaces the two PADS net names that contain a
literal backslash (`\\EARPHONE_INSERTED`, `AUDIO_AMP_\\SHDN`) -- a backslash is
an escape character inside KiCad s-expressions, so those names are not valid.

Usage:
  python tools/kicad_downgrade_for_eda.py \
      --input dist/kicad/PSDR_2.6.1_revB.kicad_pcb \
      --output dist/kicad/PSDR_2.6.1_revB_edaimport8.kicad_pcb
"""
import argparse
import hashlib
import re

RENAMES = {
    '\\EARPHONE_INSERTED': 'EARPHONE_INSERTED',
    'AUDIO_AMP_\\SHDN': 'AUDIO_AMP_SHDN',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--version', default='20240108')
    ap.add_argument('--generator-version', default='8.0')
    a = ap.parse_args()

    src = open(a.input, encoding='utf-8').read()
    out = src

    out = re.sub(r'\(version \d+\)', '(version %s)' % a.version, out, count=1)
    out = re.sub(r'\(generator_version "[^"]*"\)', '(generator_version "%s")' % a.generator_version, out, count=1)
    out = re.sub(r'^\t\(embedded_fonts[^\n]*\)\n', '', out, count=1, flags=re.M)
    for old, new in RENAMES.items():
        out = out.replace(old, new)

    open(a.output, 'w', encoding='utf-8', newline='\n').write(out)

    nets_src = len(re.findall(r'^\t\(net \d+ "', src, re.M))
    nets_out = len(re.findall(r'^\t\(net \d+ "', out, re.M))
    print('nets declared: %d -> %d' % (nets_src, nets_out))
    print('backslashes left:', out.count('\\'))
    print('embedded_fonts left:', out.count('embedded_fonts'))
    print('paren balance delta:', out.count('(') - src.count('('), out.count(')') - src.count(')'))
    for p in (a.input, a.output):
        data = open(p, 'rb').read()
        print('%s  %d B  sha256 %s' % (p, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == '__main__':
    main()
