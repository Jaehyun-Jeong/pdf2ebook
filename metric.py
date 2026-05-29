#!/usr/bin/env python3
"""Per-page printing metric for the Ralph loop.

For each output page: content-bbox coverage (% of page area inked) and median
on-device font size (pt). Flags blank pages (<15% coverage) and reports the
font distribution. Usage: python metric.py <pdf>
"""
import sys
import statistics
import fitz

d = fitz.open(sys.argv[1])
n = d.page_count
sizes = []
covs = []
blanks = []
for i in range(n):
    pg = d[i]
    A = pg.rect.width * pg.rect.height
    td = pg.get_text("dict")
    # content bbox = union of all text/image block bboxes
    inked = 0.0
    bb = None
    pg_sizes = []
    for b in td["blocks"]:
        r = fitz.Rect(b["bbox"])
        if r.is_empty or r.width <= 0 or r.height <= 0:
            continue
        bb = r if bb is None else (bb | r)
        for ln in b.get("lines", []):
            for sp in ln.get("spans", []):
                pg_sizes.append(sp["size"])
    cov = (bb.width * bb.height / A) if bb else 0.0
    covs.append(cov)
    if pg_sizes:
        sizes.extend(pg_sizes)
    if cov < 0.15:
        blanks.append((i, round(cov * 100, 2)))
print(f"pages: {n}")
print(f"median font: {statistics.median(sizes):.2f}pt  (p10={sorted(sizes)[len(sizes)//10]:.2f} "
      f"p90={sorted(sizes)[len(sizes)*9//10]:.2f})")
print(f"coverage: median={statistics.median(covs)*100:.1f}%  min={min(covs)*100:.2f}%  "
      f"max={max(covs)*100:.1f}%")
print(f"blank pages (<15% cov): {len(blanks)} -> {blanks[:20]}")
d.close()
