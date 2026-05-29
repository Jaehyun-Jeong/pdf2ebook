# Fix Plan

One item per line, ordered by priority — the top unchecked item is what the
next loop iteration does. Verify every change by rendering pages and LOOKING.

## To do

- [ ] **Confirm figures/tables render whole** on a figure-heavy page of each
      paper (render + look). pack_slices keeps an atom intact, but a figure made
      of many small vector drawings could still be split between atoms — check
      and, if needed, merge clustered drawing atoms into one figure atom.
- [ ] **Tune title/header band size.** Full-width title bands are inherently
      small (full A4 width scaled to 257pt). Acceptable for title/authors, but
      check no full-width *body* paragraph (non-column) ends up too small; if so,
      fitw-slice those bands instead of single-shot fit.
- [ ] **Spot-check reading order** on a 2-col page with a mid-page figure: should
      be left-col, right-col, then the spanning figure in its y-position.

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
