# Fix Plan

One item per line, ordered by priority — the top unchecked item is what the
next loop iteration does. Verify every change by rendering pages and LOOKING.

## To do

- [ ] **#1 Collapse whitespace — kill mostly-blank pages (TOP PRIORITY).**
      Confirmed by rendering: sparse source pages (title page, a lone trailing
      line + page number) produce near-empty output pages, because `pack_slices`
      cuts on big vertical gaps and `emit_region` renders the gap as whitespace.
      Fix: replace pack_slices+emit_region for split modes with an atom-STACKING
      emitter that lays atoms top-to-bottom on the output page with *collapsed*
      spacing (preserve small inter-line gaps, cap large gaps at ~0.8x atom
      height), starting a new page when full. Result: dense, pretty pages, no
      cut lines, no blank waste. Preserve each atom's horizontal offset within
      its region (so centered titles stay centered, columns stay left-aligned).
- [ ] **#2 Merge clustered atoms into figures BEFORE stacking.** `region_atoms`
      returns a figure's many sub-drawings/images as separate atoms; stacking
      them individually would scramble a figure. Cluster atoms by proximity
      (overlapping/near bboxes) into one composite atom rendered whole. Must land
      together with #1 or figures break.
- [ ] **#3 Re-verify reading order** on a 2-col page with a mid-page figure:
      left-col, right-col, then the spanning figure at its y-position.

## Done

- [x] **Occluded sentences / cut lines** — replaced geometric `slice_fit_width`
      with `region_atoms()` + `pack_slices()`: groups indivisible atoms (text
      *lines*, images, drawings) into screen-height slices, cutting only in the
      whitespace between atoms, no overlap. A text line can no longer be
      bisected. Verified on MIT consecutive pages. (commit iter1)
- [x] **Tiny font on 2-col pages** — `two_col_regions()` band-segmentation:
      full-width spans (title/abstract/wide figures) become their own full-width
      region; two-column bands split left-then-right at `estimate_gutter()`.
      Fixes pages that previously collapsed to one tiny full-width strip whenever
      any element crossed the centre (the MonoBite problem). Body text now fills
      a column. Verified on MonoBite renders. (commit iter2)
- [x] **Prettiness / consistency** — `emit_region` top-aligns content within a
      6pt uniform margin (was vertical-centered) so pages line up. Verified on
      MonoBite + LeCun renders. (commit iter3)
- [x] **Re-converted all three** to papers/ereader/, all device-sized
      257x347pt, text preserved (MonoBite 86pp/3.9MB/27003 chars, LeCun
      173pp/4.2MB, MIT 449pp/21.6MB).
