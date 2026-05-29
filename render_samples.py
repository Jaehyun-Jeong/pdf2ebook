#!/usr/bin/env python3
"""Render representative pages of a PDF to PNGs for visual inspection.

The Ralph loop uses this to *see* whether a converted PDF is actually
readable (font big enough? lines cut? figures sliced?). Renders the first
few pages plus a couple from the middle.

Usage:
  python render_samples.py <pdf> [out_dir] [dpi]
"""
import sys
import os
import fitz

pdf = sys.argv[1]
out_dir = sys.argv[2] if len(sys.argv) > 2 else "diag"
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150

os.makedirs(out_dir, exist_ok=True)
d = fitz.open(pdf)
n = d.page_count
# first 3, middle, and the page after a likely figure region
idxs = sorted(set([0, 1, 2, n // 2, n // 2 + 1, n - 1]) & set(range(n)))
stem = os.path.splitext(os.path.basename(pdf))[0]
for i in idxs:
    pix = d[i].get_pixmap(dpi=dpi)
    path = os.path.join(out_dir, f"{stem}__p{i:03d}.png")
    pix.save(path)
    print(path)
d.close()
