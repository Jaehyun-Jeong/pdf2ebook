---
name: pdf2ebooks-status
description: "State of the pdf2ebooks project — the pdf2ereader tool, what's done, what's pending"
metadata: 
  node_type: memory
  type: project
  originSessionId: c10b2eea-c48d-4dc4-bc58-60d7d7a630b2
---

`pdf2ebooks` builds `pdf2ereader.py`: a PyMuPDF tool that makes textbook/paper
PDFs readable on small (6") e-readers while **preserving the original design**
(no reflow — see [[preserve-pdf-design]]). venv via `uv` at `.venv/`; inputs in
`papers/`, outputs in `papers/ereader/` (PDFs gitignored).

Modes: `crop` (margin trim), `fitw` (fit-to-width continuous flow), `2col`
(two-column split), `auto` (picks per doc), `reflow` (exists but user rejected —
breaks design), plus `--landscape auto/on/off` for wide single-column docs.

**Done:** occluded-text fix, empty-page elimination (continuous `_Flow`), 2-col
tiny-font fix, landscape auto for wide single-column.

**Pending (as of 2026-05-29):** MIT paper (equation-heavy diffusion textbook)
still has two unfixed issues — (1) tall display equations split across page
boundaries (e.g. eq 68 "TimeEmb"), (2) body font only ~6.5pt (too small).
Planned fixes: cluster overlapping text-glyph atoms in `region_blocks` so
equations stay whole; scale text by the text-COLUMN width (not figure-inflated
crop width) to enlarge font without reflow. LeCun ~8.1pt, MonoBite 9.7pt (the
reference size — keep unchanged). These fixes were attempted repeatedly but kept
getting lost to session tool-output instability; verify state with `git` and
real conversions, not just tool output.
